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
        "# import requests\ntext = 'import httpx'\n",
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
        "packages/common/run.py:2: HTTP_SALIENTE: Importación prohibida en esta ubicación: httpx.\n"
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


ADAPTER = "apps/companion/src/coalsense_companion/adapters/voice/run.py"


@pytest.mark.parametrize(
    "module",
    [
        "ssl",
        "ftplib",
        "smtplib",
        "socketserver",
        "asyncio",
        "asyncio.streams",
        "selectors",
        "multiprocessing.connection",
        "urllib3",
        "httpcore",
        "grpc",
        "paho.mqtt",
        "zmq",
        "numpy",
    ],
)
def test_vision_voice_allowlist_rejects(tree: Path, module: str) -> None:
    write(tree, ADAPTER, f"import {module}")
    assert any(f"{ADAPTER}:1: RED_PRIVADA:" in f for f in audit(tree))


@pytest.mark.parametrize(
    "path", ["apps/companion/vision.py", "apps/companion/src/x/adapters/voice.py"]
)
def test_module_files_are_covered(tree: Path, path: str) -> None:
    write(tree, path, "import ssl")
    assert any("RED_PRIVADA" in f for f in audit(tree))


def test_vision_voice_allows_stdlib_own_and_relative(tree: Path) -> None:
    write(
        tree,
        ADAPTER,
        "from __future__ import annotations\n"
        "import json, dataclasses\nfrom pathlib import Path\nimport email.message\n"
        "from coalsense_common import ids\nfrom . import helper\nfrom ..bus import Bus\n",
    )
    assert audit(tree) == []


def test_reviewed_third_party_allowlist(tree: Path) -> None:
    path = tree / "tools/audit/forbidden_imports.yaml"
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["rules"][0]["allowed"] = [{"module": "numpy", "reason": "arrays"}]
    path.write_text(json.dumps(policy), encoding="utf-8")
    write(tree, ADAPTER, "import numpy.linalg\n")
    assert audit(tree) == []
    write(tree, ADAPTER, "import numpy.linalg\nimport cv2\n")
    assert len(audit(tree)) == 1


def test_denied_module_beats_allowed_entry(tree: Path) -> None:
    path = tree / "tools/audit/forbidden_imports.yaml"
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["rules"][0]["allowed"] = [{"module": "requests", "reason": "x"}]
    path.write_text(json.dumps(policy), encoding="utf-8")
    write(tree, ADAPTER, "import requests")
    assert any("RED_PRIVADA" in f for f in audit(tree))


@pytest.mark.parametrize(
    "module", ["urllib3", "httpcore", "grpc", "websocket", "pycurl", "socket", "websocket.client"]
)
def test_extended_outbound_clients(tree: Path, module: str) -> None:
    write(tree, "packages/common/run.py", f"import {module}")
    assert any("HTTP_SALIENTE" in f for f in audit(tree))


@pytest.mark.parametrize(
    "source",
    [
        "__import__(name)",
        '__import__("so" + "cket")',
        "import importlib\nimportlib.import_module(name)",
        "import importlib as il\nil.import_module(*args)",
        "from importlib import import_module\nimport_module(name)",
        "import builtins\nbuiltins.__import__(name)",
        "import builtins as b\nb.__import__(name)",
        "from builtins import __import__ as imp\nimp(name)",
        "f = __import__\nf(name)",
        "import importlib\nf = importlib.import_module",
        "exec(code)",
        "eval(code)",
        "import importlib\nimportlib.import_module('.socket', package=__name__)",
    ],
)
@pytest.mark.parametrize(
    ("path", "rule"),
    [
        ("apps/orchestrator/agents/run.py", "BD_AGENTES"),
        (ADAPTER, "RED_PRIVADA"),
        ("packages/common/run.py", "HTTP_SALIENTE"),
    ],
)
def test_dynamic_imports_are_flagged(tree: Path, source: str, path: str, rule: str) -> None:
    write(tree, path, source)
    assert any(f"{path}:" in f and f": {rule}: " in f for f in audit(tree))


def test_dynamic_import_exempt_where_rule_excluded(tree: Path) -> None:
    write(tree, "packages/common/tests/run.py", "exec(code)")
    write(tree, "apps/orchestrator/gateway/run.py", "__import__(name)")
    assert audit(tree) == []


@pytest.mark.parametrize(
    "source",
    [
        "def f():\n    import httpx\n",
        "try:\n    import httpx\nexcept ImportError:\n    httpx = None\n",
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import httpx\n",
        "import urllib.request as c",
        "async def f():\n    from httpx import AsyncClient\n",
        "class A:\n    def m(self):\n        __import__('httpx')\n",
    ],
)
def test_nested_import_forms(tree: Path, source: str) -> None:
    write(tree, "packages/common/run.py", source)
    assert any("HTTP_SALIENTE" in f for f in audit(tree))


@pytest.mark.parametrize("hidden", ["build", "dist", "venv", ".hidden"])
def test_nested_special_dirs_are_scanned(tree: Path, hidden: str) -> None:
    path = f"apps/companion/src/coalsense_companion/adapters/vision/{hidden}/x.py"
    write(tree, path, "import socket")
    assert any(f"{path}:1: RED_PRIVADA:" in f for f in audit(tree))


def test_package_root_build_and_tool_dirs_are_pruned(tree: Path) -> None:
    write(tree, "packages/common/pyproject.toml", "")
    write(tree, "packages/common/build/lib/run.py", "import httpx")
    write(tree, "packages/common/dist/run.py", "import httpx")
    for tool in (".venv", "node_modules", "__pycache__", ".mypy_cache", ".turbo", ".git"):
        write(tree, f"packages/common/{tool}/run.py", "import httpx")
    assert audit(tree) == []
    write(tree, "packages/common/src/build/run.py", "import httpx")
    assert len(audit(tree)) == 1


def test_message_names_denied_module_only(tree: Path) -> None:
    write(tree, ADAPTER, "import ssl\nimport PRIVATE_USER_TEXT\n")
    result = audit(tree)
    assert any(
        f.endswith("RED_PRIVADA: Importación prohibida en esta ubicación: ssl.") for f in result
    )
    assert not any("PRIVATE_USER_TEXT" in f for f in result)


def test_root_hidden_tooling_dirs_are_pruned_but_github_is_scanned(tree: Path) -> None:
    write(tree, ".claude/skills/x/run.py", "import httpx")
    write(tree, ".agents/run.py", "import httpx")
    assert audit(tree) == []
    write(tree, ".github/scripts/run.py", "import httpx")
    assert any(f.startswith(".github/scripts/run.py:1: HTTP_SALIENTE") for f in audit(tree))


def test_builtins_literal_import_is_checked(tree: Path) -> None:
    write(tree, "packages/common/run.py", 'import builtins\nbuiltins.__import__("httpx")\n')
    assert any("HTTP_SALIENTE" in f for f in audit(tree))
