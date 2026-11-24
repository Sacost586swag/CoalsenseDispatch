"""Validación local sin red y errores sin valores privados (REQ-01-001, 004, 083)."""

import json
from copy import deepcopy
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker

from ._schemas import CATALOG, HEARTBEAT_SCHEMA, INTENT_SCHEMA, PROFILE_SCHEMA, TOOL_MANIFEST_SCHEMA
from .models import CapabilityProfile, HeartbeatEvent, Intent, ToolManifest

_FORMATS = FormatChecker()
if "date-time" not in _FORMATS.checkers:
    raise RuntimeError("RFC 3339 validation is required")
_INTENTS = {
    kind: Draft202012Validator(
        {"$defs": INTENT_SCHEMA["$defs"], "$ref": "#/$defs/" + item["definition"]},
        format_checker=_FORMATS,
    )
    for kind, item in CATALOG.items()
}
_PROFILE = Draft202012Validator(PROFILE_SCHEMA, format_checker=_FORMATS)
_HEARTBEAT = Draft202012Validator(HEARTBEAT_SCHEMA, format_checker=_FORMATS)
_TOOL_MANIFEST = Draft202012Validator(TOOL_MANIFEST_SCHEMA, format_checker=_FORMATS)
_TOOL_NAME = Draft202012Validator(
    {
        "$defs": TOOL_MANIFEST_SCHEMA["$defs"],
        "$ref": "#/$defs/ToolName",
    }
)


class ContractError(ValueError):
    """El error no contiene la entrada, los errores del validador ni sus rutas."""


def _json_copy(value: object) -> object:
    # Un round trip garantiza JSON real: sin NaN, infinito, objetos Python ni ciclos.
    # La copia aísla al bus de cambios posteriores por parte de un adaptador.
    return json.loads(json.dumps(value, allow_nan=False))


def validate_intent(value: object) -> Intent:
    try:
        candidate = _json_copy(value)
        if not isinstance(candidate, dict):
            raise ValueError
        kind = candidate.get("type")
        if not isinstance(kind, str) or kind not in _INTENTS:
            raise ValueError
        _INTENTS[kind].validate(candidate)
        candidate["monotonic_ts"] = int(candidate["monotonic_ts"])
        return cast(Intent, candidate)
    except Exception:
        raise ContractError("Invalid intention") from None


def validate_profile(value: object) -> CapabilityProfile:
    try:
        candidate = _json_copy(value)
        _PROFILE.validate(candidate)
        return cast(CapabilityProfile, deepcopy(candidate))
    except Exception:
        raise ContractError("Invalid capability profile") from None


def priority_for(kind: str) -> str:
    if kind not in CATALOG:
        raise ContractError("Unknown intention type")
    return CATALOG[kind]["priority"]


def validate_heartbeat(value: object) -> HeartbeatEvent:
    try:
        candidate = _json_copy(value)
        _HEARTBEAT.validate(candidate)
        assert isinstance(candidate, dict)
        identifiers = [route["identifier"] for route in candidate["state"]["routes"]]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError
        return cast(HeartbeatEvent, candidate)
    except Exception:
        raise ContractError("Invalid heartbeat event") from None


def intent_types() -> frozenset[str]:
    return frozenset(CATALOG)


def validate_tool_manifest(value: object) -> ToolManifest:
    candidate: object = None
    valid = False
    try:
        candidate = _json_copy(value)
        _TOOL_MANIFEST.validate(candidate)
        valid = True
    except Exception:
        pass
    if not valid:
        raise ContractError("Invalid tool manifest")
    return cast(ToolManifest, candidate)


def validate_tool_name(value: object) -> str:
    if type(value) is not str or not _TOOL_NAME.is_valid(value):
        raise ContractError("Invalid tool name")
    return value
