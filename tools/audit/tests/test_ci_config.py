"""REQ-00-002/061: validate the CI contract with a real YAML parser (PyYAML, dev only).

ci.yml and the local setup action are ordinary block YAML. They are parsed with
`yaml.safe_load` through a loader that rejects duplicate keys. PyYAML follows YAML 1.1,
so the bare `on:` key loads as the boolean True; `_on` normalises that.
Mutated workflows live exclusively in tmp_path; the helper script is exercised with
node over stdin (no files written).
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

REPO = Path(__file__).resolve().parents[3]
WORKFLOW = REPO / ".github/workflows/ci.yml"
SETUP = REPO / ".github/actions/setup/action.yml"
REQUIRE_TASKS = REPO / ".github/scripts/require-tasks.mjs"
STAGES = ["install", "lint", "typecheck", "test", "audit", "accessibility", "integration"]
MATRIX_STAGES = ["install", "lint", "typecheck", "test"]
FILTERED = ["lint", "typecheck", "test"]
UNFILTERED = {"audit": "audit", "accessibility": "test:a11y", "integration": "test:integration"}
SHA_PIN = re.compile(r"[\w-]+/[\w-]+@[0-9a-f]{40}")
pytestmark = pytest.mark.integration


class _UniqueLoader(yaml.SafeLoader):  # type: ignore[misc]
    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            assert key not in seen, f"Duplicate key: {key}"
            seen.add(key)
        mapping: dict[Any, Any] = super().construct_mapping(node, deep)
        return mapping


def _load(path: Path) -> dict[Any, Any]:
    config: dict[Any, Any] = yaml.load(path.read_text(encoding="utf-8"), _UniqueLoader)
    return config


def _on(config: dict[Any, Any]) -> Any:
    return config["on"] if "on" in config else config[True]


def _validate_pins(uses: str) -> None:
    if uses.startswith("./"):
        assert uses == "./.github/actions/setup"
    else:
        assert SHA_PIN.fullmatch(uses), uses


def _validate_setup(action: dict[Any, Any]) -> None:
    assert action["runs"]["using"] == "composite"
    steps = action["runs"]["steps"]
    for step in steps:
        assert "continue-on-error" not in step
        if "uses" in step:
            _validate_pins(step["uses"])
        else:
            assert step["shell"] == "bash"
    node, python, uv, pnpm, store, cache, install = steps
    assert node["uses"].startswith("actions/setup-node@")
    assert node["with"] == {"node-version": "24"}
    assert python["uses"].startswith("actions/setup-python@")
    assert python["with"] == {"python-version": "3.12"}
    assert uv["uses"].startswith("astral-sh/setup-uv@")
    assert uv["with"] == {
        "version": "0.12.13",
        "enable-cache": True,
        "cache-dependency-glob": "uv.lock",
    }
    assert pnpm["run"] == "npm install --global pnpm@11.21.0"
    assert 'pnpm store path --silent)" >> "$GITHUB_OUTPUT"' in store["run"]
    assert cache["uses"].startswith("actions/cache@")
    assert cache["with"]["path"] == "${{ steps.pnpm-store.outputs.path }}"
    assert "hashFiles('pnpm-lock.yaml')" in cache["with"]["key"]
    assert "runner.os" in cache["with"]["key"]
    assert install["run"].strip() == "pnpm install --frozen-lockfile\nuv sync --locked"


def _validate(config: dict[Any, Any]) -> None:
    assert _on(config) == {"pull_request": None, "merge_group": None}
    assert config["permissions"] == {"contents": "read"}
    assert config["concurrency"] == {
        "group": "ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}",
        "cancel-in-progress": True,
    }
    assert config["defaults"] == {"run": {"shell": "bash"}}
    assert "secrets" not in json.dumps(config, default=str).lower()
    jobs = config["jobs"]
    assert list(jobs) == ["start", *STAGES, "required"]
    for job in jobs.values():
        assert "permissions" not in job
        assert "continue-on-error" not in job
        for step in job["steps"]:
            assert "continue-on-error" not in step
            if "uses" in step:
                _validate_pins(step["uses"])

    for stage in STAGES:
        job = jobs[stage]
        # Every stage hangs off install: audit/a11y/integration are not hidden behind test.
        assert job["needs"] == (["start"] if stage == "install" else ["install"])
        assert "if" not in job  # Default success() must gate every stage.
        assert job["timeout-minutes"] == 15
        if stage in MATRIX_STAGES:
            assert job["runs-on"] == "${{ matrix.os }}"
            assert job["strategy"] == {
                "fail-fast": False,
                "matrix": {"os": ["ubuntu-latest", "windows-latest"]},
            }
        else:
            assert job["runs-on"] == "ubuntu-latest"
            assert "strategy" not in job
        steps = job["steps"]
        assert all("if" not in step for step in steps)
        checkout, setup, *rest = steps
        assert checkout["uses"].startswith("actions/checkout@")
        assert checkout["with"] == {"fetch-depth": 0, "persist-credentials": False}
        assert setup == {"uses": "./.github/actions/setup"}
        if stage == "install":
            assert rest == []
        elif stage in FILTERED:
            assert [step["run"] for step in rest] == [
                "git rev-parse --verify origin/main",
                f"pnpm turbo run {stage} --filter='...[origin/main]'",
            ]
        else:
            task = UNFILTERED[stage]
            # turbo exits 0 when a task exists but no package implements it: require >=1 task.
            assert [step["run"] for step in rest] == [
                f"pnpm turbo run {task} --dry=json | node .github/scripts/require-tasks.mjs {task}",
                f"pnpm turbo run {task}",
            ]

    start = jobs["start"]
    assert start["outputs"] == {"started": "${{ steps.clock.outputs.started }}"}
    assert start["steps"] == [
        {"id": "clock", "run": 'echo "started=$(date +%s)" >> "$GITHUB_OUTPUT"'}
    ]
    final = jobs["required"]
    assert final["needs"] == ["start", *STAGES]
    assert final["if"] == "${{ always() }}"
    gate, summary = final["steps"]
    assert "if" not in gate
    assert gate["env"] == {"NEEDS": "${{ toJSON(needs) }}"}
    assert '.value.result != "success"' in gate["run"]
    assert '"\\(.key)=\\(.value.result)"' in gate["run"]  # names each failed stage
    assert "exit 1" in gate["run"]
    assert summary["if"] == "${{ always() }}"
    assert summary["env"] == {"STARTED": "${{ needs.start.outputs.started }}"}
    assert "$(date +%s) - STARTED" in summary["run"]
    assert '>> "$GITHUB_STEP_SUMMARY"' in summary["run"]
    assert "${elapsed}s" in summary["run"]


def test_ci_contract() -> None:
    _validate(_load(WORKFLOW))
    _validate_setup(_load(SETUP))


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("on",), {"push": None}),
        (("on",), {"pull_request": None}),  # merge_group missing: merge queue would hang
        (("permissions",), {"contents": "write"}),
        (("concurrency", "cancel-in-progress"), False),
        (("jobs", "test", "needs"), ["typecheck"]),
        (("jobs", "audit", "needs"), ["test"]),  # audit hidden behind a failing test
        (("jobs", "integration", "needs"), ["accessibility"]),
        (("jobs", "lint", "if"), "${{ always() }}"),
        (("jobs", "typecheck", "continue-on-error"), True),
        (("jobs", "test", "strategy", "matrix", "os"), ["ubuntu-latest"]),
        (("jobs", "install", "steps", 0, "uses"), "actions/checkout@v4"),
        (("jobs", "install", "steps", 0, "with", "fetch-depth"), 1),
        (("jobs", "install", "steps", 1, "uses"), "./.github/actions/other"),
        (("jobs", "lint", "steps", 2, "run"), "git rev-parse HEAD"),
        (("jobs", "lint", "steps", 3, "run"), "pnpm turbo run lint"),
        (("jobs", "lint", "steps", 3, "run"), "pnpm turbo run lint --filter=...[origin/main]"),
        (("jobs", "typecheck", "steps", 3, "run"), "pnpm turbo run typecheck"),
        (("jobs", "test", "steps", 3, "run"), "pnpm turbo run test || true"),
        (("jobs", "audit", "steps", 2, "run"), "pnpm turbo run audit --dry=json"),
        (("jobs", "audit", "steps", 3, "run"), "pnpm turbo run audit --filter='...[origin/main]'"),
        (("jobs", "accessibility", "steps", 2, "run"), "echo skip"),  # no task-count guard
        (("jobs", "accessibility", "steps", 3, "continue-on-error"), True),
        (("jobs", "integration", "steps", 3, "run"), "echo placeholder"),
        (("jobs", "audit", "permissions"), {"contents": "write"}),
        (("jobs", "required", "if"), "${{ success() }}"),
        (("jobs", "required", "steps", 0, "run"), "echo success"),
        (("jobs", "required", "steps", 1, "run"), "echo duration"),
        (("jobs", "required", "steps", 1, "if"), "${{ success() }}"),
        (("env",), {"TOKEN": "${{ secrets.TOKEN }}"}),
    ],
)
def test_ci_rejects_contract_regressions(
    tmp_path: Path, path: tuple[Any, ...], value: object
) -> None:
    config = _load(WORKFLOW)
    if path == ("on",):  # PyYAML 1.1 loads the bare `on` key as True.
        path = (True,) if True in config else path
    target: Any = config
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    candidate = tmp_path / "ci.yml"
    candidate.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(AssertionError):
        _validate(_load(candidate))


@pytest.mark.parametrize(
    ("step", "key", "value"),
    [
        (0, "uses", "actions/setup-node@v4"),
        (0, "with", {"node-version": "22"}),
        (1, "with", {"python-version": "3.13"}),
        (
            2,
            "with",
            {"version": "latest", "enable-cache": True, "cache-dependency-glob": "uv.lock"},
        ),
        (
            2,
            "with",
            {"version": "0.12.13", "enable-cache": False, "cache-dependency-glob": "uv.lock"},
        ),
        (3, "run", "npm install --global pnpm"),
        (5, "with", {"path": "x", "key": "static"}),
        (6, "run", "pnpm install\nuv sync"),
    ],
)
def test_setup_action_rejects_regressions(
    tmp_path: Path, step: int, key: str, value: object
) -> None:
    action = _load(SETUP)
    action["runs"]["steps"][step][key] = value
    candidate = tmp_path / "action.yml"
    candidate.write_text(yaml.safe_dump(action), encoding="utf-8")
    with pytest.raises(AssertionError):
        _validate_setup(_load(candidate))


def test_ci_rejects_missing_stage(tmp_path: Path) -> None:
    config = _load(WORKFLOW)
    del config["jobs"]["audit"]
    candidate = tmp_path / "ci.yml"
    candidate.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(AssertionError):
        _validate(_load(candidate))


def test_ci_rejects_duplicate_keys(tmp_path: Path) -> None:
    candidate = tmp_path / "ci.yml"
    candidate.write_text("permissions:\n  contents: read\npermissions:\n  contents: write\n")
    with pytest.raises(AssertionError, match="Duplicate key"):
        _load(candidate)


def _run_require_tasks(plan: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    assert node, "node is required to exercise require-tasks.mjs"
    return subprocess.run(
        [node, str(REQUIRE_TASKS), "test:a11y"],
        input=plan,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("plan", "code"),
    [
        ('{"tasks": [{"command": "vitest run"}]}', 0),
        ('{"tasks": [{"command": "<NONEXISTENT>"}, {"command": "pnpm test"}]}', 0),
        ('{"tasks": []}', 1),  # task defined in turbo.json, no package implements it
        ('{"tasks": [{"command": "<NONEXISTENT>"}]}', 1),
        ("not json", 1),
    ],
)
def test_require_tasks_fails_on_empty_stage(plan: str, code: int) -> None:
    assert _run_require_tasks(plan).returncode == code
