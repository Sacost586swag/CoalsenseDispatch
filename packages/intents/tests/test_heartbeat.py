"""Contrato de latido y consumidor sin reloj remoto, reproducción ni datos privados."""

from copy import deepcopy

import pytest
from coalsense_common import new_id
from coalsense_intents import ContractError, validate_heartbeat
from coalsense_intents.heartbeat import HeartbeatReceiver


def packet(*, reachable: bool = True, sequence: int = 1, instance: str | None = None):
    return {
        "event": "heartbeat",
        "schema_version": 1,
        "instance_id": instance or new_id(),
        "sequence": sequence,
        "wall_ts": "2026-11-17T00:00:00.000Z",
        "state": {
            "stop_reachable": reachable,
            "revision": 1,
            "updated_at": "2026-11-17T00:00:00.000Z",
            "routes": [
                {
                    "identifier": "keyboard@1",
                    "modality": "keyboard_mouse",
                    "healthy": reachable,
                    "reason": "healthy" if reachable else "device_unavailable",
                }
            ],
        },
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "no_route",
        "false_with_healthy_route",
        "true_with_unhealthy_route",
        "reason",
        "extra",
        "timestamp",
        "sequence",
        "bool_sequence",
        "duplicate",
        "private",
        "invalid_instance",
    ],
)
def test_invalid_or_inconsistent_wire_event_is_rejected_without_echo(mutation: str) -> None:
    value = packet()
    if mutation == "no_route":
        value["state"]["routes"] = []
    elif mutation == "false_with_healthy_route":
        value["state"]["stop_reachable"] = False
    elif mutation == "true_with_unhealthy_route":
        value["state"]["routes"][0].update(healthy=False, reason="stale")
    elif mutation == "reason":
        value["state"]["routes"][0]["reason"] = "stale"
    elif mutation == "extra":
        value["state"]["routes"][0]["profile"] = "private condition"
    elif mutation == "timestamp":
        value["wall_ts"] = "tomorrow"
    elif mutation == "sequence":
        value["sequence"] = 9007199254740992
    elif mutation == "bool_sequence":
        value["sequence"] = True
    elif mutation == "duplicate":
        value["state"]["routes"] *= 2
    elif mutation == "invalid_instance":
        value["instance_id"] = "not-an-instance"
    else:
        value["audio"] = "private audio"
    with pytest.raises(ContractError) as caught:
        validate_heartbeat(value)
    assert "private" not in str(caught.value)


def test_valid_event_is_copied_and_empty_unreachable_state_is_valid() -> None:
    value = packet()
    result = validate_heartbeat(value)
    value["state"]["routes"][0]["healthy"] = False
    assert result["state"]["routes"][0]["healthy"]
    empty = packet(reachable=False)
    empty["state"]["routes"] = []
    assert not validate_heartbeat(empty)["state"]["stop_reachable"]


def test_never_adopts_an_instance_from_incoming_data_and_disconnect_needs_rebind() -> None:
    receiver = HeartbeatReceiver(on_unreachable=lambda: None)
    event = packet()
    assert not receiver.receive(event) and not receiver.stop_reachable
    receiver.bind(event["instance_id"])
    assert receiver.receive(event) and receiver.stop_reachable
    receiver.disconnect()
    event["sequence"] = 2
    assert not receiver.receive(event) and not receiver.stop_reachable
    receiver.bind(event["instance_id"])
    assert receiver.receive(event) and receiver.stop_reachable


def test_expiry_uses_receipt_clock_and_replay_does_not_extend_it() -> None:
    now = [100]
    losses = []
    receiver = HeartbeatReceiver(
        on_unreachable=lambda: losses.append("lost"), clock=lambda: now[0], timeout_ns=10
    )
    event = packet()
    event["wall_ts"] = "2099-01-01T00:00:00.000Z"
    receiver.bind(event["instance_id"])
    assert receiver.receive(event)
    now[0] = 109
    assert not receiver.receive(event) and receiver.stop_reachable
    now[0] = 110
    assert not receiver.stop_reachable and losses == ["lost"]
    event["sequence"] = 2
    assert receiver.receive(event) and receiver.stop_reachable


def test_reconnect_preserves_high_water_mark_and_new_authenticated_instance_resets_it() -> None:
    receiver = HeartbeatReceiver(on_unreachable=lambda: None)
    event = packet(sequence=5)
    receiver.bind(event["instance_id"])
    assert receiver.receive(event)
    receiver.bind(event["instance_id"])
    assert not receiver.receive(event)
    event["sequence"] = 6
    assert receiver.receive(event)
    next_instance = packet()
    assert not receiver.receive(next_instance)
    receiver.bind(next_instance["instance_id"])
    assert receiver.receive(next_instance)


def test_old_revision_is_rejected_and_reported_loss_is_immediate() -> None:
    losses = []
    receiver = HeartbeatReceiver(on_unreachable=lambda: losses.append("lost"))
    event = packet()
    receiver.bind(event["instance_id"])
    assert receiver.receive(event)
    old = deepcopy(event)
    old.update(sequence=2)
    old["state"]["revision"] = 0
    assert not receiver.receive(old) and receiver.stop_reachable
    lost = packet(reachable=False, sequence=3, instance=event["instance_id"])
    lost["state"]["revision"] = 2
    assert receiver.receive(lost) and not receiver.stop_reachable
    assert losses == ["lost"]


def test_invalid_authenticated_packet_fails_closed_and_callback_failure_is_observable() -> None:
    def fail() -> None:
        raise RuntimeError("private connection details")

    receiver = HeartbeatReceiver(on_unreachable=fail)
    event = packet()
    receiver.bind(event["instance_id"])
    assert receiver.receive(event)
    assert not receiver.receive({"private": "condition"})
    assert not receiver.stop_reachable and receiver.notification_failures == 1


@pytest.mark.parametrize("deadline", [0, -1, True, 1.5])
def test_invalid_receiver_timeout_is_rejected(deadline: object) -> None:
    with pytest.raises(ValueError):
        HeartbeatReceiver(on_unreachable=lambda: None, timeout_ns=deadline)
