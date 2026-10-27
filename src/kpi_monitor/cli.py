"""Runnable demo, local HTTP service and inspectable import/replay tools."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from .domain import ProductionEvent, Shift, calculate_oee
from .simulation import SCENARIOS, scenario
from .storage import Store


def parser():
    root = argparse.ArgumentParser(description="Industrial KPI Monitor · OEE auditable")
    root.add_argument("--db", default=os.getenv("KPI_DB_PATH", "var/monitor.db"))
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("demo", "serve"):
        command = commands.add_parser(name)
        command.add_argument("--host", default="127.0.0.1")
        command.add_argument("--port", default=8000, type=int)
    seed = commands.add_parser("seed", help="Load one deterministic synthetic scenario")
    seed.add_argument("scenario", choices=SCENARIOS, default="reference", nargs="?")
    report = commands.add_parser("report")
    report.add_argument("shift_id")
    export = commands.add_parser("export", help="Export a reproducible synthetic fixture")
    export.add_argument("scenario", choices=SCENARIOS)
    export.add_argument("directory", type=Path)
    ingest = commands.add_parser("import", help="Import shift JSON and event JSONL")
    ingest.add_argument("shift", type=Path)
    ingest.add_argument("events", type=Path)
    commands.add_parser("mqtt-listen", help="Consume MQTT into SQLite; configuration via env")
    replay = commands.add_parser("mqtt-replay", help="Publish synthetic history via QoS 1")
    replay.add_argument("scenario", choices=SCENARIOS, default="reference", nargs="?")
    replay.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Seconds between historical records (not simulated time)",
    )
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        if args.command in {"serve", "demo"}:
            import uvicorn

            from .api import create_app

            if args.command == "demo":
                store = Store(args.db)
                shift, events = scenario("reference")
                store.add_shift(shift)
                store.ingest(events)
            app = create_app(args.db, demo_mode=args.command == "demo")
            uvicorn.run(app, host=args.host, port=args.port)
        elif args.command == "seed":
            shift, events = scenario(args.scenario)
            store = Store(args.db)
            store.add_shift(shift)
            print(json.dumps({"shift_id": shift.shift_id, **store.ingest(events)}))
        elif args.command == "report":
            store = Store(args.db)
            shift = store.shift(args.shift_id)
            print(calculate_oee(shift, store.events(shift)).model_dump_json(indent=2))
        elif args.command == "export":
            shift, events = scenario(args.scenario)
            args.directory.mkdir(parents=True, exist_ok=True)
            for filename in ("shift.json", "events.jsonl"):
                if (args.directory / filename).exists():
                    raise ValueError(f"refusing to overwrite {filename}; choose a new directory")
            (args.directory / "shift.json").write_text(shift.model_dump_json(indent=2), "utf-8")
            (args.directory / "events.jsonl").write_text(
                "".join(e.model_dump_json() + "\n" for e in events), "utf-8"
            )
            print(f"Exported {len(events)} synthetic intervals to {args.directory}")
        elif args.command == "import":
            if args.shift.stat().st_size > 65536 or args.events.stat().st_size > 20_000_000:
                raise ValueError("import exceeds 64 KiB shift / 20 MB events limit")
            shift = Shift.model_validate_json(args.shift.read_text("utf-8"))
            events = [
                ProductionEvent.model_validate_json(line)
                for line in args.events.read_text("utf-8").splitlines()
                if line.strip()
            ]
            if len(events) > 20000:
                raise ValueError("import exceeds 20000 intervals")
            if any(e.machine_id != shift.machine_id for e in events):
                raise ValueError("all imported intervals must belong to the shift's machine")
            store = Store(args.db)
            store.add_shift(shift)
            print(json.dumps(store.ingest(events)))
        elif args.command == "mqtt-listen":
            from .mqtt import MQTTConfig, MQTTIngestor

            MQTTIngestor(Store(args.db), MQTTConfig.from_env()).run()
        elif args.command == "mqtt-replay":
            from .mqtt import MQTTConfig, publish_scenario

            shift, events = scenario(args.scenario)
            count = publish_scenario(MQTTConfig.from_env(), shift, events, args.delay)
            print(
                f"Broker acknowledged {count} historical synthetic intervals. Check API coverage."
            )
        return 0
    except KeyboardInterrupt:
        return 130
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
