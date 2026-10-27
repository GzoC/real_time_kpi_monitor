"""Wait for actual consumer persistence, not just broker PUBACK or container uptime."""

import json
import time
from urllib.error import HTTPError
from urllib.request import urlopen

deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    try:
        with urlopen("http://127.0.0.1:8000/api/shifts/healthy/report", timeout=3) as response:
            report = json.load(response)
        if report["coverage"] == 1 and abs(report["oee"] - 0.98) < 1e-9:
            print("Container smoke passed: MQTT -> SQLite -> HTTP OEE 98%")
            break
    except HTTPError as exc:
        if exc.code != 404:
            raise
    time.sleep(0.2)
else:
    raise SystemExit("MQTT consumer did not persist a complete correct shift")
