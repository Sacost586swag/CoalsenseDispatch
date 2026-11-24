"""La salud proviene del receptor enlazado, caduca localmente y no se comparte entre sesiones."""

import asyncio
from dataclasses import replace

from coalsense_common import new_id
from coalsense_intents.heartbeat import HeartbeatReceiver
from coalsense_orchestrator.policy.health import DenyStopHealth, HeartbeatStopHealth

from .test_engine import principal


def test_authenticated_receiver_expiry_and_disconnection_are_seen_by_the_policy_adapter() -> None:
    actor = principal()
    now = [0]
    receiver = HeartbeatReceiver(on_unreachable=lambda: None, clock=lambda: now[0])
    health = HeartbeatStopHealth(
        lambda session: receiver if session.session_id == actor.session_id else None
    )
    instance = new_id()
    receiver.bind(instance)
    assert asyncio.run(health.reachable(actor)) is False
    packet = {
        "event": "heartbeat",
        "schema_version": 1,
        "instance_id": instance,
        "sequence": 1,
        "wall_ts": "2026-11-18T00:00:00.000Z",
        "state": {
            "stop_reachable": True,
            "revision": 1,
            "updated_at": "2026-11-18T00:00:00.000Z",
            "routes": [
                {
                    "identifier": "keyboard@1",
                    "modality": "keyboard_mouse",
                    "healthy": True,
                    "reason": "healthy",
                }
            ],
        },
    }
    assert receiver.receive(packet)
    assert asyncio.run(health.reachable(actor)) is True
    assert asyncio.run(health.reachable(replace(actor, session_id=new_id()))) is False
    now[0] = receiver.timeout_ns
    assert asyncio.run(health.reachable(actor)) is False
    receiver.disconnect()
    assert asyncio.run(health.reachable(actor)) is False
    assert asyncio.run(DenyStopHealth().reachable(actor)) is False
