"""SQLite persistence: atomic batches, idempotent events and explicit conflicts."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .domain import OEEReport, ProductionEvent, Shift


class ConflictError(ValueError):
    """The submitted record conflicts with an existing identity or time interval."""


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS shifts (
                    shift_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY, machine_id TEXT NOT NULL,
                    start TEXT NOT NULL, end TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS events_machine_time
                    ON events(machine_id, start, end);
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY, shift_id TEXT NOT NULL,
                    code TEXT NOT NULL, severity TEXT NOT NULL, message TEXT NOT NULL,
                    acknowledged INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(shift_id, code));
                CREATE TABLE IF NOT EXISTS rejected_messages (
                    id INTEGER PRIMARY KEY, received_at TEXT NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    reason TEXT NOT NULL);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _canonical(record):
        return json.dumps(record.model_dump(mode="json"), sort_keys=True)

    def add_shift(self, shift: Shift) -> bool:
        payload = self._canonical(shift)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT payload FROM shifts WHERE shift_id=?", (shift.shift_id,)
            ).fetchone()
            if old:
                if old["payload"] != payload:
                    raise ConflictError("shift_id already exists with different configuration")
                return False
            db.execute("INSERT INTO shifts VALUES (?, ?)", (shift.shift_id, payload))
            return True

    def shifts(self, limit: int = 100) -> list[Shift]:
        with self.connection() as db:
            return [
                Shift.model_validate_json(row["payload"])
                for row in db.execute(
                    "SELECT payload FROM shifts ORDER BY rowid DESC LIMIT ?", (limit,)
                )
            ]

    def shift(self, shift_id: str) -> Shift:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM shifts WHERE shift_id=?", (shift_id,)).fetchone()
            if row is None:
                raise KeyError(shift_id)
            return Shift.model_validate_json(row["payload"])

    def ingest(self, events: list[ProductionEvent]) -> dict[str, int]:
        """All records commit together; an identical retransmission is harmless."""
        inserted = duplicates = 0
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            for event in events:
                payload = self._canonical(event)
                old = db.execute(
                    "SELECT payload FROM events WHERE event_id=?", (event.event_id,)
                ).fetchone()
                if old:
                    if old["payload"] != payload:
                        raise ConflictError("event_id reused with different content")
                    duplicates += 1
                    continue
                start = event.start.isoformat()
                end = event.end.isoformat()
                overlap = db.execute(
                    "SELECT event_id FROM events WHERE machine_id=? AND start<? AND end>?",
                    (event.machine_id, end, start),
                ).fetchone()
                if overlap:
                    raise ConflictError("telemetry overlaps an existing interval")
                db.execute(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                    (event.event_id, event.machine_id, start, end, payload),
                )
                inserted += 1
        return {"inserted": inserted, "duplicates": duplicates}

    def events(self, shift: Shift) -> list[ProductionEvent]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT payload FROM events WHERE machine_id=? AND start<? AND end>? "
                "ORDER BY start LIMIT 50001",
                (shift.machine_id, shift.end.isoformat(), shift.start.isoformat()),
            )
            result = [ProductionEvent.model_validate_json(row["payload"]) for row in rows]
            if len(result) > 50000:
                raise ValueError("report exceeds the 50000-interval local limit")
            return result

    def record_rejection(self, reason: str):
        with self.connection() as db:
            db.execute("INSERT INTO rejected_messages(reason) VALUES (?)", (reason[:1000],))

    def rejection_count(self) -> int:
        with self.connection() as db:
            return db.execute("SELECT COUNT(*) FROM rejected_messages").fetchone()[0]

    def sync_alerts(self, report: OEEReport):
        current = {}
        if report.status == "insufficient_data":
            current["telemetry_gap"] = ("warning", "Cobertura incompleta: OEE no disponible.")
        elif report.status == "invalid_configuration":
            current["invalid_cycle"] = (
                "critical",
                "Rendimiento superior al 100 %: revise ciclo y conteos.",
            )
        elif report.oee is not None and report.oee < 0.85:
            severity = "critical" if report.oee < 0.75 else "warning"
            current["low_oee"] = (
                severity,
                f"OEE de {report.oee:.1%}; umbral de demostración: 85 %.",
            )
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            for old in db.execute("SELECT code FROM alerts WHERE shift_id=?", (report.shift_id,)):
                if old["code"] not in current:
                    db.execute(
                        "UPDATE alerts SET active=0 WHERE shift_id=? AND code=?",
                        (report.shift_id, old["code"]),
                    )
            for code, (severity, message) in current.items():
                db.execute(
                    """
                    INSERT INTO alerts(shift_id, code, severity, message)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(shift_id, code) DO UPDATE SET
                        severity=excluded.severity, message=excluded.message,
                        acknowledged=CASE WHEN alerts.active=0 THEN 0 ELSE alerts.acknowledged END,
                        active=1
                """,
                    (report.shift_id, code, severity, message),
                )

    def alerts(self, shift_id: str | None = None) -> list[dict]:
        with self.connection() as db:
            if shift_id is None:
                rows = db.execute("SELECT * FROM alerts ORDER BY id DESC")
            else:
                rows = db.execute(
                    "SELECT * FROM alerts WHERE shift_id=? ORDER BY id DESC", (shift_id,)
                )
            return [dict(row) for row in rows]

    def acknowledge(self, alert_id: int) -> dict:
        with self.connection() as db:
            count = db.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,)).rowcount
            if not count:
                raise KeyError(alert_id)
            return dict(db.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone())
