"""Real TCP broker integration; no mocked MQTT success paths."""

import asyncio
import socket
import threading
import time
from dataclasses import replace

import pytest
from amqtt.broker import Broker

from kpi_monitor.domain import calculate_oee
from kpi_monitor.mqtt import MQTTConfig, MQTTIngestor, make_client, publish_scenario
from kpi_monitor.simulation import scenario
from kpi_monitor.storage import Store


@pytest.fixture
def broker():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    ready, stop = threading.Event(), threading.Event()
    errors = []

    async def serve():
        server = Broker(
            {
                "listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{port}"}},
                "plugins": {
                    "amqtt.plugins.authentication.AnonymousAuthPlugin": {"allow_anonymous": False}
                },
            }
        )
        await server.start()
        ready.set()
        try:
            while not stop.is_set():
                await asyncio.sleep(0.02)
        finally:
            await server.shutdown()

    def run():
        try:
            asyncio.run(serve())
        except Exception as exc:
            errors.append(exc)
            ready.set()

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    assert ready.wait(10), "broker failed to start"
    assert not errors
    try:
        # aMQTT deliberately discards disconnected anonymous sessions. A named
        # identity exercises its persistent-session path (not an auth/TLS test).
        yield MQTTConfig(port=port, client_id=f"test-consumer-{port}", username="integration-test")
    finally:
        stop.set()
        worker.join(10)
        assert not worker.is_alive()
        assert not errors


def eventually(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.03)
    pytest.fail("MQTT observable state did not converge before timeout")


def test_real_broker_replay_reconnect_and_rejections(broker, tmp_path, monkeypatch):
    readiness = tmp_path / "consumer.ready"
    monkeypatch.setenv("MQTT_READY_FILE", str(readiness))
    store = Store(tmp_path / "mqtt.db")
    shift, events = scenario("reference")
    consumer = MQTTIngestor(store, broker)
    consumer.start()
    try:
        assert consumer.ready.wait(8)
        assert readiness.read_text() == "ready"
        assert publish_scenario(broker, shift, events, delay=0) == 50
        eventually(lambda: len(store.events(shift)) == 50)
        assert calculate_oee(store.shift(shift.shift_id), store.events(shift)).oee == pytest.approx(
            0.684
        )
        # New network connection, same persistent client identity and durable DB.
        consumer.stop()
        assert readiness.read_text() == "not_ready"
        consumer = MQTTIngestor(store, broker)
        consumer.start()
        assert consumer.ready.wait(8)
        publish_scenario(broker, shift, events, delay=0)
        publisher = make_client(broker)
        publisher.connect(broker.host, broker.port)
        publisher.loop_start()
        try:
            info = publisher.publish(f"{broker.prefix}/events", b"{broken json", qos=1)
            info.wait_for_publish(5)
            info = publisher.publish(
                f"{broker.prefix}/events",
                events[0].model_copy(update={"good_count": 0}).model_dump_json(),
                qos=1,
            )
            info.wait_for_publish(5)
            eventually(lambda: store.rejection_count() == 2)
        finally:
            publisher.disconnect()
            publisher.loop_stop()
        assert len(store.events(shift)) == 50
        assert calculate_oee(shift, store.events(shift)).oee == pytest.approx(0.684)
    finally:
        consumer.stop()


def test_payload_size_and_topic_are_bounded(tmp_path):
    consumer = MQTTIngestor(Store(tmp_path / "db"), MQTTConfig())
    with pytest.raises(ValueError, match="64 KiB"):
        consumer.handle("kpi/v1/events", b"x" * 65537)
    with pytest.raises(ValueError, match="unsupported"):
        consumer.handle("not/a/topic", b"{}")


def test_persistent_subscription_delivers_queued_events_after_reconnect(broker, tmp_path):
    store = Store(tmp_path / "queued.db")
    shift, events = scenario("healthy")
    consumer = MQTTIngestor(store, broker)
    consumer.start()
    assert consumer.ready.wait(8)
    consumer.stop()
    publish_scenario(broker, shift, events, delay=0)
    assert store.events(shift) == []
    resumed = MQTTIngestor(store, broker)
    resumed.start()
    try:
        assert resumed.ready.wait(8)
        eventually(lambda: len(store.events(shift)) == 50)
        assert calculate_oee(store.shift("healthy"), store.events(shift)).oee == pytest.approx(0.98)
    finally:
        resumed.stop()


@pytest.mark.parametrize(
    "changes",
    [
        {"port": 0},
        {"prefix": "kpi/#"},
        {"client_id": ""},
        {"password": "secret"},
        {"ca_file": "test.pem"},
    ],
)
def test_invalid_mqtt_configuration_fails_before_connect(changes):
    with pytest.raises(ValueError):
        replace(MQTTConfig(), **changes)
