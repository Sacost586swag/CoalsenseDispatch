"""La composición real exige salud y pierde autorizaciones al caer la última ruta."""

from coalsense_companion.actuator.runtime import create_runtime
from coalsense_companion.bus.auth import AdapterRegistry

from ..bus.test_core import message
from ..bus.test_stop_state import Clock, healthy
from .test_actuator import Hardware, Probe


def setup():
    clock, hardware = Clock(), Hardware()
    registry = AdapterRegistry()
    adapter = registry.register("keyboard@1", "keyboard_mouse", "person")
    outcomes, health_changes = [], []
    runtime = create_runtime(
        registry,
        hardware,
        Probe(),
        lambda _: None,
        outcomes.append,
        approval_min_confidence=0.85,
        clock=clock,
        on_health=health_changes.append,
    )

    def send(kind: str, payload: object = None):
        assert runtime.bus.publish(message(kind, payload), adapter.credential).accepted
        runtime.bus.drain()
        return outcomes[-1]

    return runtime, hardware, clock, adapter.credential, outcomes, health_changes, send


def test_no_resume_at_startup_until_a_stop_route_is_verified() -> None:
    runtime, hardware, _, _, _, _, send = setup()
    assert send("input.resume").code.endswith("blocked") and runtime.controller.paused
    route = runtime.state.register("keyboard@1", "keyboard_mouse")
    assert send("input.resume").code.endswith("blocked")
    runtime.state.observe(route, healthy())
    assert runtime.controller.paused  # recuperarse no es una decisión de reanudar
    assert send("input.resume").code.endswith("resumed")
    assert send("pointer.click", {"button": "left"}).code.endswith("done")
    assert len(hardware.events) == 2


def test_loss_stops_drag_synchronously_and_recovery_requires_explicit_resume() -> None:
    runtime, hardware, _, _, _, changes, send = setup()
    route = runtime.state.register("keyboard@1", "keyboard_mouse")
    runtime.state.observe(route, healthy())
    send("input.resume")
    send("pointer.drag_toggle", {"button": "left"})
    runtime.state.fail(route, "device_unavailable")
    assert runtime.controller.paused and not runtime.actuator.dragging and not hardware.buttons
    assert changes[-1].stop_reachable is False
    runtime.state.observe(route, healthy())
    assert send("pointer.click", {"button": "left"}).code.endswith("blocked")
    assert send("input.resume").code.endswith("resumed")


def test_health_loss_invalidates_queued_actions_even_after_recovery_and_resume() -> None:
    runtime, hardware, _, credential, outcomes, _, send = setup()
    route = runtime.state.register("keyboard@1", "keyboard_mouse")
    runtime.state.observe(route, healthy())
    send("input.resume")
    runtime.bus.publish(message("pointer.click", {"button": "left"}), credential)
    runtime.state.fail(route, "adapter_unresponsive")
    runtime.state.observe(route, healthy())
    # Reanudar primero desde otra entrega vigente no debe resucitar la cola vieja.
    runtime.controller.resume()
    runtime.bus.drain()
    assert outcomes[-1].code.endswith("blocked") and not hardware.events
    assert send("pointer.click", {"button": "left"}).code.endswith("done")


def test_health_expires_between_characters_without_fresh_reports_or_network() -> None:
    runtime, hardware, clock, _, _, _, send = setup()
    route = runtime.state.register("keyboard@1", "keyboard_mouse")
    runtime.state.observe(route, healthy())
    send("input.resume")
    hardware.after = lambda: setattr(clock, "now", runtime.state.max_age_ns)
    outcome = send("text.insert", {"text": "abc"})
    assert outcome.code.endswith("blocked") and outcome.partial
    assert hardware.events == [("text", "a")]
    assert runtime.controller.paused and not runtime.state.snapshot().stop_reachable


def test_another_healthy_modality_preserves_stop_availability_when_one_dies() -> None:
    runtime, hardware, _, _, _, _, send = setup()
    first = runtime.state.register("vision@1", "head_gesture")
    second = runtime.state.register("keyboard@1", "keyboard_mouse")
    runtime.state.observe(first, healthy())
    runtime.state.observe(second, healthy())
    send("input.resume")
    runtime.state.fail(first, "adapter_unresponsive")
    assert runtime.state.snapshot().stop_reachable and not runtime.controller.paused
    assert send("pointer.click", {"button": "left"}).code.endswith("done")
    assert len(hardware.events) == 2


def test_undo_remains_available_without_a_healthy_route_while_ordinary_actions_stay_paused() -> (
    None
):
    runtime, hardware, _, _, _, _, send = setup()
    assert send("control.undo").code == "input.undo.empty"
    assert runtime.controller.paused and not hardware.events
