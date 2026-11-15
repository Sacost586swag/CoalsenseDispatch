"""REQ-00-002/061: validate the CI contract without a YAML dependency.

ci.yml deliberately uses JSON (a YAML 1.2 subset), plus full-line YAML comments.
Strip only full-line comments, then parse with stdlib json, rejecting duplicate
keys. This is a strict documented subset, not a general-purpose YAML parser:
unsupported YAML fails instead of silently bypassing structural checks.
All mutated workflows live exclusively in tmp_path; no network/tools required.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[3]
WORKFLOW = REPO / ".github/workflows/ci.yml"
STAGES = ["install", "lint", "typecheck", "test", "audit", "accessibility", "integration"]
pytestmark = pytest.mark.integration


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result, f"Duplicate key: {key}"
        result[key] = value
    return result


def _load(path: Path) -> dict[str, Any]:
    source = "\n".join(
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    )
    config: dict[str, Any] = json.loads(source, object_pairs_hook=_unique)
    return config


def _validate(config: dict[str, Any]) -> None:
    assert config["on"] == {"pull_request": {}}
    assert config["permissions"] == {"contents": "read"}
    assert config["concurrency"] == {
        "group": "ci-${{ github.workflow }}-${{ github.event.pull_request.number }}",
        "cancel-in-progress": True,
    }
    assert config["defaults"] == {"run": {"shell": "bash"}}
    assert "secrets" not in json.dumps(config).lower()
    jobs = config["jobs"]
    assert list(jobs) == ["start", *STAGES, "required"]
    for job in jobs.values():
        assert "permissions" not in job
        assert "continue-on-error" not in job
        for step in job["steps"]:
            assert "continue-on-error" not in step
            if "uses" in step:
                assert re.fullmatch(r"[\w-]+/[\w-]+@[0-9a-f]{40}", step["uses"])

    for index, stage in enumerate(STAGES):
        job = jobs[stage]
        assert job["needs"] == [STAGES[index - 1] if index else "start"]
        assert "if" not in job  # Default success() must gate every stage.
        assert job["timeout-minutes"] == 15
        if index < 4:
            assert job["runs-on"] == "${{ matrix.os }}"
            assert job["strategy"] == {
                "fail-fast": False,
                "matrix": {"os": ["ubuntu-latest", "windows-latest"]},
            }
        else:
            assert job["runs-on"] == "ubuntu-latest"
        steps = job["steps"]
        assert all("if" not in step for step in steps)
        assert len(steps) == (7 if stage in STAGES[1:4] else 5 if stage == "install" else 6)
        for step, action, inputs in zip(
            steps[:3],
            ["actions/checkout", "actions/setup-node", "actions/setup-python"],
            [
                {"fetch-depth": 0, "persist-credentials": False},
                {"node-version": "24"},
                {"python-version": "3.12"},
            ],
            strict=True,
        ):
            assert step["uses"].split("@")[0] == action
            assert step["with"] == inputs
        assert steps[3]["run"] == (
            "npm install --global pnpm@11.21.0\npython -m pip install uv==0.12.13"
        )
        assert steps[4]["run"] == "pnpm install --frozen-lockfile\nuv sync --locked"
        if stage in STAGES[1:4]:
            assert steps[5]["run"] == "git rev-parse --verify origin/main"
            assert steps[6]["run"] == f"pnpm turbo run {stage} --filter=...[origin/main]"
        elif stage != "install":
            task = {
                "audit": "audit",
                "accessibility": "test:a11y",
                "integration": "test:integration",
            }[stage]
            assert steps[5]["run"] == f"pnpm turbo run {task}"

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
    assert gate["env"] == {"RESULTS": "${{ join(needs.*.result, ',') }}"}
    assert '"$result" != "success"' in gate["run"]
    assert "exit 1" in gate["run"]
    assert summary["if"] == "${{ always() }}"
    assert summary["env"] == {"STARTED": "${{ needs.start.outputs.started }}"}
    assert "$(date +%s) - STARTED" in summary["run"]
    assert '>> "$GITHUB_STEP_SUMMARY"' in summary["run"]
    assert "${elapsed}s" in summary["run"]


def test_ci_contract() -> None:
    _validate(_load(WORKFLOW))


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("on",), {"push": {}}),
        (("permissions",), {"contents": "write"}),
        (("concurrency", "cancel-in-progress"), False),
        (("jobs", "test", "needs"), ["install"]),
        (("jobs", "lint", "if"), "${{ always() }}"),
        (("jobs", "typecheck", "continue-on-error"), True),
        (("jobs", "test", "strategy", "matrix", "os"), ["ubuntu-latest"]),
        (("jobs", "install", "steps", 0, "uses"), "actions/checkout@v4"),
        (("jobs", "install", "steps", 0, "with", "fetch-depth"), 1),
        (("jobs", "install", "steps", 1, "with", "node-version"), "22"),
        (("jobs", "install", "steps", 2, "with", "python-version"), "3.13"),
        (("jobs", "install", "steps", 3, "run"), "npm install -g pnpm\npip install uv"),
        (("jobs", "install", "steps", 4, "run"), "pnpm install\nuv sync"),
        (("jobs", "lint", "steps", 6, "run"), "pnpm turbo run lint"),
        (("jobs", "typecheck", "steps", 6, "run"), "pnpm turbo run typecheck"),
        (("jobs", "test", "steps", 6, "run"), "pnpm turbo run test || true"),
        (("jobs", "audit", "steps", 5, "run"), "pnpm turbo run audit --filter=...[origin/main]"),
        (("jobs", "accessibility", "steps", 5, "continue-on-error"), True),
        (("jobs", "integration", "steps", 5, "run"), "echo placeholder"),
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
    target = config
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    candidate = tmp_path / "ci.yml"
    candidate.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(AssertionError):
        _validate(_load(candidate))


def test_ci_rejects_missing_stage(tmp_path: Path) -> None:
    config = _load(WORKFLOW)
    del config["jobs"]["audit"]
    candidate = tmp_path / "ci.yml"
    candidate.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(AssertionError):
        _validate(_load(candidate))


def test_ci_rejects_duplicate_keys(tmp_path: Path) -> None:
    candidate = tmp_path / "ci.yml"
    candidate.write_text('{"permissions": {}, "permissions": {}}', encoding="utf-8")
    with pytest.raises(AssertionError, match="Duplicate key"):
        _load(candidate)
