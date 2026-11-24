"""REQ-02-021/022: registro cerrado, contratos completos y efecto por defecto."""

from copy import deepcopy

import pytest
from coalsense_orchestrator.gateway.manifest import ManifestError, ToolManifest
from coalsense_orchestrator.gateway.registry import ToolRegistry


def manifest() -> dict[str, object]:
    return {
        "name": "email.draft",
        "input_schema": {
            "type": "object",
            "properties": {"body": {"type": "string"}},
            "required": ["body"],
            "additionalProperties": False,
        },
        "output_schema": {"type": "object", "additionalProperties": False},
        "effect_class": "internal_write",
        "reversible": True,
        "compensation": "email.discard_draft",
        "data_categories": [],
        "provider": "local",
    }


def test_missing_effect_defaults_to_external_without_mutating_the_manifest() -> None:
    source = manifest()
    source.pop("effect_class")
    parsed = ToolManifest.parse(source)
    assert parsed.effect_class == "external_effect"
    assert "effect_class" not in source


@pytest.mark.parametrize(
    "key",
    ["name", "input_schema", "output_schema", "reversible", "data_categories", "provider"],
)
def test_incomplete_manifest_fails(key: str) -> None:
    source = manifest()
    source.pop(key)
    with pytest.raises(ManifestError, match="^gateway.manifest.invalid$"):
        ToolManifest.parse(source)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("name", "email draft"),
        ("name", ""),
        ("name", "Email.send"),
        ("name", "email.draft\n"),
        ("effect_class", None),
        ("effect_class", "unknown"),
        ("reversible", 1),
        ("compensation", None),
        ("compensation", ""),
        ("data_categories", ["task", "task"]),
        ("data_categories", [" "]),
        ("data_categories", ["task\n"]),
        ("provider", ""),
        ("provider", "local\n"),
        ("input_schema", {"type": "nonsense"}),
        ("output_schema", {"required": "not-a-list"}),
        ("secret", "private"),
    ],
)
def test_invalid_or_unknown_fields_fail_without_echo(key: str, value: object) -> None:
    source = manifest()
    source[key] = value
    with pytest.raises(ManifestError, match="^gateway.manifest.invalid$") as caught:
        ToolManifest.parse(source)
    assert "private" not in str(caught.value)


def test_reversibility_and_compensation_are_consistent() -> None:
    source = manifest()
    source.pop("compensation")
    with pytest.raises(ManifestError):
        ToolManifest.parse(source)
    source["reversible"] = False
    assert ToolManifest.parse(source).compensation is None
    source["compensation"] = "email.discard_draft"
    with pytest.raises(ManifestError):
        ToolManifest.parse(source)


def test_validates_input_and_output_without_reflecting_private_content() -> None:
    parsed = ToolManifest.parse(manifest())
    private = {"body": "Mis notas privadas"}
    result = parsed.validate_input(private)
    assert result == private and result is not private
    result["body"] = "Otro"
    assert private["body"] == "Mis notas privadas"
    for operation, value in [
        (parsed.validate_input, {"body": "Mis notas privadas", "unexpected": True}),
        (parsed.validate_output, {"private": "Mis notas privadas"}),
        (parsed.validate_input, {"body": float("nan")}),
    ]:
        with pytest.raises(ManifestError) as caught:
            operation(value)
        assert "privadas" not in str(caught.value)
        assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "reference", ["https://invalid.example/schema", "file:///private", "other.json"]
)
def test_remote_references_are_rejected_at_registration(reference: str) -> None:
    source = manifest()
    source["input_schema"] = {"$defs": {"Hidden": {"$ref": reference}}}
    with pytest.raises(ManifestError):
        ToolManifest.parse(source)


def test_local_references_and_formats_are_checked_without_network() -> None:
    source = manifest()
    source["input_schema"] = {
        "$defs": {"Date": {"type": "string", "format": "date-time"}},
        "$ref": "#/$defs/Date",
    }
    parsed = ToolManifest.parse(source)
    assert parsed.validate_input("2026-11-18T10:00:00Z") == "2026-11-18T10:00:00Z"
    with pytest.raises(ManifestError):
        parsed.validate_input("not-a-date")


def test_registry_refuses_duplicates_and_returns_isolated_contracts() -> None:
    registry = ToolRegistry()
    source = manifest()
    registry.register(source)
    source["effect_class"] = "read"
    contract = registry.get("email.draft")
    assert contract.effect_class == "internal_write"
    exported = contract.to_dict()
    exported["input_schema"] = {"type": "null"}
    assert contract.to_dict()["input_schema"] != exported["input_schema"]
    with pytest.raises(ManifestError, match="^gateway.tool.duplicate$"):
        registry.register(deepcopy(manifest()))
    with pytest.raises(ManifestError, match="^gateway.tool.unknown$"):
        registry.get("email.send")
    assert registry.names() == ("email.draft",)
