import pytest
from fastapi.testclient import TestClient

from kpi_monitor.api import create_app
from kpi_monitor.simulation import scenario


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "api.db", demo_mode=True)) as value:
        yield value


def test_demo_can_be_replayed_without_changing_oee(client):
    assert client.post("/api/demo/reference").json()["inserted"] == 50
    assert client.post("/api/demo/reference").json()["duplicates"] == 50
    result = client.get("/api/shifts/reference/report")
    assert result.status_code == 200
    assert result.json()["oee"] == pytest.approx(0.684)
    assert len(client.get("/api/shifts/reference/events").json()) == 50
    assert len(client.get("/api/shifts").json()) == 1


def test_unknown_metrics_serialize_as_null(client):
    client.post("/api/demo/no_data")
    result = client.get("/api/shifts/no_data/report")
    assert result.status_code == 200
    assert result.json()["oee"] is None
    assert result.json()["status"] == "insufficient_data"


def test_alert_acknowledgement_survives_dashboard_polling(client):
    client.post("/api/demo/reference")
    client.get("/api/shifts/reference/report")
    alert_id = client.get("/api/alerts").json()[0]["id"]
    assert client.post(f"/api/alerts/{alert_id}/acknowledge").status_code == 200
    client.get("/api/shifts/reference/report")
    alerts = client.get("/api/alerts?shift_id=reference").json()
    assert len(alerts) == 1
    assert alerts[0]["acknowledged"] == 1


def test_conflicting_event_returns_conflict_not_success(client):
    _, events = scenario("healthy")
    payload = events[0].model_dump(mode="json")
    assert client.post("/api/events", json=[payload]).status_code == 200
    payload["good_count"] = 0
    assert client.post("/api/events", json=[payload]).status_code == 409


@pytest.mark.parametrize(
    "change",
    [
        {"good_count": -1},
        {"total_count": 1.5},
        {"state": "unknown"},
        {"start": "2026-01-01T00:00:00"},
        {"extra": "forbidden"},
    ],
)
def test_invalid_telemetry_returns_422(client, change):
    _, events = scenario("healthy")
    payload = events[0].model_dump(mode="json")
    payload.update(change)
    assert client.post("/api/events", json=[payload]).status_code == 422


def test_batch_size_limits(client):
    assert client.post("/api/events", json=[]).status_code == 422


def test_missing_resources_are_404(client):
    assert client.get("/api/shifts/missing/report").status_code == 404
    assert client.post("/api/alerts/999/acknowledge").status_code == 404
    assert client.post("/api/demo/missing").status_code == 404


def test_demo_is_disabled_by_default(tmp_path):
    with TestClient(create_app(tmp_path / "disabled.db")) as client:
        assert client.post("/api/demo/healthy").status_code == 403
        assert client.get("/api/demo/scenarios").json()["scenarios"] == {}


def test_health_checks_storage(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_shift_can_be_created_and_conflicts_are_explicit(client):
    shift, _ = scenario("healthy")
    payload = shift.model_dump(mode="json")
    assert client.post("/api/shifts", json=payload).status_code == 201
    payload["ideal_cycle_seconds"] = 20
    assert client.post("/api/shifts", json=payload).status_code == 409
