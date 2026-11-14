"""Forbidden import fixtures live exclusively in pytest temporary directories."""

import json
from pathlib import Path

import pytest
from coalsense_audit.imports import audit


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    policy = Path(__file__).resolve().parents[1] / "forbidden_imports.yaml"
    target = tmp_path / "tools/audit/forbidden_imports.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(policy.read_bytes())
    return tmp_path


def write(root: Path, path: str, source: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


@pytest.mark.parametrize("adapter", ["voice", "head_gesture", "gaze", "vision"])
@pytest.mark.parametrize(
    "module", ["socket", "http", "urllib", "requests", "httpx", "aiohttp", "websockets"]
)
def test_private_adapters(tree: Path, adapter: str, module: str) -> None:
    path = f"apps/companion/src/client/adapters/{adapter}/nested/run.py"
    write(tree, path, f"import {module}.client as client\n")
    assert any(f"{path}:1: RED_PRIVADA:" in f for f in audit(tree))


@pytest.mark.parametrize(
    "module", ["psycopg", "psycopg2", "asyncpg", "sqlalchemy", "coalsense_orchestrator.persistence"]
)
@pytest.mark.parametrize(
    "source",
    [
        "import {module} as db",
        "from {module} import client",
        'importlib.import_module("{module}")',
        '__import__("{module}")',
    ],
)
def test_agents(tree: Path, module: str, source: str) -> None:
    write(tree, "apps/orchestrator/agents/run.py", source.format(module=module))
    assert any("BD_AGENTES" in f for f in audit(tree))


@pytest.mark.parametrize(
    "module", ["requests", "httpx", "aiohttp", "urllib.request", "http.client", "websockets"]
)
@pytest.mark.parametrize("base", ["apps/other", "packages/common", "tools/other", ""])
def test_outbound_clients(tree: Path, module: str, base: str) -> None:
    write(tree, f"{base}/run.py".lstrip("/"), f"import {module}")
    assert any("HTTP_SALIENTE" in f for f in audit(tree))


@pytest.mark.parametrize(
    "path",
    [
        "apps/orchestrator/gateway/run.py",
        "apps/orchestrator/src/service/gateway/deep/run.py",
        "packages/common/tests/run.py",
        "tests/run.py",
        "tools/audit/fixture.py",
    ],
)
def test_http_exceptions(tree: Path, path: str) -> None:
    write(tree, path, "import httpx")
    assert audit(tree) == []


def test_exceptions_do_not_disable_other_rules(tree: Path) -> None:
    write(tree, "apps/orchestrator/agents/tests/run.py", "import psycopg")
    write(tree, "apps/companion/vision/tests/run.py", "import socket")
    assert len(audit(tree)) == 2


@pytest.mark.parametrize(
    "source",
    [
        "from urllib import request as r",
        "from http import client",
        "import importlib as il\nil.import_module('httpx')",
        "from importlib import import_module as load\nload('httpx')",
    ],
)
def test_import_variants(tree: Path, source: str) -> None:
    write(tree, "packages/common/run.py", source)
    assert any("HTTP_SALIENTE" in f for f in audit(tree))


def test_relative_persistence(tree: Path) -> None:
    write(
        tree,
        "apps/orchestrator/src/coalsense_orchestrator/agents/run.py",
        "from .. import persistence",
    )
    assert any("BD_AGENTES" in f for f in audit(tree))


def test_clean_source(tree: Path) -> None:
    write(
        tree,
        "apps/orchestrator/agents/run.py",
        "import json, httpx_helpers\nfrom urllib import parse\n"
        "# import requests\ntext = 'import httpx'\n__import__(variable)\n",
    )
    assert audit(tree) == []


def test_syntax_failure_is_private(tree: Path) -> None:
    write(tree, "packages/common/run.py", "PRIVATE_USER_TEXT = (")
    findings = audit(tree)
    assert len(findings) == 1 and "ENTRADA" in findings[0]
    assert "PRIVATE_USER_TEXT" not in findings[0]


@pytest.mark.parametrize("data", ["not json PRIVATE_USER_TEXT", "{}", '{"rules": []}'])
def test_invalid_policy(tree: Path, data: str) -> None:
    (tree / "tools/audit/forbidden_imports.yaml").write_text(data, encoding="utf-8")
    findings = audit(tree)
    assert len(findings) == 1 and "ENTRADA" in findings[0]
    assert "PRIVATE_USER_TEXT" not in findings[0]


def test_policy_drives_globs_and_modules(tree: Path) -> None:
    path = tree / "tools/audit/forbidden_imports.yaml"
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["rules"][0]["paths"] = ["packages/*/private/**/*.py"]
    policy["rules"][0]["modules"] = ["custom_network"]
    path.write_text(json.dumps(policy), encoding="utf-8")
    write(tree, "packages/common/private/run.py", "import custom_network.child")
    assert len(audit(tree)) == 1


@pytest.mark.integration
def test_repository_smoke() -> None:
    assert audit(Path(__file__).resolve().parents[3]) == []


def test_main_exit_status_and_output(
    tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from coalsense_audit import imports

    fake_module = tree / "tools/audit/src/coalsense_audit/imports.py"
    monkeypatch.setattr(imports, "__file__", str(fake_module))
    assert imports.main() == 0
    assert capsys.readouterr().out == ""
    write(tree, "packages/common/run.py", "\nimport httpx\n")
    assert imports.main() == 1
    assert capsys.readouterr().out == (
        "packages/common/run.py:2: HTTP_SALIENTE: Importación prohibida en esta ubicación.\n"
    )


def test_missing_policy_fails(tree: Path) -> None:
    (tree / "tools/audit/forbidden_imports.yaml").unlink()
    assert any("ENTRADA" in f for f in audit(tree))


def test_similar_gateway_path_is_not_exempt(tree: Path) -> None:
    write(tree, "packages/common/gateway/run.py", "import httpx")
    write(tree, "apps/orchestrator/gateway_helpers/run.py", "import requests")
    assert len(audit(tree)) == 2


def test_diagnostics_never_echo_dynamic_literal(tree: Path) -> None:
    write(tree, "packages/common/run.py", '__import__("httpx.PRIVATE_USER_TEXT")')
    result = audit(tree)
    assert len(result) == 1 and "PRIVATE_USER_TEXT" not in result[0]
