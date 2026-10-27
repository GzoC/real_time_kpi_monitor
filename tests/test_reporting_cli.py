import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from kpi_monitor.api import create_app
from kpi_monitor.cli import main
from kpi_monitor.domain import Shift
from kpi_monitor.reports import telemetry_metadata, time_series
from kpi_monitor.simulation import scenario


def test_time_buckets_do_not_turn_breaks_or_missing_intervals_into_zero():
    shift, events = scenario("sensor_loss")
    points = time_series(shift, events)
    assert len(points) == 6
    assert points[2]["oee"] == 0
    assert points[3]["status"] == "planned_break"
    assert points[3]["coverage"] is None
    assert points[4]["oee"] is None
    assert points[4]["coverage"] == 0.5


def test_external_freshness_and_historical_demo_are_distinct():
    shift, events = scenario("reference")
    now = shift.end + timedelta(days=20)
    synthetic = telemetry_metadata(shift, events, now=now)
    assert not synthetic["stale"]
    assert synthetic["event_age_seconds"] > 0
    external = shift.model_copy(update={"source": "external"})
    live = telemetry_metadata(external, events[:1], now=shift.start + timedelta(minutes=20))
    assert live["stale"] and live["phase"] == "in_progress"
    assert telemetry_metadata(external, [], now=shift.start)["stale"]
    assert telemetry_metadata(external, events, now=shift.start)["clock_ahead"]


def test_shift_duration_is_bounded():
    shift, _ = scenario("reference")
    with pytest.raises(ValueError, match="24 hours"):
        Shift(**{**shift.model_dump(), "end": shift.end + timedelta(days=1)})


def test_snapshot_provides_consistent_counts_and_metadata(tmp_path):
    with TestClient(create_app(tmp_path / "db", demo_mode=True)) as client:
        client.post("/api/demo/reference")
        response = client.get("/api/shifts/reference/snapshot")
        data = response.json()
        assert data["report"]["oee"] == pytest.approx(0.684)
        assert data["event_count"] == len(data["events"]) == 50
        assert data["metadata"]["source"] == "synthetic"
        assert data["metadata"]["scope"] == "full_shift"
        assert response.headers["cache-control"] == "no-store"
        assert client.get("/api/shifts/reference/snapshot?minutes=0").status_code == 422


def test_cli_export_import_report_and_duplicate_replay(tmp_path, capsys):
    folder = tmp_path / "fixture"
    db = str(tmp_path / "import.db")
    assert main(["export", "reference", str(folder)]) == 0
    capsys.readouterr()
    args = ["--db", db, "import", str(folder / "shift.json"), str(folder / "events.jsonl")]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["inserted"] == 50
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["duplicates"] == 50
    assert main(["--db", db, "report", "reference"]) == 0
    assert json.loads(capsys.readouterr().out)["oee"] == pytest.approx(0.684)
    assert main(["export", "reference", str(folder)]) == 1


def test_cli_invalid_import_does_not_insert_partial_events(tmp_path):
    folder = tmp_path / "fixture"
    main(["export", "reference", str(folder)])
    with (folder / "events.jsonl").open("a") as stream:
        stream.write("not json\n")
    db = tmp_path / "invalid.db"
    assert (
        main(["--db", str(db), "import", str(folder / "shift.json"), str(folder / "events.jsonl")])
        == 1
    )
    assert not db.exists()
