"""Salud de Alto: evidencia verificada, caducidad y pérdida de la última ruta."""

import pytest
from coalsense_companion.bus.stop_state import RouteEvidence, StopState
from hypothesis import given
from hypothesis import strategies as st


class Clock:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now


def healthy() -> RouteEvidence:
    return RouteEvidence(True, True, True, True)


def test_startup_is_false_and_registration_is_not_proof_of_health() -> None:
    clock = Clock()
    changes, losses = [], []
    state = StopState(on_unreachable=losses.append, on_change=changes.append, clock=clock)
    assert not state.snapshot().stop_reachable
    route = state.register("voice@1", "voice")
    assert not state.snapshot().stop_reachable
    assert state.snapshot().routes[0].reason == "starting"
    state.observe(route, healthy())
    assert state.snapshot().stop_reachable and not losses
    assert changes[-1].stop_reachable


@given(st.booleans(), st.booleans(), st.booleans(), st.booleans())
def test_model_route_requires_every_health_fact(
    device: bool, model: bool, adapter: bool, stop: bool
) -> None:
    state = StopState(on_unreachable=lambda _: None)
    route = state.register("vision@1", "head_gesture")
    state.observe(route, RouteEvidence(device, model, adapter, stop))
    assert state.snapshot().stop_reachable == (device and model and adapter and stop)


def test_keyboard_route_does_not_need_a_model_but_still_needs_a_live_stop_binding() -> None:
    state = StopState(on_unreachable=lambda _: None)
    route = state.register("keyboard@1", "keyboard_mouse")
    state.observe(route, RouteEvidence(True, False, True, False))
    assert not state.snapshot().stop_reachable
    state.observe(route, RouteEvidence(True, False, True, True))
    assert state.snapshot().stop_reachable


def test_last_route_loss_notifies_before_return_and_does_not_depend_on_ui_success() -> None:
    order: list[str] = []

    def failed_ui(_) -> None:
        order.append("ui")
        raise RuntimeError("private device name")

    state = StopState(on_unreachable=lambda _: order.append("halt"), on_change=failed_ui)
    first = state.register("voice@1", "voice")
    second = state.register("keyboard@1", "keyboard_mouse")
    state.observe(first, healthy())
    state.observe(second, healthy())
    order.clear()
    state.fail(first, "adapter_unresponsive")
    assert state.snapshot().stop_reachable and "halt" not in order
    state.fail(second, "device_unavailable")
    assert order[-2:] == ["halt", "ui"]
    assert not state.snapshot().stop_reachable and state.notification_failures > 0


def test_expiry_at_deadline_is_fail_closed_even_without_a_new_adapter_report() -> None:
    clock = Clock()
    losses = []
    state = StopState(on_unreachable=losses.append, clock=clock, max_age_ns=100)
    route = state.register("voice@1", "voice")
    state.observe(route, healthy())
    clock.now = 99
    assert state.snapshot().stop_reachable
    clock.now = 100
    assert not state.snapshot().stop_reachable
    assert state.snapshot().routes[0].reason == "stale" and len(losses) == 1
    state.observe(route, healthy())
    assert state.snapshot().stop_reachable


def test_restart_changes_token_and_delayed_report_cannot_revive_old_process() -> None:
    state = StopState(on_unreachable=lambda _: None)
    first = state.register("vision@1", "head_gesture")
    state.observe(first, healthy())
    second = state.renew(first)
    assert not state.snapshot().stop_reachable
    with pytest.raises(ValueError, match="Unknown route"):
        state.observe(first, healthy())
    state.observe(second, healthy())
    assert state.snapshot().stop_reachable


def test_health_keeps_original_receipt_time_instead_of_refreshing_an_old_report() -> None:
    clock = Clock()
    state = StopState(on_unreachable=lambda _: None, clock=clock, max_age_ns=100)
    route = state.register("voice@1", "voice")
    clock.now = 150
    state.observe(route, healthy(), observed_ns=50)
    assert not state.snapshot().stop_reachable and state.snapshot().routes[0].reason == "stale"
    with pytest.raises(ValueError):
        state.observe(route, healthy(), observed_ns=151)
    assert not state.snapshot().stop_reachable


def test_invalid_evidence_is_not_truthy_or_serialized_into_feedback() -> None:
    with pytest.raises(ValueError):
        RouteEvidence("camera name", True, True, True)
    state = StopState(on_unreachable=lambda _: None)
    route = state.register("voice@1", "voice")
    state.observe(route, healthy())
    with pytest.raises(ValueError):
        state.observe(route, {"device_streaming": True})
    assert not state.snapshot().stop_reachable


def test_foreign_tokens_and_duplicates_are_rejected_and_remove_last_route_is_a_loss() -> None:
    losses = []
    state = StopState(on_unreachable=losses.append)
    other = StopState(on_unreachable=lambda _: None)
    route = state.register("voice@1", "voice")
    foreign = other.register("voice@1", "voice")
    with pytest.raises(ValueError):
        state.register("voice@1", "voice")
    with pytest.raises(ValueError):
        state.observe(foreign, healthy())
    state.observe(route, healthy())
    state.remove(route)
    assert not state.snapshot().stop_reachable and len(losses) == 1


def test_loss_callback_failure_is_observable_and_does_not_leave_true_state() -> None:
    def fail(_) -> None:
        raise RuntimeError("device details")

    state = StopState(on_unreachable=fail)
    route = state.register("voice@1", "voice")
    state.observe(route, healthy())
    state.fail(route, "stopped")
    assert not state.snapshot().stop_reachable and state.halt_failures == 1


@pytest.mark.parametrize("age", [0, -1, True, 1.5])
def test_invalid_deadline_is_rejected(age: object) -> None:
    with pytest.raises(ValueError):
        StopState(on_unreachable=lambda _: None, max_age_ns=age)
