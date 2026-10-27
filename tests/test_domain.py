from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from kpi_monitor.domain import Interval, ProductionEvent, Shift, calculate_oee

T = datetime(2026, 1, 1, tzinfo=UTC)


def shift(**kwargs):
    return Shift(
        shift_id="shift",
        machine_id="line",
        name="Test",
        start=T,
        end=T + timedelta(hours=1),
        ideal_cycle_seconds=6,
        **kwargs,
    )


def event(start, end, total=0, good=0, state="running", event_id="event"):
    return ProductionEvent(
        event_id=event_id,
        machine_id="line",
        start=T + timedelta(minutes=start),
        end=T + timedelta(minutes=end),
        state=state,
        total_count=total,
        good_count=good,
    )


def test_reference_shift_matches_hand_calculation():
    # 60 min - 10 min break = 50 planned; 40 running; 360 total; 342 good.
    schedule = shift(
        breaks=(Interval(start=T + timedelta(minutes=30), end=T + timedelta(minutes=40)),)
    )
    report = calculate_oee(
        schedule,
        [
            event(0, 20, 180, 171, event_id="first"),
            event(20, 30, state="stopped", event_id="stop"),
            event(40, 60, 180, 171, event_id="last"),
        ],
    )
    assert report.availability == pytest.approx(0.8)
    assert report.performance == pytest.approx(0.9)
    assert report.quality == pytest.approx(0.95)
    assert report.oee == pytest.approx(0.684)
    assert report.coverage == 1


def test_no_data_is_unknown_not_perfect():
    result = calculate_oee(shift(), [])
    assert result.coverage == 0
    assert result.missing_seconds == 3600
    assert result.oee is result.availability is result.performance is result.quality is None


def test_zero_quality_stays_zero():
    result = calculate_oee(shift(), [event(0, 60, 600, 0)])
    assert result.quality == result.oee == 0
    assert result.performance == 1


def test_ideal_speed_is_not_capped_at_ninety_percent():
    result = calculate_oee(shift(), [event(0, 60, 600, 600)])
    assert result.oee == result.performance == 1


def test_irregular_sampling_is_weighted_by_duration():
    result = calculate_oee(
        shift(),
        [
            event(0, 5, state="stopped", event_id="a"),
            event(5, 60, 550, 550, event_id="b"),
        ],
    )
    assert result.availability == pytest.approx(55 / 60)


def test_missing_interval_suppresses_oee():
    result = calculate_oee(shift(), [event(0, 30, 300, 300)])
    assert result.coverage == 0.5
    assert result.oee is None
    assert result.total_count == 300


def test_partial_piece_counts_are_not_fabricated():
    result = calculate_oee(shift(), [event(-10, 60, 700, 700)])
    assert result.oee is None
    assert "interval_crosses_planned_boundary" in result.issues


def test_overlap_rejected():
    with pytest.raises(ValueError, match="overlapping"):
        calculate_oee(shift(), [event(0, 40), event(30, 60, event_id="b")])


def test_above_ideal_speed_is_visible_invalid_configuration():
    result = calculate_oee(shift(), [event(0, 60, 1200, 1200)])
    assert result.performance == 2
    assert result.oee is None
    assert result.status == "invalid_configuration"


@pytest.mark.parametrize("state", ["running", "stopped"])
def test_known_no_production_has_zero_oee_and_undefined_quality(state):
    result = calculate_oee(shift(), [event(0, 60, state=state)])
    assert result.oee == 0
    assert result.quality is None
    assert result.status == "no_production"


@pytest.mark.parametrize(
    "total,good,state",
    [
        (-1, 0, "running"),
        (10, 11, "running"),
        (1, 1, "stopped"),
        (1.5, 1, "running"),
        (True, 0, "running"),
    ],
)
def test_invalid_piece_counts_rejected(total, good, state):
    with pytest.raises(ValidationError):
        event(0, 60, total, good, state)


def test_naive_timestamps_rejected():
    with pytest.raises(ValidationError, match="UTC offset"):
        Interval(start=datetime(2026, 1, 1), end=datetime(2026, 1, 2))


def test_breaks_must_be_disjoint():
    with pytest.raises(ValidationError):
        shift(
            breaks=(
                Interval(start=T, end=T + timedelta(minutes=20)),
                Interval(start=T + timedelta(minutes=10), end=T + timedelta(minutes=30)),
            )
        )


def test_events_for_other_machine_do_not_change_report():
    other = event(0, 60, 600, 600).model_copy(update={"machine_id": "other"})
    assert calculate_oee(shift(), [other]).coverage == 0
