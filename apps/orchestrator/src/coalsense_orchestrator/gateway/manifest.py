"""Contratos inmutables de herramientas; validación local y sin contenido en errores."""

import json
from dataclasses import dataclass, field
from typing import cast

from coalsense_intents import validate_tool_manifest
from coalsense_intents.models import JsonValue, ToolEffectClass, ToolSchema
from jsonschema import Draft202012Validator, FormatChecker


class ManifestError(ValueError):
    """Código de dominio, sin datos ni errores internos del validador."""


def _local_schema(schema: ToolSchema) -> None:
    """No resuelve referencias remotas, ni siquiera durante el registro."""
    Draft202012Validator.check_schema(schema)

    def walk(value: JsonValue) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ("$ref", "$dynamicRef"):
                    if not isinstance(child, str) or not child.startswith("#"):
                        raise ManifestError("gateway.manifest.invalid")
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema)


@dataclass(frozen=True)
class ToolManifest:
    name: str
    effect_class: ToolEffectClass
    reversible: bool
    compensation: str | None
    data_categories: tuple[str, ...]
    provider: str
    _encoded: str = field(repr=False)

    @classmethod
    def parse(cls, value: object) -> "ToolManifest":
        result: ToolManifest | None = None
        try:
            candidate = validate_tool_manifest(value)
            _local_schema(candidate["input_schema"])
            _local_schema(candidate["output_schema"])
            effect = candidate.get("effect_class", "external_effect")
            candidate["effect_class"] = effect
            result = cls(
                candidate["name"],
                effect,
                candidate["reversible"],
                candidate.get("compensation"),
                tuple(candidate["data_categories"]),
                candidate["provider"],
                json.dumps(candidate, ensure_ascii=False, allow_nan=False),
            )
        except Exception:
            pass
        if result is None:
            raise ManifestError("gateway.manifest.invalid")
        return result

    def to_dict(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], json.loads(self._encoded))

    def _validate(self, value: object, schema_name: str, error: str) -> JsonValue:
        valid = False
        candidate: JsonValue = None
        try:
            candidate = json.loads(json.dumps(value, allow_nan=False))
            schema = self.to_dict()[schema_name]
            assert isinstance(schema, dict)
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(candidate)
            valid = True
        except Exception:
            pass
        if not valid:
            raise ManifestError(error)
        return candidate

    def validate_input(self, value: object) -> JsonValue:
        return self._validate(value, "input_schema", "gateway.input.invalid")

    def validate_output(self, value: object) -> JsonValue:
        return self._validate(value, "output_schema", "gateway.output.invalid")
