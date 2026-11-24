"""Integración bus→actuador con destino y hardware controlados, sin SendInput real."""

import threading
from collections.abc import Callable

import pytest
from coalsense_companion.actuator.halt import ActuationBlocked
from coalsense_companion.actuator.results import ActuationResult
from coalsense_companion.actuator.runtime import create_runtime
from coalsense_companion.actuator.target import Target
from coalsense_companion.bus.auth import AdapterRegistry
from coalsense_companion.bus.stop_state import RouteEvidence

from ..bus.test_core import message


class Hardware:
    def __init__(self) -> None:
        self.events: list[tuple[object, ...]] = []
        self.down: set[str] = set()
        self.buttons: set[str] = set()
        self.after: Callable[[], None] = lambda: None
        self.fail_text = False
        self.fail_release = False
        self.text_releases = 0

    def key_down(self, key: str) -> bool:
        if key in self.down:
            return False
        self.down.add(key)
        self.events.append(("key_down", key))
        self.after()
        return True

    def key_up(self, key: str) -> None:
        self.events.append(("key_up", key))
        self.down.discard(key)

    def button_down(self, button: str) -> bool:
        self.buttons.add(button)
        self.events.append(("button_down", button))
        self.after()
        return True

    def button_up(self, button: str) -> None:
        self.events.append(("button_up", button))
        self.buttons.discard(button)

    def move(self, x: float, y: float, *, absolute: bool = False) -> None:
        self.events.append(("move", x, y, absolute))

    def scroll(self, dx: float, dy: float) -> None:
        self.events.append(("scroll", dx, dy))

    def write_character(self, character: str) -> None:
        self.events.append(("text", character))
        self.after()
        if self.fail_text:
            raise RuntimeError("private application text")

    def release_text(self) -> None:
        self.text_releases += 1
        if self.fail_release:
            raise RuntimeError("private application text")


class Probe:
    def __init__(self) -> None:
        self.target = Target(1, 2, 3, True, "")
        self.calls: list[bool] = []

    def capture(self, *, pointer: bool) -> Target:
        self.calls.append(pointer)
        return self.target


def setup():
    registry = AdapterRegistry()
    session = registry.register("keyboard@1.0", "keyboard_mouse", "person")
    hardware, target = Hardware(), Probe()
    results: list[ActuationResult] = []
    runtime = create_runtime(
        registry,
        hardware,
        target,
        lambda _: None,
        results.append,
        approval_min_confidence=0.85,
        clock=lambda: 0,
    )

    route = runtime.state.register("keyboard@1.0", "keyboard_mouse")
    runtime.state.observe(route, RouteEvidence(True, False, True, True))

    def send(kind: str, payload: object = None) -> ActuationResult:
        assert runtime.bus.publish(message(kind, payload), session.credential).accepted
        runtime.bus.drain()
        return results[-1]

    return runtime, hardware, target, results, send, session.credential


def test_initially_paused_and_no_direct_or_foreign_permission() -> None:
    runtime, hardware, _, _, send, _ = setup()
    assert send("pointer.move", {"mode": "relative", "x": 1, "y": 2}).code.endswith("blocked")
    assert hardware.events == []
    with pytest.raises(ActuationBlocked):
        runtime.actuator.gate.begin(message("pointer.click", {"button": "left"}), "pointer")
    assert send("input.resume").code.endswith("resumed")
    assert not runtime.controller.paused


@pytest.mark.parametrize("reason", ["elevated", "unavailable"])
def test_uncontrollable_target_reports_reason_and_alternative_without_input(reason: str) -> None:
    _, hardware, target, _, send, _ = setup()
    send("input.resume")
    target.target = Target(1, 2, 3, False, reason)
    outcome = send("key.press", {"keys": ["Enter"]})
    assert outcome.code.endswith(reason)
    assert "ayuda humana" in outcome.message_es
    assert not outcome.partial and hardware.events == []


def test_pointer_key_and_unicode_dispatch_and_results_do_not_expose_content() -> None:
    runtime, hardware, probe, results, send, _ = setup()
    send("input.resume")
    send("pointer.move", {"mode": "absolute", "x": -4, "y": 15})
    send("pointer.scroll", {"dx": 1, "dy": -1})
    send("pointer.double_click", {"button": "right"})
    send("key.press", {"keys": ["Control", "A"]})
    outcome = send("text.insert", {"text": "privado🌿"})
    assert ("move", -4, 15, True) in hardware.events
    assert ("scroll", 1, -1) in hardware.events
    assert hardware.events.count(("button_down", "right")) == 2
    assert [
        (event[0], event[1]) for event in hardware.events if str(event[0]).startswith("key")
    ] == [
        ("key_down", "CONTROL"),
        ("key_down", "A"),
        ("key_up", "A"),
        ("key_up", "CONTROL"),
    ]
    assert hardware.events[-1] == ("text", "🌿")
    assert not hardware.down and not hardware.buttons
    assert not outcome.partial and outcome.code.endswith("done")
    assert "privado" not in repr(results)
    assert True in probe.calls and False in probe.calls
    assert send("control.undo").code == "input.undo.irreversible"
    assert not runtime.controller.paused


def test_interim_dictation_is_not_inserted() -> None:
    _, hardware, _, _, send, _ = setup()
    send("input.resume")
    assert send("text.dictation", {"text": "en curso", "final": False}).code.endswith("interim")
    assert hardware.events == []
    send("text.dictation", {"text": "listo", "final": True})
    assert len(hardware.events) == 5


def test_changed_focus_stops_text_after_first_character_without_writing_elsewhere() -> None:
    runtime, hardware, target, _, send, _ = setup()
    send("input.resume")
    hardware.after = lambda: setattr(target, "target", Target(4, 5, 6, True, ""))
    outcome = send("text.insert", {"text": "abc"})
    assert outcome.code.endswith("changed") and outcome.partial
    assert hardware.events == [("text", "a")]
    assert runtime.controller.paused and hardware.text_releases == 1
    assert send("control.undo").code.endswith("irreversible")


def test_all_key_names_are_validated_before_acquiring_any_key() -> None:
    _, hardware, _, _, send, _ = setup()
    send("input.resume")
    outcome = send("key.press", {"keys": ["Control", "not-a-key"]})
    assert outcome.code.endswith("failed") and not outcome.partial
    assert hardware.events == []


def test_key_aliases_cannot_acquire_the_same_physical_key_twice() -> None:
    _, hardware, _, _, send, _ = setup()
    send("input.resume")
    assert send("key.press", {"keys": ["Ctrl", "Control"]}).code.endswith("failed")
    assert hardware.events == []


def test_drag_state_ends_with_second_toggle_even_when_target_is_unavailable() -> None:
    runtime, hardware, probe, _, send, _ = setup()
    send("input.resume")
    assert send("pointer.drag_toggle", {"button": "left"}).code.endswith("dragging")
    assert runtime.actuator.dragging and hardware.buttons == {"left"}
    probe.target = Target(0, 0, 0, False)
    assert send("pointer.drag_toggle", {"button": "left"}).code.endswith("done")
    assert not runtime.actuator.dragging and not hardware.buttons


def test_denied_target_during_drag_releases_button_instead_of_leaving_it_held() -> None:
    runtime, hardware, probe, _, send, _ = setup()
    send("input.resume")
    send("pointer.drag_toggle", {"button": "left"})
    probe.target = Target(4, 5, 6, False, "elevated")
    outcome = send("pointer.move", {"mode": "relative", "x": 1, "y": 2})
    assert outcome.code.endswith("elevated") and not outcome.partial
    assert runtime.controller.paused and not runtime.actuator.dragging and not hardware.buttons


def test_drag_is_undoable_and_stop_clears_the_state_without_waiting_for_drain() -> None:
    runtime, hardware, _, _, send, credential = setup()
    send("input.resume")
    send("pointer.drag_toggle", {"button": "left"})
    assert send("control.undo").code == "input.undo.done"
    assert not runtime.actuator.dragging and not hardware.buttons
    send("pointer.drag_toggle", {"button": "left"})
    runtime.bus.publish(message("control.stop"), credential)
    assert not runtime.actuator.dragging and not hardware.buttons and runtime.controller.paused


def test_new_drag_cannot_be_undone_by_an_older_drag_entry() -> None:
    runtime, _, _, _, send, credential = setup()
    send("input.resume")
    send("pointer.drag_toggle", {"button": "left"})
    runtime.bus.publish(message("control.stop"), credential)
    runtime.bus.drain()
    send("input.resume")
    send("pointer.drag_toggle", {"button": "right"})
    assert send("control.undo").code == "input.undo.done"
    assert send("control.undo").code == "input.undo.unverified"


def test_failure_releases_resources_and_keeps_failed_cancellations_for_retry() -> None:
    runtime, hardware, _, results, send, _ = setup()
    send("input.resume")
    hardware.fail_text = hardware.fail_release = True
    outcome = send("text.insert", {"text": "secret"})
    assert outcome.code.endswith("halt_failed") and outcome.partial
    assert "private" not in repr(results) and "secret" not in repr(results)
    assert send("input.resume").code.endswith("blocked")
    hardware.fail_release = False
    runtime.controller.halt()
    assert send("input.resume").code.endswith("resumed")


def test_stop_interrupts_between_characters_while_consumer_is_still_running() -> None:
    runtime, hardware, _, _, send, credential = setup()
    send("input.resume")
    entered, release = threading.Event(), threading.Event()

    def wait() -> None:
        entered.set()
        assert release.wait(3)

    hardware.after = wait
    worker = threading.Thread(target=lambda: send("text.insert", {"text": "abc"}))
    worker.start()
    assert entered.wait(3)
    stop = threading.Thread(target=lambda: runtime.bus.publish(message("control.stop"), credential))
    stop.start()
    assert runtime.controller.wait_until_paused(3)
    release.set()
    worker.join(3)
    stop.join(3)
    assert not worker.is_alive() and not stop.is_alive()
    assert hardware.events == [("text", "a")]
    assert runtime.controller.paused


def test_feedback_failure_does_not_repeat_input_and_close_unsubscribes() -> None:
    runtime, hardware, _, _, send, _ = setup()
    send("input.resume")

    def fail(_: ActuationResult) -> None:
        raise RuntimeError("unavailable")

    runtime.actuator.feedback = fail
    send("pointer.click", {"button": "left"})
    assert runtime.actuator.feedback_failures == 1
    assert len(hardware.events) == 2
    runtime.actuator.close()
    send("pointer.click", {"button": "left"})
    assert len(hardware.events) == 2 and runtime.controller.paused


def test_system_adapter_can_stop_but_cannot_resume_or_inject_inputs() -> None:
    registry = AdapterRegistry()
    system = registry.register("supervisor@1.0", "keyboard_mouse", "system")
    person = registry.register("keyboard@1.0", "keyboard_mouse", "person")
    hardware, outcomes = Hardware(), []
    runtime = create_runtime(
        registry,
        hardware,
        Probe(),
        lambda _: None,
        outcomes.append,
        approval_min_confidence=0.85,
        clock=lambda: 0,
    )
    route = runtime.state.register("keyboard@1.0", "keyboard_mouse")
    runtime.state.observe(route, RouteEvidence(True, False, True, True))
    runtime.bus.publish(message("input.resume"), person.credential)
    runtime.bus.publish(message("key.press", {"keys": ["Enter"]}), system.credential)
    runtime.bus.publish(message("control.undo"), system.credential)
    runtime.bus.drain()
    assert hardware.events == []
    assert [outcome.code for outcome in outcomes[-2:]] == [
        "input.actuation.resumed",
        "input.actuation.blocked",
    ]
    assert runtime.bus.publish(message("control.stop"), system.credential).accepted
    assert runtime.controller.paused
    runtime.bus.publish(message("input.resume"), system.credential)
    runtime.bus.drain()
    assert outcomes[-1].code.endswith("blocked") and runtime.controller.paused


def test_focus_change_mid_chord_releases_owned_modifiers_and_preserves_external_keys() -> None:
    runtime, hardware, probe, _, send, _ = setup()
    send("input.resume")
    hardware.down.add("SHIFT")
    hardware.after = lambda: setattr(probe, "target", Target(4, 5, 6, True, ""))
    outcome = send("key.press", {"keys": ["Shift", "Control", "A"]})
    assert outcome.code.endswith("changed") and outcome.partial
    assert hardware.events == [("key_down", "CONTROL"), ("key_up", "CONTROL")]
    assert hardware.down == {"SHIFT"} and runtime.controller.paused


def test_second_click_rechecks_target_and_does_not_click_new_popup() -> None:
    runtime, hardware, probe, _, send, _ = setup()
    send("input.resume")
    hardware.after = lambda: setattr(probe, "target", Target(4, 5, 6, True, ""))
    outcome = send("pointer.double_click", {"button": "left"})
    assert outcome.code.endswith("changed") and outcome.partial
    assert hardware.events == [("button_down", "left"), ("button_up", "left")]
    assert not hardware.buttons and runtime.controller.paused


def test_ill_formed_unicode_is_rejected_before_any_character_is_inserted() -> None:
    _, hardware, _, _, send, _ = setup()
    send("input.resume")
    outcome = send("text.insert", {"text": "a\ud800"})
    assert outcome.code.endswith("failed") and not outcome.partial
    assert hardware.events == []
