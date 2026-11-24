"""Propiedades del bus (REQ-01-004 a 014); no necesita cámara, audio ni red."""

import threading

from coalsense_common import new_id
from coalsense_companion.bus.auth import AdapterRegistry
from coalsense_companion.bus.core import IntentBus
from coalsense_intents import Intent, intent_types
from hypothesis import given
from hypothesis import strategies as st


def message(kind: str, payload: object = None) -> dict[str, object]:
    value: dict[str, object] = {
        "id": new_id(),
        "type": kind,
        "monotonic_ts": 100,
        "wall_ts": "2026-11-16T10:00:00.000Z",
        "confidence": 0.95,
        "payload": {} if payload is None else payload,
    }
    if kind.startswith("approval."):
        value.update(pending_action_id=new_id(), content_digest="a" * 64)
    return value


def setup_bus(capacity: int = 4) -> tuple[IntentBus, AdapterRegistry, str, list[object], list[str]]:
    registry = AdapterRegistry()
    adapter = registry.register("voice@1.0.0", "voice", "person")
    records: list[object] = []
    stops: list[str] = []
    bus = IntentBus(
        registry,
        records.append,
        on_stop=lambda: stops.append("halt"),
        normal_capacity=capacity,
        approval_min_confidence=0.85,
    )
    return bus, registry, adapter.credential, records, stops


@given(
    st.lists(
        st.sampled_from(
            ["nav.next", "control.stop", "control.undo", "help.request_human", "approval.approve"]
        ),
        min_size=1,
        max_size=80,
    )
)
def test_preemptive_intentions_precede_all_normals_without_loss(kinds: list[str]) -> None:
    bus, _, credential, _, stops = setup_bus(1)
    received: list[Intent] = []
    bus.subscribe(intent_types(), received.append)
    for kind in kinds:
        assert bus.publish(message(kind), credential).accepted
    bus.drain()
    expected = [
        kind for kind in kinds if kind in {"control.stop", "control.undo", "help.request_human"}
    ]
    expected += [
        kind for kind in kinds if kind not in {"control.stop", "control.undo", "help.request_human"}
    ]
    assert [item["type"] for item in received] == expected
    assert len(stops) == kinds.count("control.stop")


def test_saturation_coalesces_only_adjacent_movement_and_never_drops_discrete_actions() -> None:
    bus, _, credential, records, _ = setup_bus(1)
    bus.publish(message("pointer.move", {"mode": "absolute", "x": 10, "y": 20}), credential)
    assert (
        bus.publish(
            message("pointer.move", {"mode": "absolute", "x": 30, "y": 40}), credential
        ).status
        == "coalesced"
    )
    bus.publish(message("pointer.click", {"button": "left"}), credential)
    assert (
        bus.publish(
            message("pointer.move", {"mode": "relative", "x": 1, "y": 1}), credential
        ).status
        == "dropped_continuous"
    )
    for kind in ("approval.approve", "approval.reject", "key.press", "pointer.scroll"):
        payload = (
            {"keys": ["Enter"]}
            if kind == "key.press"
            else {"dx": 0, "dy": 1}
            if kind == "pointer.scroll"
            else {}
        )
        assert bus.publish(message(kind, payload), credential).accepted
    received = bus.drain()
    assert len(received) == 6
    assert received[0]["payload"] == {"mode": "absolute", "x": 30, "y": 40}
    assert "dropped_continuous" in repr(records)


def test_relative_motion_is_added_not_replaced_when_coalesced() -> None:
    bus, _, credential, _, _ = setup_bus(1)
    for x in [2, 3, -1]:
        bus.publish(message("pointer.move", {"mode": "relative", "x": x, "y": 1}), credential)
    assert bus.drain()[0]["payload"] == {"mode": "relative", "x": 4, "y": 3}


def test_validation_and_consumer_failures_never_leak_text_or_mutate_other_consumers() -> None:
    bus, _, credential, records, _ = setup_bus()
    received: list[Intent] = []
    original = message("text.dictation", {"text": "texto-privado", "final": True})
    bus.subscribe(["text.dictation"], lambda item: item["payload"].update(text="changed"))
    bus.subscribe(["text.dictation"], lambda _: (_ for _ in ()).throw(ValueError("texto-privado")))
    bus.subscribe(["text.dictation"], received.append)
    assert bus.publish(original, credential).accepted
    original["payload"] = {"text": "later", "final": True}
    bus.drain()
    assert received[0]["payload"] == {"text": "texto-privado", "final": True}
    assert not bus.publish(
        message("text.dictation", {"text": "texto-privado"}), credential
    ).accepted
    assert "texto-privado" not in repr(records)


def test_stop_halts_synchronously_while_a_normal_consumer_is_blocked() -> None:
    bus, _, credential, _, stops = setup_bus()
    entered, release = threading.Event(), threading.Event()

    def slow(_: Intent) -> None:
        entered.set()
        assert release.wait(3)

    bus.subscribe(["nav.next"], slow)
    bus.publish(message("nav.next"), credential)
    worker = threading.Thread(target=bus.drain_one)
    worker.start()
    try:
        assert entered.wait(3)
        assert bus.publish(message("control.stop"), credential).accepted
        assert stops == ["halt"]  # el consumidor lento no se ha liberado todavía
    finally:
        release.set()
        worker.join(3)
    assert not worker.is_alive()


def test_stop_is_still_queued_if_the_halt_port_or_audit_sink_fails() -> None:
    bus, _, credential, _, _ = setup_bus()

    def broken() -> None:
        raise OSError("private hardware details")

    bus.on_stop = broken
    bus.audit = lambda _: broken()
    result = bus.publish(message("control.stop"), credential)
    assert result.status == "stop_fault" and result.accepted
    assert bus.last_halt_failed is True
    assert bus.audit_failures > 0
    assert bus.drain()[0]["type"] == "control.stop"


def test_input_priority_and_actor_are_derived_from_the_registered_session() -> None:
    bus, registry, credential, _, _ = setup_bus()
    raw = message("nav.next") | {
        "priority": "preemptive",
        "actor_origin": "system",
        "adapter": "forged",
        "modality": "gaze",
    }
    assert bus.publish(raw, credential).accepted
    delivered = bus.drain()[0]
    assert (
        delivered["priority"],
        delivered["actor_origin"],
        delivered["adapter"],
        delivered["modality"],
    ) == ("normal", "person", "voice@1.0.0", "voice")
    assert not bus.publish(raw, "not-registered").accepted
    registry.revoke(credential)
    assert not bus.publish(raw, credential).accepted


def test_system_cannot_approve_and_caregiver_origin_survives_for_policy_validation() -> None:
    bus, registry, _, records, _ = setup_bus()
    system = registry.register("system@1", "keyboard_mouse", "system")
    caregiver = registry.register("caregiver@1", "keyboard_mouse", "caregiver")
    approval = message("approval.approve")
    assert not bus.publish(approval | {"actor_origin": "person"}, system.credential).accepted
    assert bus.publish(approval, caregiver.credential).accepted
    assert bus.drain()[0]["actor_origin"] == "caregiver"
    assert system.credential not in repr(system) + repr(records)


def test_unsubscribe_is_idempotent_even_for_duplicate_callbacks() -> None:
    bus, _, credential, _, _ = setup_bus()
    seen: list[Intent] = []
    remove = bus.subscribe(["nav.next"], seen.append)
    bus.subscribe(["nav.next"], seen.append)
    remove()
    remove()
    bus.publish(message("nav.next"), credential)
    bus.drain()
    assert len(seen) == 1
