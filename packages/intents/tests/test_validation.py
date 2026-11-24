import json
import traceback
from pathlib import Path

import pytest
from coalsense_intents import (
    ContractError,
    intent_types,
    priority_for,
    validate_intent,
    validate_profile,
)
from hypothesis import given
from hypothesis import strategies as st

from .test_schema import intention, profile

PAYLOADS: dict[str, object] = {
    "control.stop": {},
    "control.undo": {},
    "help.request_human": {},
    "approval.approve": {},
    "approval.reject": {},
    "pointer.move": {"mode": "relative", "x": 1, "y": -2},
    "pointer.click": {"button": "left"},
    "pointer.double_click": {"button": "left"},
    "pointer.drag_toggle": {"button": "left"},
    "pointer.scroll": {"dx": 0, "dy": -1},
    "key.press": {"keys": ["Control", "Enter"]},
    "text.insert": {"text": "Notas"},
    "text.dictation": {"text": "Notas", "final": True},
    "nav.next": {},
    "nav.previous": {},
    "nav.select": {},
    "nav.back": {},
    "ui.show_numbers": {},
    "ui.show_grid": {},
    "ui.select_target": {"by": "number", "value": "3"},
    "mode.set": {"mode": "dictation"},
    "input.pause": {},
    "input.resume": {},
    "profile.switch": {"profile_id": "en-cama"},
    "calibration.request": {"modality": "voice"},
    "command.invoke": {"name": "custom", "parameters": {"count": 3, "enabled": True}},
}


@pytest.mark.parametrize("kind", PAYLOADS)
def test_every_catalogued_intention_validates_in_the_packaged_validator(kind: str) -> None:
    value = intention(kind, PAYLOADS[kind])
    if kind.startswith("approval."):
        value.update(pending_action_id=value["id"], content_digest="a" * 64)
    assert validate_intent(value)["type"] == kind
    assert priority_for(kind) == value["priority"]


def test_generated_catalog_covers_exactly_the_contract_and_embedded_schemas_match() -> None:
    assert intent_types() == set(PAYLOADS)
    from coalsense_intents._schemas import INTENT_SCHEMA, PROFILE_SCHEMA

    root = Path(__file__).parents[1] / "schema"
    assert INTENT_SCHEMA == json.loads((root / "intent.schema.json").read_text("utf-8"))
    assert PROFILE_SCHEMA == json.loads(
        (root / "capability-profile.schema.json").read_text("utf-8")
    )


def test_validation_copies_inputs_and_never_echoes_private_values() -> None:
    raw = intention("text.dictation", {"text": "contenido-privado", "final": True})
    validated = validate_intent(raw)
    raw["payload"] = {"text": "changed", "final": True}
    assert validated["type"] == "text.dictation"
    assert validated["payload"]["text"] == "contenido-privado"
    private_text = "-".join(["contenido", "privado"])
    invalid = raw | {"profile": private_text}
    with pytest.raises(ContractError) as caught:
        validate_intent(invalid)
    assert private_text not in "".join(traceback.format_exception(caught.value))
    assert validate_profile(profile())["schema_version"] == 1


@given(st.one_of(st.none(), st.booleans(), st.text(), st.lists(st.integers())))
def test_non_object_intentions_are_always_rejected(value: object) -> None:
    with pytest.raises(ContractError):
        validate_intent(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_non_json_numbers_fail_closed(value: float) -> None:
    with pytest.raises(ContractError):
        validate_intent(intention() | {"confidence": value})
