"""REQ-01-002: cambios de forma, restricciones o salida requieren regeneración."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from coalsense_audit.schema_drift import audit

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    target = tmp_path / "packages/intents"
    source = ROOT / "packages/intents"
    target.mkdir(parents=True)
    for directory in ("schema", "gen", "python", "ts"):
        shutil.copytree(
            source / directory, target / directory, ignore=shutil.ignore_patterns("__pycache__")
        )
    shutil.copy2(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    return tmp_path


def test_committed_generation_is_current(tree: Path) -> None:
    assert audit(tree) == []


def test_generation_is_independent_of_the_callers_working_directory(tree: Path) -> None:
    package = tree / "packages/intents"
    result = subprocess.run(
        [sys.executable, str(package / "gen/generate.py"), "--check"],
        cwd=package,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "mutation", ["schema", "constraint", "heartbeat", "manifest", "python", "ts", "missing"]
)
def test_unregenerated_change_is_rejected(tree: Path, mutation: str) -> None:
    root = tree / "packages/intents"
    path = root / "schema/intent.schema.json"
    if mutation in {"schema", "constraint"}:
        document = json.loads(path.read_text("utf-8"))
        if mutation == "schema":
            document["$defs"]["TextInsertPayload"]["properties"]["extra"] = {"type": "boolean"}
        else:
            document["$defs"]["Envelope"]["properties"]["monotonic_ts"]["minimum"] = 2
        path.write_text(json.dumps(document), encoding="utf-8")
    elif mutation == "missing":
        (root / "ts/src/types.ts").unlink()
    elif mutation == "manifest":
        manifest = root / "schema/tool-manifest.schema.json"
        document = json.loads(manifest.read_text("utf-8"))
        document["$defs"]["ToolName"]["minLength"] = 4
        manifest.write_text(json.dumps(document), encoding="utf-8")
    elif mutation == "heartbeat":
        heartbeat = root / "schema/heartbeat.schema.json"
        document = json.loads(heartbeat.read_text("utf-8"))
        document["$defs"]["HeartbeatEvent"]["properties"]["sequence"]["minimum"] = 2
        heartbeat.write_text(json.dumps(document), encoding="utf-8")
    else:
        output = root / (
            "python/coalsense_intents/models.py" if mutation == "python" else "ts/src/types.ts"
        )
        output.write_text(output.read_text("utf-8") + "\n", encoding="utf-8")
    assert audit(tree)
