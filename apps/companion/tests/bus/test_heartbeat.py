"""Emisión periódica y expiración local sin depender del enlace ni de modelos."""

import threading

import pytest
from coalsense_companion.bus.stop_state import StopState
from coalsense_companion.uplink.heartbeat import HeartbeatPublisher
from coalsense_intents import HeartbeatEvent
from coalsense_intents.heartbeat import HeartbeatReceiver

from .test_stop_state import Clock, healthy


def test_tick_emits_minimal_schema_event_and_route_expiry_reaches_consumer() -> None:
    clock = Clock()
    losses, events = [], []
    state = StopState(on_unreachable=lambda _: losses.append("local"), clock=clock, max_age_ns=10)
    route = state.register("voice@1", "voice")
    publisher = HeartbeatPublisher(state, events.append)
    receiver = HeartbeatReceiver(on_unreachable=lambda: losses.append("remote"))
    receiver.bind(publisher.instance_id)
    assert publisher.tick()
    assert not events[-1]["state"]["stop_reachable"]
    state.observe(route, healthy())
    assert publisher.tick() and receiver.receive(events[-1])
    assert receiver.stop_reachable
    clock.now = 10
    assert publisher.tick() and receiver.receive(events[-1])
    assert not receiver.stop_reachable and losses == ["local", "remote"]
    assert [event["sequence"] for event in events] == [1, 2, 3]
    assert set(events[-1]) == {
        "event",
        "schema_version",
        "instance_id",
        "sequence",
        "wall_ts",
        "state",
    }


def test_send_failure_does_not_keep_local_route_alive_and_does_not_log_exception() -> None:
    clock = Clock()
    losses = []
    state = StopState(on_unreachable=lambda _: losses.append("halt"), clock=clock, max_age_ns=10)
    route = state.register("voice@1", "voice")
    state.observe(route, healthy())

    def fail(_: HeartbeatEvent) -> None:
        raise RuntimeError("private network details")

    publisher = HeartbeatPublisher(state, fail)
    assert not publisher.tick() and publisher.send_failures == 1
    clock.now = 10
    assert not publisher.tick() and losses == ["halt"]
    assert publisher.send_failures == 2 and "private" not in repr(publisher)


def test_periodic_worker_emits_without_manual_ticks_and_can_stop_immediately() -> None:
    stopped = threading.Event()
    events: list[HeartbeatEvent] = []

    def collect(event: HeartbeatEvent) -> None:
        events.append(event)
        if len(events) == 2:
            stopped.set()

    publisher = HeartbeatPublisher(
        StopState(on_unreachable=lambda _: None), collect, interval_seconds=0.01
    )
    worker = threading.Thread(target=publisher.run, args=(stopped,))
    worker.start()
    worker.join(3)
    assert not worker.is_alive() and len(events) == 2


@pytest.mark.parametrize("interval", [0, -1, float("nan"), float("inf"), True])
def test_invalid_heartbeat_interval_is_rejected(interval: float) -> None:
    with pytest.raises(ValueError):
        HeartbeatPublisher(
            StopState(on_unreachable=lambda _: None), lambda _: None, interval_seconds=interval
        )
