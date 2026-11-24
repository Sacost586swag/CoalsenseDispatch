import pytest
from coalsense_companion.bus.approval_guard import ApprovalGuard
from hypothesis import given
from hypothesis import strategies as st

from .test_core import message, setup_bus


@pytest.mark.parametrize("threshold", [-1, 1.1, True, float("nan"), float("inf"), -float("inf")])
def test_invalid_thresholds_cannot_disable_the_guard(threshold: float) -> None:
    with pytest.raises(ValueError):
        ApprovalGuard(threshold)


def test_threshold_boundary_and_rejection_do_not_make_rejecting_harder() -> None:
    bus, _, credential, _, _ = setup_bus()
    assert bus.publish(message("approval.approve") | {"confidence": 0.85}, credential).accepted
    assert bus.publish(message("approval.reject") | {"confidence": 0}, credential).accepted
    assert [item["type"] for item in bus.drain()] == ["approval.approve", "approval.reject"]


def test_uncertainty_produces_feedback_and_failed_feedback_never_approves() -> None:
    bus, _, credential, _, _ = setup_bus()
    seen = []
    bus.on_approval_feedback = seen.append
    assert not bus.publish(message("approval.approve") | {"confidence": 0.1}, credential).accepted
    assert seen[0].code == "approval.uncertain"

    def failed(_: object) -> None:
        raise OSError("private details")

    bus.on_approval_feedback = failed
    assert not bus.publish(message("approval.approve") | {"confidence": 0.1}, credential).accepted
    assert bus.feedback_failures == 1 and bus.drain() == []


@given(st.floats(min_value=0, max_value=0.849999, allow_nan=False, allow_infinity=False))
def test_uncertain_approval_never_reaches_a_consumer(confidence: float) -> None:
    bus, _, credential, _, _ = setup_bus()
    assert not bus.publish(
        message("approval.approve") | {"confidence": confidence}, credential
    ).accepted
    assert bus.drain() == []
    assert bus.publish(message("approval.reject") | {"confidence": 0}, credential).accepted
