"""Reporting metadata and bounded, independent time buckets."""

from datetime import UTC, datetime, timedelta

from .domain import Interval, ProductionEvent, Shift, calculate_oee


def telemetry_metadata(shift: Shift, events: list[ProductionEvent], *, now=None) -> dict:
    now = now or datetime.now(UTC)
    last_end = max((e.end for e in events), default=None)
    age = (now - last_end).total_seconds() if last_end else None
    phase = "scheduled" if now < shift.start else "in_progress" if now < shift.end else "finished"
    return {
        "source": shift.source,
        "phase": phase,
        "last_event_end": last_end,
        "event_age_seconds": age,
        "clock_ahead": age is not None and age < -5,
        "stale": shift.source == "external"
        and phase == "in_progress"
        and (age is None or age > 120),
        "stale_after_seconds": 120,
        "evaluated_at": now,
        "scope": "full_shift",
    }


def time_series(shift: Shift, events: list[ProductionEvent], minutes: int = 10) -> list[dict]:
    """No prorating: a record crossing a bucket boundary makes that bucket unknown."""
    if not 1 <= minutes <= 60:
        raise ValueError("minutes must be between 1 and 60")
    result = []
    cursor = shift.start
    while cursor < shift.end:
        end = min(cursor + timedelta(minutes=minutes), shift.end)
        pauses = tuple(
            Interval(start=max(cursor, p.start), end=min(end, p.end))
            for p in shift.breaks
            if p.start < end and p.end > cursor
        )
        point = {
            "start": cursor,
            "end": end,
            "oee": None,
            "coverage": None,
            "status": "planned_break",
        }
        if sum(p.seconds for p in pauses) < (end - cursor).total_seconds():
            window = Shift(**{**shift.model_dump(), "start": cursor, "end": end, "breaks": pauses})
            report = calculate_oee(window, events)
            point.update(oee=report.oee, coverage=report.coverage, status=report.status)
        result.append(point)
        cursor = end
    return result
