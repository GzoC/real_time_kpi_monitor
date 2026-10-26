import pytest

from kpi_monitor.domain import calculate_oee
from kpi_monitor.simulation import scenario
from kpi_monitor.storage import ConflictError, Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "test.db")


def test_replay_is_idempotent(store):
    shift, events = scenario("reference")
    assert store.add_shift(shift)
    assert not store.add_shift(shift)
    assert store.ingest(events) == {"inserted": 50, "duplicates": 0}
    assert store.ingest(events) == {"inserted": 0, "duplicates": 50}
    report = calculate_oee(store.shift("reference"), store.events(shift))
    assert report.oee == pytest.approx(0.684)


def test_batch_conflict_rolls_back_every_event(store):
    shift, events = scenario("reference")
    store.add_shift(shift)
    conflicting = events[0].model_copy(update={"event_id": "different"})
    with pytest.raises(ConflictError, match="overlaps"):
        store.ingest([events[0], events[1], conflicting])
    assert store.events(shift) == []


def test_reused_id_with_different_content_is_conflict(store):
    _, events = scenario("healthy")
    store.ingest([events[0]])
    with pytest.raises(ConflictError, match="different content"):
        store.ingest([events[0].model_copy(update={"good_count": 0})])


def test_shift_configuration_is_immutable(store):
    shift, _ = scenario("healthy")
    store.add_shift(shift)
    with pytest.raises(ConflictError):
        store.add_shift(shift.model_copy(update={"ideal_cycle_seconds": 12}))


def test_out_of_order_non_overlapping_events_are_supported(store):
    shift, events = scenario("healthy")
    store.ingest(list(reversed(events)))
    assert store.events(shift) == events


def test_polling_does_not_duplicate_or_unacknowledge_alerts(store):
    shift, events = scenario("reference")
    report = calculate_oee(shift, events)
    store.sync_alerts(report)
    alert = store.alerts()[0]
    store.acknowledge(alert["id"])
    store.sync_alerts(report)
    assert len(store.alerts()) == 1
    assert store.alerts()[0]["acknowledged"] == 1


def test_resolved_alert_recurs_unacknowledged(store):
    shift, events = scenario("healthy")
    incomplete = calculate_oee(shift, [])
    store.sync_alerts(incomplete)
    store.acknowledge(store.alerts()[0]["id"])
    store.sync_alerts(calculate_oee(shift, events))
    assert store.alerts()[0]["active"] == 0
    store.sync_alerts(incomplete)
    assert store.alerts()[0]["acknowledged"] == 0
    assert store.alerts()[0]["active"] == 1


def test_missing_records_are_explicit(store):
    with pytest.raises(KeyError):
        store.shift("missing")
    with pytest.raises(KeyError):
        store.acknowledge(999)


def test_rejected_messages_are_counted(store):
    store.record_rejection("invalid payload")
    assert store.rejection_count() == 1


@pytest.mark.parametrize(
    "name,oee,coverage",
    [
        ("reference", 0.684, 1.0),
        ("healthy", 0.98, 1.0),
        ("sensor_loss", None, 0.8),
        ("zero_quality", 0.0, 1.0),
        ("no_data", None, 0.0),
    ],
)
def test_scenarios_have_documented_outcomes(name, oee, coverage):
    shift, events = scenario(name)
    result = calculate_oee(shift, events)
    assert result.coverage == pytest.approx(coverage)
    if oee is None:
        assert result.oee is None
    else:
        assert result.oee == pytest.approx(oee)
