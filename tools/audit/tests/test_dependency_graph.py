"""Los consumidores no pueden reutilizar resultados de dependencias anteriores."""

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def validate_tasks(tasks: dict[str, dict[str, object]]) -> None:
    for name in ("lint", "typecheck", "test", "build"):
        assert f"^{name}" in tasks[name].get("dependsOn", [])
    assert "COALSENSE_SKIP_NETWORK_TESTS" in tasks["test"].get("env", [])
    assert "COALSENSE_TEST_POSTGRES" in tasks["test"].get("env", [])


def test_quality_and_build_tasks_hash_upstream_dependencies() -> None:
    validate_tasks(json.loads((ROOT / "turbo.json").read_text("utf-8"))["tasks"])


@pytest.mark.parametrize("name", ["lint", "typecheck", "test", "build"])
def test_missing_upstream_edge_is_rejected(name: str) -> None:
    tasks = json.loads((ROOT / "turbo.json").read_text("utf-8"))["tasks"]
    tasks[name]["dependsOn"] = []
    with pytest.raises(AssertionError):
        validate_tasks(tasks)


@pytest.mark.parametrize("name", ["COALSENSE_SKIP_NETWORK_TESTS", "COALSENSE_TEST_POSTGRES"])
def test_test_results_cannot_be_reused_with_a_different_integration_mode(name: str) -> None:
    tasks = json.loads((ROOT / "turbo.json").read_text("utf-8"))["tasks"]
    tasks["test"]["env"].remove(name)
    with pytest.raises(AssertionError):
        validate_tasks(tasks)


@pytest.mark.integration
def test_required_integration_graph_contains_the_real_postgres_runner() -> None:
    pnpm = "pnpm.cmd" if os.name == "nt" else "pnpm"
    result = subprocess.run(
        [pnpm, "exec", "turbo", "run", "test:integration", "--dry=json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    tasks = json.loads(result.stdout)["tasks"]
    task = next(
        item for item in tasks if item["taskId"] == "@coalsense/orchestrator#test:integration"
    )
    assert task["command"] == "uv run --locked python tools/test_postgres.py"
    assert (ROOT / "apps/orchestrator/tools/test_postgres.py").is_file()


def test_python_workspace_dependencies_are_visible_to_turborepo() -> None:
    workspace = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["tool"]["uv"][
        "workspace"
    ]
    members = {}
    for relative in workspace["members"]:
        path = ROOT / relative
        project = tomllib.loads((path / "pyproject.toml").read_text("utf-8"))["project"]
        manifest = json.loads((path / "package.json").read_text("utf-8"))
        members[project["name"]] = (project, manifest)
    for project, manifest in members.values():
        for dependency in project.get("dependencies", []):
            name = re.split(r"[<>=!;\[ ]", dependency, maxsplit=1)[0]
            if name in members:
                target = members[name][1]["name"]
                assert manifest.get("dependencies", {}).get(target) == "workspace:*"
