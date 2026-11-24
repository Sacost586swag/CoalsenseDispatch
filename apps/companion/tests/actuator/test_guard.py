"""Permisos del bus y generaciones: una cola anterior a Alto no se reactiva."""

import pytest
from coalsense_companion.actuator.guard import ActuationGate
from coalsense_companion.actuator.halt import ActuationBlocked, HaltController
from coalsense_companion.bus.core import BusDelivery
from coalsense_companion.bus.stop_guard import StopGuard

from ..bus.test_core import message, setup_bus
from ..bus.test_stop_guard import Hardware


def test_only_deliveries_from_the_bound_bus_can_start_actuation() -> None:
    bus, _, credential, _, _ = setup_bus()
    controller = HaltController(Hardware())
    controller.resume()
    gate = ActuationGate(bus, controller)
    requests: list[BusDelivery] = []
    bus.subscribe_bound(["nav.next"], requests.append)
    bus.publish(message("nav.next"), credential)
    bus.drain()
    lease = gate.begin(requests[0], "pointer")
    gate.finish(lease)
    with pytest.raises(ActuationBlocked):
        gate.begin(requests[0], "pointer")
    with pytest.raises(ActuationBlocked):
        gate.begin(message("nav.next"), "pointer")
    other, _, other_credential, _, _ = setup_bus()
    other_requests: list[BusDelivery] = []
    other.subscribe_bound(["nav.next"], other_requests.append)
    other.publish(message("nav.next"), other_credential)
    other.drain()
    with pytest.raises(ActuationBlocked):
        gate.begin(other_requests[0], "pointer")


def test_old_queued_requests_cannot_run_even_after_explicit_resume() -> None:
    bus, _, credential, _, _ = setup_bus()
    controller = HaltController(Hardware())
    controller.resume()
    bus.on_stop = StopGuard(controller).halt
    gate = ActuationGate(bus, controller)
    requests: list[BusDelivery] = []
    bus.subscribe_bound(["nav.next"], requests.append)
    bus.publish(message("nav.next"), credential)
    bus.publish(message("control.stop"), credential)
    controller.resume()
    bus.publish(message("nav.next"), credential)
    bus.drain()
    assert len(requests) == 2
    with pytest.raises(ActuationBlocked):
        gate.begin(requests[0], "pointer")
    gate.finish(gate.begin(requests[1], "pointer"))


def test_copies_for_plain_consumers_do_not_change_bound_delivery_contents() -> None:
    bus, _, credential, _, _ = setup_bus()
    bus.subscribe(["text.insert"], lambda item: item["payload"].update(text="changed"))
    requests: list[BusDelivery] = []
    bus.subscribe_bound(["text.insert"], requests.append)
    bus.publish(message("text.insert", {"text": "original"}), credential)
    bus.drain()
    assert requests[0].intent["payload"] == {"text": "original"}


def test_each_step_rechecks_generation_and_resume_needs_its_own_intention() -> None:
    bus, _, credential, _, _ = setup_bus()
    controller = HaltController(Hardware())
    controller.resume()
    bus.on_stop = StopGuard(controller).halt
    gate = ActuationGate(bus, controller)
    requests: list[BusDelivery] = []
    bus.subscribe_bound(["nav.next", "input.resume"], requests.append)
    bus.publish(message("nav.next"), credential)
    bus.drain()
    with pytest.raises(ActuationBlocked):
        gate.resume(requests[0])
    ticket = gate.begin(requests[0], "pointer")
    bus.publish(message("control.stop"), credential)
    bus.publish(message("input.resume"), credential)
    bus.drain()
    gate.resume(requests[-1])
    with pytest.raises(ActuationBlocked):
        gate.step(ticket, lambda: pytest.fail("Old action revived"))


def test_movement_cannot_coalesce_across_a_stop_generation() -> None:
    bus, _, credential, _, _ = setup_bus(1)
    bus.publish(message("pointer.move", {"mode": "relative", "x": 10, "y": 0}), credential)
    bus.publish(message("control.stop"), credential)
    result = bus.publish(message("pointer.move", {"mode": "relative", "x": 1, "y": 0}), credential)
    assert result.status == "dropped_continuous"
    moves = [intent for intent in bus.drain() if intent["type"] == "pointer.move"]
    assert len(moves) == 1 and moves[0]["payload"]["x"] == 10


def test_undo_after_stop_does_not_resume_ordinary_actions_and_a_new_stop_interrupts_it() -> None:
    bus, _, credential, _, _ = setup_bus()
    controller = HaltController(Hardware())
    bus.on_stop = StopGuard(controller).halt
    gate = ActuationGate(bus, controller)
    requests: list[BusDelivery] = []
    bus.subscribe_bound(["control.undo", "nav.next"], requests.append)
    bus.publish(message("control.stop"), credential)
    bus.publish(message("control.undo"), credential)
    bus.publish(message("nav.next"), credential)
    bus.drain()
    ticket = gate.begin(requests[0], "undo")
    changes: list[int] = []
    gate.step(ticket, lambda: changes.append(1))
    assert controller.paused
    with pytest.raises(ActuationBlocked):
        gate.begin(requests[1], "pointer")
    bus.publish(message("control.stop"), credential)
    with pytest.raises(ActuationBlocked):
        gate.step(ticket, lambda: changes.append(2))
    assert changes == [1]
