"""T-01-009: detención síncrona, liberación de recursos y carreras de reanudación."""

import threading

import pytest
from coalsense_companion.actuator.halt import ActuationBlocked, HaltController, HaltFailure
from coalsense_companion.bus.auth import AdapterRegistry
from coalsense_companion.bus.core import IntentBus
from coalsense_companion.bus.stop_guard import StopGuard
from hypothesis import given, settings
from hypothesis import strategies as st

from .test_core import message


class Hardware:
    def __init__(self) -> None:
        self.keys: set[str] = set()
        self.buttons: set[str] = set()
        self.fail_keys: set[str] = set()

    def key_down(self, key: str) -> bool:
        if key in self.keys:
            return False
        self.keys.add(key)
        return True

    def key_up(self, key: str) -> None:
        if key in self.fail_keys:
            raise OSError("private hardware details")
        self.keys.discard(key)

    def button_down(self, button: str) -> bool:
        if button in self.buttons:
            return False
        self.buttons.add(button)
        return True

    def button_up(self, button: str) -> None:
        self.buttons.discard(button)


@settings(deadline=None)
@given(
    mode=st.sampled_from(
        ["command", "dictation", "sleep", "tracking_paused", "scan", "calibration"]
    ),
    modality=st.sampled_from(["voice", "head_gesture", "keyboard_mouse", "gaze", "switch_scan"]),
    keys=st.sets(st.sampled_from(["Control", "Shift", "A"])),
    buttons=st.sets(st.sampled_from(["left", "right", "middle"])),
    online=st.booleans(),
)
def test_stop_releases_every_owned_resource_in_all_logical_modes(
    mode: str,
    modality: str,
    keys: set[str],
    buttons: set[str],
    online: bool,
) -> None:
    hardware = Hardware()
    controller = HaltController(hardware)
    controller.resume()
    activities = {kind: True for kind in ["pointer", "text", "dictation", "scan", "calibration"]}
    for kind in activities:
        controller.begin(kind, cancel=lambda kind=kind: activities.__setitem__(kind, False))
    lease = controller.begin("keys")
    for key in keys:
        controller.key_down(lease, key)
    for button in buttons:
        controller.button_down(lease, button)
    registry = AdapterRegistry()
    adapter = registry.register("fixture@1", modality, "person")  # type: ignore[arg-type]
    # El modo y la conectividad no participan en el camino local de Alto.
    state = {"mode": mode, "online": online}
    guard = StopGuard(controller)
    bus = IntentBus(registry, lambda _: None, on_stop=guard.halt, approval_min_confidence=0.85)
    assert bus.publish(message("control.stop"), adapter.credential).accepted
    assert controller.paused and not hardware.keys and not hardware.buttons
    assert not any(activities.values()) and controller.active_count == 0
    assert guard.last_report is not None and guard.last_report.safe
    assert state == {"mode": mode, "online": online}
    with pytest.raises(ActuationBlocked):
        controller.step(lease, lambda: pytest.fail("Actuation after Alto"))


def test_resume_never_revives_a_lease_captured_before_stop() -> None:
    controller = HaltController(Hardware())
    with pytest.raises(ActuationBlocked):
        controller.begin("text")  # arranque cerrado hasta reanudar explícitamente
    controller.resume()
    old = controller.begin("text")
    controller.halt()
    controller.resume()
    with pytest.raises(ActuationBlocked):
        controller.step(old, lambda: pytest.fail("Old lease revived"))
    new = controller.begin("text")
    changes: list[str] = []
    controller.step(new, lambda: changes.append("new"))
    controller.finish(new)
    assert changes == ["new"] and controller.active_count == 0


def test_all_resources_are_attempted_on_failure_and_resume_waits_for_recovery() -> None:
    hardware = Hardware()
    controller = HaltController(hardware)
    controller.resume()
    lease = controller.begin("keys")
    controller.key_down(lease, "Control")
    controller.key_down(lease, "Shift")
    controller.button_down(lease, "left")
    hardware.fail_keys.add("Control")
    with pytest.raises(HaltFailure) as caught:
        controller.halt()
    assert controller.paused and hardware.keys == {"Control"} and not hardware.buttons
    assert caught.value.report.keys_remaining == 1
    assert "private hardware details" not in repr(caught.value)
    with pytest.raises(ActuationBlocked):
        controller.resume()
    hardware.fail_keys.clear()
    assert controller.halt().safe
    controller.resume()


def test_stop_does_not_release_keys_already_held_outside_the_companion() -> None:
    hardware = Hardware()
    hardware.keys.add("Control")
    controller = HaltController(hardware)
    controller.resume()
    lease = controller.begin("keys")
    controller.key_down(lease, "Control")
    controller.key_down(lease, "A")
    controller.halt()
    assert hardware.keys == {"Control"}


def test_failed_activity_cancellation_is_retried_without_exposing_its_exception() -> None:
    controller = HaltController(Hardware())
    controller.resume()
    attempts = []

    def cancel() -> None:
        attempts.append(1)
        if len(attempts) == 1:
            raise OSError("private activity content")

    controller.begin("dictation", cancel=cancel)
    guard = StopGuard(controller)
    with pytest.raises(HaltFailure):
        guard.halt()
    assert guard.last_report is not None and not guard.last_report.safe
    with pytest.raises(ActuationBlocked):
        controller.resume()
    guard.halt()
    assert guard.last_report is not None and guard.last_report.safe and len(attempts) == 2


def test_an_in_flight_step_cannot_schedule_another_step_after_stop() -> None:
    controller = HaltController(Hardware())
    controller.resume()
    lease = controller.begin("text")
    entered, release = threading.Event(), threading.Event()
    changes: list[str] = []

    def operation() -> None:
        entered.set()
        assert release.wait(3)
        changes.append("in-flight")

    worker = threading.Thread(target=lambda: controller.step(lease, operation))
    worker.start()
    assert entered.wait(3)
    stopped = threading.Thread(target=controller.halt)
    stopped.start()
    try:
        assert controller.wait_until_paused(3)
        with pytest.raises(ActuationBlocked):
            controller.begin("text")
    finally:
        release.set()
        worker.join(3)
        stopped.join(3)
    assert not worker.is_alive() and not stopped.is_alive()
    with pytest.raises(ActuationBlocked):
        controller.step(lease, lambda: changes.append("stale"))
    assert changes == ["in-flight"]
