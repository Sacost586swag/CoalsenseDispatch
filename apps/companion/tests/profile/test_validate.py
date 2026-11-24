import copy

import pytest
from coalsense_common import AppError
from coalsense_companion.profile.validate import validate_for_activation


def profile() -> dict[str, object]:
    return {
        "schema_version": 1,
        "profile_id": "en-cama",
        "label": "En cama",
        "language": "es-EC",
        "modalities": {"voice": {"enabled": True}},
        "bindings": [
            {"modality": "voice", "trigger": {"phrase": phrase}, "intent": kind}
            for phrase, kind in [
                ("alto", "control.stop"),
                ("deshacer", "control.undo"),
                ("ayuda", "help.request_human"),
            ]
        ],
        "approval_min_confidence": 0.85,
        "min_target_px": 44,
        "feedback": {"visual": True, "audio": True},
    }


@pytest.mark.parametrize("kind", ["control.stop", "control.undo", "help.request_human"])
def test_safety_routes_can_change_but_cannot_be_removed(kind: str) -> None:
    previous = profile()
    valid = validate_for_activation(previous)
    edited = copy.deepcopy(valid)
    for binding in edited["bindings"]:
        if binding["intent"] == kind:
            binding["trigger"] = {"phrase": "otra frase"}
    assert validate_for_activation(edited)["bindings"] == edited["bindings"]
    edited["bindings"] = [binding for binding in edited["bindings"] if binding["intent"] != kind]
    with pytest.raises(AppError):
        validate_for_activation(edited)
    assert validate_for_activation(previous) == valid  # la propuesta fallida no toca el anterior


def test_new_enabled_modality_needs_its_own_routes() -> None:
    value = validate_for_activation(profile())
    value["modalities"]["head_gesture"] = {"enabled": True}
    with pytest.raises(AppError):
        validate_for_activation(value)
    value["bindings"].extend(
        [
            {"modality": "head_gesture", "trigger": {"gesture": gesture}, "intent": kind}
            for gesture, kind in [
                ("mouth_open", "control.stop"),
                ("jaw_left", "control.undo"),
                ("jaw_right", "help.request_human"),
            ]
        ]
    )
    assert validate_for_activation(value)["modalities"]["head_gesture"]["enabled"]
    value["modalities"]["head_gesture"]["gestures"] = {
        "mouth_open": {"on": 0.2, "off": 0.3, "hold_ms": 0, "cooldown_ms": 0},
    }
    with pytest.raises(AppError):
        validate_for_activation(value)  # histéresis inválida


def test_declared_condition_needs_a_confirmed_consent_not_only_a_reference() -> None:
    value = profile() | {
        "declared_condition": {
            "text": "dato privado",
            "consent_ref": "consent-1",
            "category": "special",
        }
    }
    for check in (None, lambda _: False):
        with pytest.raises(AppError) as caught:
            validate_for_activation(value, has_consent=check)
        assert "dato privado" not in str(caught.value)
    assert validate_for_activation(value, has_consent=lambda ref: ref == "consent-1")

    def broken(_: str) -> bool:
        raise OSError("dato privado")

    with pytest.raises(AppError):
        validate_for_activation(value, has_consent=broken)


def test_approval_dwell_inherits_general_time_and_cannot_be_shorter() -> None:
    value = validate_for_activation(profile())
    value["modalities"]["gaze"] = {"enabled": True, "dwell_ms": 1000}
    value["bindings"].extend(
        [
            {"modality": "gaze", "trigger": {"target_id": target, "dwell_ms": 1000}, "intent": kind}
            for target, kind in [
                ("cs-stop", "control.stop"),
                ("cs-undo", "control.undo"),
                ("cs-help", "help.request_human"),
            ]
        ]
    )
    assert validate_for_activation(value)
    value["modalities"]["gaze"]["approval_dwell_ms"] = 500
    with pytest.raises(AppError):
        validate_for_activation(value)


@pytest.mark.parametrize(
    "change",
    [
        {"min_target_px": 43},
        {"schema_version": 2},
        {"diagnosis": "private"},
        {"feedback": {"visual": False, "audio": False}},
    ],
)
def test_invalid_profile_uses_common_recoverable_error_without_content(
    change: dict[str, object],
) -> None:
    with pytest.raises(AppError) as caught:
        validate_for_activation(profile() | change)
    assert caught.value.code == "input.profile.invalid"
    assert caught.value.recoverable and caught.value.next_actions
    assert "private" not in repr(caught.value.to_dict())
