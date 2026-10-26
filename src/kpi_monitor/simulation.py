"""Deterministic synthetic fixtures; not measurements from a factory."""

from datetime import UTC, datetime, timedelta

from .domain import Interval, ProductionEvent, Shift

SCENARIOS = {
    "reference": "Turno con parada",
    "healthy": "Operación estable",
    "sensor_loss": "Pérdida de telemetría",
    "zero_quality": "Rechazo total",
    "no_data": "Sin datos",
}
BASE_TIME = datetime(2026, 1, 15, 8, tzinfo=UTC)


def scenario(name: str) -> tuple[Shift, list[ProductionEvent]]:
    if name not in SCENARIOS:
        raise ValueError(f"unknown scenario: {name}")
    # Distinct machines avoid overlapping scenarios and support idempotent seeding.
    machine = f"DEMO-{name}"
    shift = Shift(
        shift_id=name,
        machine_id=machine,
        name=SCENARIOS[name],
        start=BASE_TIME,
        end=BASE_TIME + timedelta(hours=1),
        ideal_cycle_seconds=6,
        breaks=(
            Interval(
                start=BASE_TIME + timedelta(minutes=30), end=BASE_TIME + timedelta(minutes=40)
            ),
        ),
        source="synthetic",
    )
    events = []
    running_index = 0
    for minute in range(60):
        if 30 <= minute < 40 or name == "no_data":
            continue
        stopped = name in {"reference", "sensor_loss"} and 20 <= minute < 30
        if stopped:
            count = good = 0
        elif name in {"reference", "sensor_loss"}:
            count = 9
            good = 8 if running_index < 18 else 9
            running_index += 1
        else:
            count = 10
            good = 0 if name == "zero_quality" else (9 if running_index < 10 else 10)
            running_index += 1
        if name == "sensor_loss" and 45 <= minute < 55:
            continue
        events.append(
            ProductionEvent(
                event_id=f"{name}-{minute:03d}",
                machine_id=machine,
                start=BASE_TIME + timedelta(minutes=minute),
                end=BASE_TIME + timedelta(minutes=minute + 1),
                state="stopped" if stopped else "running",
                total_count=count,
                good_count=good,
            )
        )
    return shift, events
