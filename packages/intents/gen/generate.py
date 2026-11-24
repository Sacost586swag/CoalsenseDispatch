"""Generación determinista de tipos desde los esquemas; sin ejecutar código del esquema.

Los tipos describen formas. JSON Schema conserva las restricciones de valores y las
invariantes condicionales; el generador falla ante construcciones de forma desconocidas.
"""

from __future__ import annotations

import argparse
import json
import keyword
import subprocess
import sys
from pathlib import Path
from typing import Any

Schema = dict[str, Any]
ROOT = Path(__file__).resolve().parents[1]


def format_python(source: str) -> str:
    imports = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            "I",
            "--fix",
            "--stdin-filename",
            "generated.py",
            "-",
        ],
        input=source,
        cwd=ROOT.parents[1],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--stdin-filename", "generated.py", "-"],
        input=imports.stdout,
        cwd=ROOT.parents[1],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.replace("\r\n", "\n")


def embedded_json(name: str, value: object, annotation: str) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    chunks = [repr(encoded[index : index + 64]) for index in range(0, len(encoded), 64)]
    return f"{name}: {annotation} = json.loads(\n    " + "\n    ".join(chunks) + "\n)\n"


def name_of(reference: str) -> str:
    if not reference.startswith("#/$defs/"):
        raise ValueError("Only local schema references are supported")
    return reference.removeprefix("#/$defs/")


def expression(schema: Schema, language: str) -> str:
    if "$ref" in schema:
        return name_of(schema["$ref"])
    if "const" in schema:
        value = schema["const"]
        return f"Literal[{value!r}]" if language == "py" else json.dumps(value)
    if "enum" in schema:
        values = schema["enum"]
        return (
            "Literal[" + ", ".join(repr(v) for v in values) + "]"
            if language == "py"
            else " | ".join(json.dumps(v) for v in values)
        )
    union = schema.get("oneOf", schema.get("anyOf"))
    if union is not None:
        return " | ".join(expression(part, language) for part in union)
    kind = schema.get("type")
    if isinstance(kind, list):
        return " | ".join(expression({"type": item}, language) for item in kind)
    primitive = {
        "string": ("str", "string"),
        "integer": ("int", "number"),
        "number": ("float", "number"),
        "boolean": ("bool", "boolean"),
        "null": ("None", "null"),
    }
    if kind in primitive:
        return primitive[kind][language == "ts"]
    if kind == "array":
        item = expression(schema["items"], language)
        return f"list[{item}]" if language == "py" else f"Array<{item}>"
    if kind == "object" and "properties" not in schema:
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            value = expression(additional, language)
            # Una firma de índice admite recursión JSON en TypeScript;
            # Record<string, JsonValue> dentro del propio alias no la admite.
            return f"dict[str, {value}]" if language == "py" else f"{{ [key: string]: {value} }}"
    raise ValueError("Unsupported schema shape; extend the generator explicitly")


def definition(name: str, schema: Schema, language: str) -> str:
    if not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError("Invalid schema definition name")
    bases = [name_of(part["$ref"]) for part in schema.get("allOf", []) if "$ref" in part]
    parts = [schema, *(part for part in schema.get("allOf", []) if "properties" in part)]
    properties = {key: value for part in parts for key, value in part.get("properties", {}).items()}
    required = {key for part in parts for key in part.get("required", [])}
    if "properties" not in schema and not bases:
        value = expression(schema, language)
        return (
            f"type {name} = {value}\n" if language == "py" else f"export type {name} = {value};\n"
        )
    if language == "py":
        inherited = ", ".join(bases or ["TypedDict"])
        lines = [f"class {name}({inherited}):"]
        for key, prop in properties.items():
            if not key.isidentifier() or keyword.iskeyword(key):
                raise ValueError("Invalid Python field name")
            value = expression(prop, language)
            if key not in required:
                value = f"NotRequired[{value}]"
            lines.append(f"    {key}: {value}")
        return "\n".join(lines + (["    pass"] if not properties else [])) + "\n"
    if not properties:
        return f"export type {name} = Record<string, never>;\n"
    fields = [
        f"  {json.dumps(key)}{'' if key in required else '?'}: {expression(prop, language)};"
        for key, prop in properties.items()
    ]
    prefix = " & ".join(bases) + " & " if bases else ""
    return f"export type {name} = {prefix}{{\n" + "\n".join(fields) + "\n};\n"


def render(root: Path = ROOT) -> dict[str, str]:
    intent = json.loads((root / "schema/intent.schema.json").read_text("utf-8"))
    profile = json.loads((root / "schema/capability-profile.schema.json").read_text("utf-8"))
    heartbeat = json.loads((root / "schema/heartbeat.schema.json").read_text("utf-8"))
    manifest = json.loads((root / "schema/tool-manifest.schema.json").read_text("utf-8"))
    py = [
        '"""Generado desde schema/*.schema.json. No editar a mano."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import Literal, NotRequired, TypedDict\n"
    ]
    ts = ["// Generado desde schema/*.schema.json. No editar a mano.\n"]
    seen: dict[str, Schema] = {}
    for document in (intent, profile, heartbeat, manifest):
        for name, schema in document["$defs"].items():
            if name in seen:
                if seen[name] != schema:
                    raise ValueError("Conflicting schema definitions")
                continue
            seen[name] = schema
            py.append(definition(name, schema, "py"))
            ts.append(definition(name, schema, "ts"))
    py.append("type Intent = " + expression({"oneOf": intent["oneOf"]}, "py") + "\n")
    for alias, constant in (("Modality", "MODALITIES"), ("ActorOrigin", "ACTOR_ORIGINS")):
        values = tuple(intent["$defs"][alias]["enum"])
        py.append(f"{constant}: tuple[{alias}, ...] = {values!r}\n")
    ts.append("export type Intent = " + expression({"oneOf": intent["oneOf"]}, "ts") + ";\n")
    catalog: dict[str, dict[str, str]] = {}
    for item in intent["oneOf"]:
        name = name_of(item["$ref"])
        props = intent["$defs"][name]["allOf"][1]["properties"]
        catalog[props["type"]["const"]] = {
            "priority": props["priority"]["const"],
            "definition": name,
        }
    schema_text = (
        '"""Esquemas embebidos generados; no editar a mano."""\n\n'
        "import json\nfrom typing import Any\n\n"
        + embedded_json("INTENT_SCHEMA", intent, "dict[str, Any]")
        + "\n"
        + embedded_json("PROFILE_SCHEMA", profile, "dict[str, Any]")
        + "\n"
        + embedded_json("HEARTBEAT_SCHEMA", heartbeat, "dict[str, Any]")
        + "\n"
        + embedded_json("TOOL_MANIFEST_SCHEMA", manifest, "dict[str, Any]")
        + "\n"
        + embedded_json("CATALOG", catalog, "dict[str, dict[str, str]]")
    )
    return {
        "python/coalsense_intents/models.py": format_python("\n\n".join(py)),
        "python/coalsense_intents/_schemas.py": format_python(schema_text),
        "ts/src/types.ts": "\n".join(ts),
        "schema/catalog.yaml": json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generar tipos de intenciones y perfil")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for relative, content in render().items():
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_text("utf-8") != content:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    for relative in stale:
        print(f"Deriva del esquema: {relative}")
    return int(bool(stale))


if __name__ == "__main__":
    raise SystemExit(main())
