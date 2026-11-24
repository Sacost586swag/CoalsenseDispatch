"""Canal local: autenticación, origen, repetición y JSON sin valores en errores."""

import json

import pytest
from coalsense_companion.bus.session import (
    PipeSession,
    SessionRejected,
    decode_message,
    encode_message,
)

from .test_core import message, setup_bus


def session():
    bus, registry, credential, _, _ = setup_bus()
    expected = registry.authenticate(credential)
    assert expected is not None
    return PipeSession(bus, registry, credential, expected), bus, registry, credential


def request(credential: str, *, sequence: int = 1, kind: str = "intent", value=None) -> bytes:
    return encode_message(
        {
            "version": 1,
            "sequence": sequence,
            "credential": credential,
            "kind": kind,
            kind: message("nav.next") if value is None else value,
        }
    )


def test_valid_session_publishes_only_via_bus_and_never_echoes_credential() -> None:
    channel, bus, _, credential = session()
    response = channel.handle(request(credential), received_ns=100)
    assert decode_message(response) == {
        "version": 1,
        "sequence": 1,
        "accepted": True,
        "status": "queued",
    }
    assert bus.drain()[0]["type"] == "nav.next"
    assert credential not in response.decode() and credential not in repr(channel)


def test_unregistered_process_or_revoked_credential_cannot_publish() -> None:
    channel, bus, registry, credential = session()
    registry.revoke(credential)
    with pytest.raises(SessionRejected):
        channel.handle(request(credential), received_ns=100)
    assert bus.drain() == []


def test_credential_from_another_adapter_is_rejected_even_if_registered() -> None:
    channel, bus, registry, _ = session()
    other = registry.register("vision@1", "head_gesture", "person")
    with pytest.raises(SessionRejected):
        channel.handle(request(other.credential), received_ns=100)
    assert not bus.drain()


def test_actor_origin_is_derived_from_authenticated_session() -> None:
    channel, bus, _, credential = session()
    value = message("nav.next") | {
        "actor_origin": "system",
        "modality": "gaze",
        "adapter": "forged",
    }
    channel.handle(request(credential, value=value), received_ns=100)
    received = bus.drain()[0]
    assert received["actor_origin"] == "person" and received["modality"] == "voice"
    assert received["adapter"] == "voice@1.0.0"


@pytest.mark.parametrize("origin,accepted", [("system", False), ("caregiver", True)])
def test_system_approval_is_rejected_and_caregiver_remains_marked(
    origin: str, accepted: bool
) -> None:
    bus, registry, _, _, _ = setup_bus()
    adapter = registry.register("keyboard@1", "keyboard_mouse", origin)
    expected = registry.authenticate(adapter.credential)
    assert expected is not None
    channel = PipeSession(bus, registry, adapter.credential, expected)
    response = decode_message(
        channel.handle(
            request(adapter.credential, value=message("approval.approve")), received_ns=100
        )
    )
    assert response["accepted"] == accepted
    received = bus.drain()
    assert bool(received) == accepted
    if received:
        assert received[0]["actor_origin"] == "caregiver"


def test_health_is_strict_and_is_consumed_once_with_receipt_time() -> None:
    channel, _, _, credential = session()
    health = {
        "device_streaming": True,
        "model_loaded": False,
        "adapter_responding": True,
        "stop_bound": True,
    }
    response = channel.handle(request(credential, kind="health", value=health), received_ns=123)
    assert decode_message(response)["status"] == "health_received"
    receipt = channel.take_health()
    assert receipt is not None and receipt.received_ns == 123
    assert receipt.evidence.device_streaming and not receipt.evidence.model_loaded
    assert channel.take_health() is None
    health["device_streaming"] = "private camera name"
    with pytest.raises(SessionRejected) as caught:
        channel.handle(
            request(credential, sequence=2, kind="health", value=health), received_ns=124
        )
    assert "private" not in str(caught.value)


@pytest.mark.parametrize("sequence", [1, 3, True, 2.0])
def test_duplicate_out_of_order_and_invalid_sequence_close_session(sequence: object) -> None:
    channel, bus, _, credential = session()
    channel.handle(request(credential), received_ns=100)
    with pytest.raises(SessionRejected):
        channel.handle(request(credential, sequence=sequence), received_ns=100)
    with pytest.raises(SessionRejected):
        channel.handle(request(credential, sequence=2), received_ns=100)
    assert len(bus.drain()) == 1


@pytest.mark.parametrize(
    "raw",
    [
        b'{"version":1,"version":1}',
        b'{"value":NaN}',
        b"[]",
        b"{}x",
        b"\xff",
        b"",
        b'{"private":"' + b"x" * 65536 + b'"}',
    ],
)
def test_malformed_json_is_rejected_without_echo(raw: bytes) -> None:
    with pytest.raises(SessionRejected) as caught:
        decode_message(raw)
    assert "private" not in str(caught.value)


def test_unknown_fields_do_not_reach_bus_and_stop_is_synchronous() -> None:
    channel, bus, _, credential = session()
    stops = []
    bus.on_stop = lambda: stops.append("halt")
    channel.handle(request(credential, value=message("control.stop")), received_ns=100)
    assert stops == ["halt"]  # no drain para detener
    forged = json.loads(request(credential, sequence=2)) | {"shell": "private command"}
    with pytest.raises(SessionRejected):
        channel.handle(encode_message(forged), received_ns=101)
    assert len(bus.drain()) == 1
