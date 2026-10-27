"""MQTT 3.1.1 transport. QoS 1 delivery, durable commit before acknowledgement."""

import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from .domain import ProductionEvent, Shift
from .storage import ConflictError, Store

LOG = logging.getLogger(__name__)
MAX_PAYLOAD_BYTES = 65536


@dataclass(frozen=True)
class MQTTConfig:
    host: str = "127.0.0.1"
    port: int = 1883
    prefix: str = "kpi/v1"
    client_id: str = "kpi-monitor-local"
    username: str | None = None
    password: str | None = None
    tls: bool = False
    ca_file: str | None = None

    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ValueError("MQTT port must be between 1 and 65535")
        if not self.prefix or any(c in self.prefix for c in "+#\x00"):
            raise ValueError("MQTT prefix must be a concrete topic prefix")
        if not self.client_id:
            raise ValueError("MQTT requires a stable unique consumer client ID")
        if self.password and not self.username:
            raise ValueError("MQTT password requires a username")
        if self.ca_file and not self.tls:
            raise ValueError("MQTT_CA_FILE requires MQTT_TLS=true")

    @classmethod
    def from_env(cls):
        tls = os.getenv("MQTT_TLS", "false").lower()
        if tls not in {"true", "false"}:
            raise ValueError("MQTT_TLS must be true or false")
        return cls(
            host=os.getenv("MQTT_HOST", "127.0.0.1"),
            port=int(os.getenv("MQTT_PORT", "1883")),
            prefix=os.getenv("MQTT_PREFIX", "kpi/v1").rstrip("/"),
            client_id=os.getenv("MQTT_CLIENT_ID", "kpi-monitor-local"),
            username=os.getenv("MQTT_USERNAME"),
            password=os.getenv("MQTT_PASSWORD"),
            tls=tls == "true",
            ca_file=os.getenv("MQTT_CA_FILE") or None,
        )


def make_client(config: MQTTConfig, *, consumer=False):
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=config.client_id if consumer else "",
        clean_session=not consumer,
        manual_ack=consumer,
    )
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    if config.username:
        client.username_pw_set(config.username, config.password)
    if config.tls:
        client.tls_set(ca_certs=config.ca_file)  # Certificate and hostname verification stay on.
    return client


class MQTTIngestor:
    def __init__(self, store: Store, config: MQTTConfig):
        self.store = store
        self.config = config
        self.ready = threading.Event()
        self.failed = threading.Event()
        readiness = os.getenv("MQTT_READY_FILE")
        self.ready_file = Path(readiness) if readiness else None
        self._write_readiness(False)
        self.client = make_client(config, consumer=True)
        self.client.on_connect = self._connect
        self.client.on_subscribe = self._subscribed
        self.client.on_disconnect = self._disconnect
        self.client.on_message = self._message

    def _connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            LOG.error("MQTT connection refused: %s", reason_code)
            return
        client.subscribe([(f"{self.config.prefix}/shifts", 1), (f"{self.config.prefix}/events", 1)])

    def _write_readiness(self, ready: bool):
        if self.ready_file:
            self.ready_file.write_text("ready" if ready else "not_ready", encoding="utf-8")

    def _subscribed(self, client, userdata, mid, reason_codes, properties):
        if any(code.is_failure for code in reason_codes):
            self.failed.set()
            LOG.error("MQTT subscription refused")
        else:
            self._write_readiness(True)
            self.ready.set()
            LOG.info("MQTT subscriptions ready")

    def _disconnect(self, client, userdata, flags, reason_code, properties):
        self.ready.clear()
        self._write_readiness(False)
        if reason_code.is_failure:
            LOG.warning("MQTT disconnected; reconnecting with backoff")

    def handle(self, topic: str, payload: bytes):
        if len(payload) > MAX_PAYLOAD_BYTES:
            raise ValueError("payload exceeds 64 KiB")
        if topic == f"{self.config.prefix}/shifts":
            self.store.add_shift(Shift.model_validate_json(payload))
        elif topic == f"{self.config.prefix}/events":
            self.store.ingest([ProductionEvent.model_validate_json(payload)])
        else:
            raise ValueError("unsupported topic")

    def _message(self, client, userdata, message):
        try:
            try:
                self.handle(message.topic, message.payload)
            except (ValidationError, ConflictError, ValueError) as exc:
                # Store categories only: never retain/log raw payloads or credentials.
                self.store.record_rejection(type(exc).__name__)
                LOG.warning("MQTT payload rejected: %s", type(exc).__name__)
            client.ack(message.mid, message.qos)
        except sqlite3.Error:
            # Do not ACK an uncommitted message. Restart the process with the same
            # client ID to resume the broker session after storage is repaired.
            LOG.exception("Storage unavailable; stopping MQTT consumer without ACK")
            self.failed.set()
            client.disconnect()

    def start(self):
        self.client.connect_async(self.config.host, self.config.port, keepalive=30)
        self.client.loop_start()

    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()
        self.ready.clear()
        self._write_readiness(False)

    def run(self):
        self.start()
        try:
            while not self.failed.wait(0.5):
                pass
            raise RuntimeError("MQTT worker failed; check storage, ACL and logs")
        finally:
            self.stop()


def publish_scenario(
    config: MQTTConfig, shift: Shift, events: list[ProductionEvent], delay: float = 0.1
) -> int:
    if delay < 0:
        raise ValueError("delay cannot be negative")
    client = make_client(config)
    connected = threading.Event()

    def on_connect(client, userdata, flags, reason_code, properties):
        if not reason_code.is_failure:
            connected.set()

    client.on_connect = on_connect
    client.connect(config.host, config.port, keepalive=30)
    client.loop_start()
    try:
        if not connected.wait(10):
            raise TimeoutError("MQTT connection was not accepted")
        for index, record in enumerate([shift, *events]):
            suffix = "shifts" if isinstance(record, Shift) else "events"
            info = client.publish(f"{config.prefix}/{suffix}", record.model_dump_json(), qos=1)
            info.wait_for_publish(timeout=10)
            if not info.is_published():
                raise TimeoutError("MQTT broker did not acknowledge publication")
            if index and delay:
                time.sleep(delay)
        return len(events)
    finally:
        client.disconnect()
        client.loop_stop()
