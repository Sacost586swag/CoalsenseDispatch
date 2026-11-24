"""Contrato de manifiesto compartido y sin dependencia del orquestador."""

import json
from pathlib import Path

import pytest
from coalsense_intents import ContractError, validate_tool_manifest, validate_tool_name
from jsonschema import Draft202012Validator

SCHEMA = json.loads(
    (Path(__file__).parents[1] / "schema/tool-manifest.schema.json").read_text("utf-8")
)


def candidate() -> dict[str, object]:
    return {
        "name": "doc.export",
        "input_schema": {"type": "object"},
        "output_schema": {},
        "reversible": False,
        "data_categories": ["task.content"],
        "provider": "local",
    }


def test_contract_is_valid_and_optional_effect_is_not_interpreted_as_read() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    source = candidate()
    assert Draft202012Validator(SCHEMA).is_valid(source)
    parsed = validate_tool_manifest(source)
    assert "effect_class" not in parsed
    parsed["input_schema"]["type"] = "null"
    assert source["input_schema"] == {"type": "object"}


@pytest.mark.parametrize("field", ["name", "input_schema", "output_schema", "provider"])
def test_embedded_schema_and_source_reject_missing_fields(field: str) -> None:
    source = candidate()
    source.pop(field)
    assert not Draft202012Validator(SCHEMA).is_valid(source)
    with pytest.raises(ContractError, match="^Invalid tool manifest$"):
        validate_tool_manifest(source)


def test_non_json_and_cyclic_manifests_fail_without_private_error_context() -> None:
    source = candidate()
    source["input_schema"] = source
    with pytest.raises(ContractError) as caught:
        validate_tool_manifest(source)
    assert caught.value.__context__ is None


@pytest.mark.parametrize("value", ["email.send\n", "Un texto privado", "Email.send", None, 1])
def test_tool_name_validation_reuses_the_shared_contract(value: object) -> None:
    with pytest.raises(ContractError, match="^Invalid tool name$"):
        validate_tool_name(value)
    assert validate_tool_name("email.send") == "email.send"
