"""Pure production-domain contracts and OEE calculation.

Intervals are half-open [start, end). Counts belong to the whole interval:
we never prorate discrete pieces across a shift or planned-break boundary.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Interval(Contract):
    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must include a UTC offset")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self

    @property
    def seconds(self) -> float:
        return (self.end - self.start).total_seconds()


class Shift(Interval):
    shift_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    machine_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    name: str = Field(min_length=1, max_length=120)
    ideal_cycle_seconds: float = Field(gt=0, le=86400)
    breaks: tuple[Interval, ...] = ()
    source: Literal["synthetic", "external"] = "synthetic"

    @model_validator(mode="after")
    def valid_breaks(self):
        previous = self.start
        for pause in sorted(self.breaks, key=lambda x: x.start):
            if pause.start < previous or pause.start < self.start or pause.end > self.end:
                raise ValueError("breaks must be disjoint and contained in the shift")
            previous = pause.end
        if sum(p.seconds for p in self.breaks) >= self.seconds:
            raise ValueError("shift must contain planned production time")
        return self

    @property
    def planned_intervals(self) -> list[Interval]:
        result = []
        cursor = self.start
        for pause in sorted(self.breaks, key=lambda x: x.start):
            if pause.start > cursor:
                result.append(Interval(start=cursor, end=pause.start))
            cursor = pause.end
        if cursor < self.end:
            result.append(Interval(start=cursor, end=self.end))
        return result


class ProductionEvent(Interval):
    event_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,120}$")
    machine_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    state: Literal["running", "stopped"]
    total_count: int = Field(ge=0, strict=True)
    good_count: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def valid_counts(self):
        if self.good_count > self.total_count:
            raise ValueError("good_count cannot exceed total_count")
        if self.state == "stopped" and self.total_count:
            raise ValueError("a stopped interval cannot produce pieces")
        if self.seconds > 86400:
            raise ValueError("telemetry intervals must not exceed 24 hours")
        return self


class OEEReport(Contract):
    shift_id: str
    planned_seconds: float
    observed_seconds: float
    running_seconds: float
    stopped_seconds: float
    missing_seconds: float
    coverage: float
    total_count: int
    good_count: int
    availability: float | None
    performance: float | None
    quality: float | None
    oee: float | None
    status: Literal["valid", "insufficient_data", "invalid_configuration", "no_production"]
    issues: tuple[str, ...]


def calculate_oee(shift: Shift, events: list[ProductionEvent]) -> OEEReport:
    """Return observed counts and only publish OEE when coverage is complete."""
    planned = shift.planned_intervals
    planned_seconds = sum(i.seconds for i in planned)
    selected = sorted(
        (
            e
            for e in events
            if e.machine_id == shift.machine_id and e.start < shift.end and e.end > shift.start
        ),
        key=lambda e: e.start,
    )
    observed = running = stopped = 0.0
    total = good = 0
    issues = []
    previous_end = None
    for event in selected:
        if previous_end is not None and event.start < previous_end:
            raise ValueError("overlapping telemetry intervals")
        previous_end = event.end
        intersections = [
            (max(event.start, window.start), min(event.end, window.end))
            for window in planned
            if event.start < window.end and event.end > window.start
        ]
        if not intersections:
            continue
        covered = sum((b - a).total_seconds() for a, b in intersections)
        if abs(covered - event.seconds) > 1e-6:
            issues.append("interval_crosses_planned_boundary")
            continue
        observed += covered
        if event.state == "running":
            running += covered
        else:
            stopped += covered
        total += event.total_count
        good += event.good_count

    missing = max(0.0, planned_seconds - observed)
    coverage = observed / planned_seconds
    availability = performance = quality = oee = None
    status = "insufficient_data"
    if missing > 1e-6 or issues:
        issues.append("incomplete_telemetry")
    else:
        availability = running / planned_seconds
        if total == 0:
            performance = 0.0 if running else None
            oee = 0.0
            status = "no_production"
            issues.append("no_pieces_produced")
        else:
            performance = shift.ideal_cycle_seconds * total / running
            quality = good / total
            if performance > 1.0 + 1e-9:
                status = "invalid_configuration"
                issues.append("performance_exceeds_100_percent")
            else:
                status = "valid"
                oee = availability * performance * quality
    return OEEReport(
        shift_id=shift.shift_id,
        planned_seconds=planned_seconds,
        observed_seconds=observed,
        running_seconds=running,
        stopped_seconds=stopped,
        missing_seconds=missing,
        coverage=coverage,
        total_count=total,
        good_count=good,
        availability=availability,
        performance=performance,
        quality=quality,
        oee=oee,
        status=status,
        issues=tuple(dict.fromkeys(issues)),
    )
