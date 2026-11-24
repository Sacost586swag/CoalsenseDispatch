"""Contratos independientes de los modelos generados (REQ-01-001, 003, 010, 083)."""

import copy
import json
from pathlib import Path

import pytest
from coalsense_common import new_id
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[1]
INTENT_SCHEMA = json.loads((ROOT / "schema/intent.schema.json").read_text("utf-8"))
PROFILE_SCHEMA = json.loads((ROOT / "schema/capability-profile.schema.json").read_text("utf-8"))
INTENT = Draft202012Validator(INTENT_SCHEMA, format_checker=FormatChecker())
PROFILE = Draft202012Validator(PROFILE_SCHEMA, format_checker=FormatChecker())


def intention(kind: str = "pointer.click", payload: object = None) -> dict[str, object]:
    return {
        "id": new_id(),
        "type": kind,
        "modality": "voice",
        "adapter": "voice@1.0.0",
        "actor_origin": "person",
        "monotonic_ts": 123_000_000,
        "wall_ts": "2026-11-16T10:00:00.000Z",
        "confidence": 0.95,
        "priority": "preemptive"
        if kind in {"control.stop", "control.undo", "help.request_human"}
        else "normal",
        "payload": {"button": "left"} if payload is None else payload,
    }


def profile() -> dict[str, object]:
    return {
        "schema_version": 1,
        "profile_id": "en-cama",
        "label": "En cama",
        "language": "es-EC",
        "modalities": {"voice": {"enabled": True}, "keyboard_mouse": {"enabled": False}},
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


def test_schemas_are_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(INTENT_SCHEMA)
    Draft202012Validator.check_schema(PROFILE_SCHEMA)


def test_same_command_from_two_modalities_has_the_same_payload() -> None:
    voice = intention()
    gesture = voice | {"modality": "head_gesture", "adapter": "vision@1.0.0", "confidence": 0.9}
    assert INTENT.is_valid(voice) and INTENT.is_valid(gesture)
    assert {key for key in voice if voice[key] != gesture[key]} == {
        "modality",
        "adapter",
        "confidence",
    }


@pytest.mark.parametrize("kind", ["approval.approve", "approval.reject"])
def test_approval_requires_the_exact_pending_action_and_digest(kind: str) -> None:
    valid = intention(kind, {}) | {"pending_action_id": new_id(), "content_digest": "a" * 64}
    assert INTENT.is_valid(valid)
    for key in ("pending_action_id", "content_digest", "confidence"):
        invalid = valid.copy()
        invalid.pop(key)
        assert not INTENT.is_valid(invalid)
    assert not INTENT.is_valid(valid | {"content_digest": "changed"})


@pytest.mark.parametrize(
    "change",
    [
        {"priority": "preemptive"},
        {"confidence": 1.1},
        {"confidence": True},
        {"id": "not-a-uuid"},
        {"wall_ts": "yesterday"},
        {"monotonic_ts": -1},
        {"monotonic_ts": 2**53},
        {"audio": "raw"},
        {"payload": {"button": "left", "landmarks": [1, 2]}},
        {"type": "shell.execute"},
        {"actor_origin": "operator"},
    ],
)
def test_invalid_or_unexpected_data_is_rejected(change: dict[str, object]) -> None:
    assert not INTENT.is_valid(intention() | change)


def test_profile_floor_no_clinical_fields_and_explicit_declared_condition() -> None:
    valid = profile()
    assert PROFILE.is_valid(valid)
    assert not PROFILE.is_valid(valid | {"min_target_px": 43})
    assert not PROFILE.is_valid(valid | {"diagnosis": "private"})
    assert not PROFILE.is_valid(valid | {"declared_condition": "private"})
    assert PROFILE.is_valid(
        valid
        | {
            "declared_condition": {
                "text": "Información declarada por la persona",
                "consent_ref": "consent-1",
                "category": "special",
            }
        }
    )


@pytest.mark.parametrize("kind", ["control.stop", "control.undo", "help.request_human"])
def test_each_enabled_modality_needs_its_safety_bindings(kind: str) -> None:
    valid = profile()
    valid["bindings"] = [item for item in valid["bindings"] if item["intent"] != kind]  # type: ignore[union-attr]
    assert not PROFILE.is_valid(valid)
    other = copy.deepcopy(profile())
    other["modalities"] = {"voice": {"enabled": True}, "head_gesture": {"enabled": True}}
    assert not PROFILE.is_valid(other)  # los vínculos de voz no protegen otra modalidad
