"""Local HTTP interface. Demo mutation is opt-in; bind to loopback by default."""

import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from .domain import OEEReport, ProductionEvent, Shift, calculate_oee
from .reports import telemetry_metadata, time_series
from .simulation import SCENARIOS, scenario
from .storage import ConflictError, Store


def create_app(db_path: str | Path | None = None, *, demo_mode: bool = False) -> FastAPI:
    store = Store(db_path or os.getenv("KPI_DB_PATH", "var/monitor.db"))
    app = FastAPI(
        title="Industrial KPI Monitor",
        version="1.0.0",
        description="Local engineering demonstrator. Not a plant control system.",
    )
    app.state.store = store
    static = Path(__file__).parent / "static"
    if static.exists():
        app.mount("/static", StaticFiles(directory=static), name="static")

    @app.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                "base-uri 'self'; form-action 'self'"
            )
            if not request.url.path.startswith(("/docs", "/redoc"))
            else "frame-ancestors 'none'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(static / "index.html")

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "demo_mode": demo_mode,
            "rejected_messages": store.rejection_count(),
        }

    @app.get("/api/shifts", response_model=list[Shift])
    def shifts(limit: Annotated[int, Query(ge=1, le=500)] = 100):
        return store.shifts(limit)

    @app.post("/api/shifts", status_code=201)
    def add_shift(value: Shift):
        try:
            return {"inserted": store.add_shift(value)}
        except ConflictError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/api/events")
    def ingest(values: Annotated[list[ProductionEvent], Field(min_length=1, max_length=1000)]):
        try:
            return store.ingest(values)
        except ConflictError as exc:
            raise HTTPException(409, str(exc)) from exc

    def get_shift(shift_id):
        try:
            return store.shift(shift_id)
        except KeyError as exc:
            raise HTTPException(404, "Shift not found") from exc

    def get_events(value):
        try:
            return store.events(value)
        except ValueError as exc:
            raise HTTPException(413, str(exc)) from exc

    @app.get("/api/shifts/{shift_id}/report", response_model=OEEReport)
    def report(shift_id: str):
        value = get_shift(shift_id)
        result = calculate_oee(value, get_events(value))
        store.sync_alerts(result)
        return result

    @app.get("/api/shifts/{shift_id}/snapshot")
    def snapshot(shift_id: str, minutes: Annotated[int, Query(ge=1, le=60)] = 10):
        value = get_shift(shift_id)
        samples = get_events(value)
        result = calculate_oee(value, samples)
        store.sync_alerts(result)
        return {
            "shift": value,
            "report": result,
            "metadata": telemetry_metadata(value, samples),
            "series": time_series(value, samples, minutes),
            "events": samples[-120:],
            "event_count": len(samples),
            "alerts": store.alerts(shift_id),
        }

    @app.get("/api/shifts/{shift_id}/events", response_model=list[ProductionEvent])
    def events(shift_id: str, limit: Annotated[int, Query(ge=1, le=5000)] = 1000):
        return get_events(get_shift(shift_id))[-limit:]

    @app.get("/api/alerts")
    def alerts(shift_id: str | None = None):
        return store.alerts(shift_id)

    @app.post("/api/alerts/{alert_id}/acknowledge")
    def acknowledge(alert_id: int):
        try:
            return store.acknowledge(alert_id)
        except KeyError as exc:
            raise HTTPException(404, "Alert not found") from exc

    @app.get("/api/demo/scenarios")
    def scenarios():
        return {"enabled": demo_mode, "scenarios": SCENARIOS if demo_mode else {}}

    @app.post("/api/demo/{name}")
    def seed_demo(name: str):
        if not demo_mode:
            raise HTTPException(403, "Demo mode is disabled")
        try:
            value, samples = scenario(name)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        try:
            store.add_shift(value)
            result = store.ingest(samples)
        except ConflictError as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"shift_id": value.shift_id, **result}

    return app
