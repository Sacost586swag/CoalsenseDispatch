"""Invariantes del perfil y verificación de consentimiento (REQ-01-016, 017, 083, 084)."""

from collections.abc import Callable

from coalsense_common import AppError
from coalsense_common.i18n_es import es
from coalsense_intents import ContractError, validate_profile

from .model import CapabilityProfile


def invalid_profile() -> AppError:
    return AppError(
        "input.profile.invalid",
        es["input.profile.invalid.message"],
        True,
        [es["input.profile.retry.message"]],
    )


def validate_for_activation(
    value: object,
    *,
    has_consent: Callable[[str], bool] | None = None,
) -> CapabilityProfile:
    try:
        profile = validate_profile(value)
    except ContractError:
        raise invalid_profile() from None
    head = profile["modalities"].get("head_gesture")
    if head:
        for gesture in head.get("gestures", {}).values():
            if gesture["off"] >= gesture["on"]:
                raise invalid_profile()
    gaze = profile["modalities"].get("gaze")
    if gaze and gaze.get("approval_dwell_ms", gaze.get("dwell_ms", 0)) < gaze.get("dwell_ms", 0):
        raise invalid_profile()
    condition = profile.get("declared_condition")
    if condition is not None:
        try:
            consented = has_consent is not None and has_consent(condition["consent_ref"])
        except Exception:
            consented = False
        if not consented:
            raise invalid_profile()
    return profile
