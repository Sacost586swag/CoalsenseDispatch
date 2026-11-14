"""REQ-00-001: un checkout limpio instala las dependencias de JS y Python desde los lockfiles."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# Sin red no se puede instalar: se omite con motivo explícito, nunca en silencio.
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("COALSENSE_SKIP_NETWORK_TESTS") == "1",
        reason="COALSENSE_SKIP_NETWORK_TESTS=1: sin red, pnpm/uv no pueden descargar paquetes",
    ),
]


def _run(cmd: list[str], cwd: Path) -> None:
    exe = shutil.which(cmd[0])
    assert exe, f"{cmd[0]} no está en el PATH"
    # CI=true: pnpm no debe pedir confirmaciones interactivas.
    env = {**os.environ, "CI": "true"}
    result = subprocess.run(
        [exe, *cmd[1:]], cwd=cwd, env=env, capture_output=True, text=True, timeout=600
    )
    assert result.returncode == 0, (
        f"{' '.join(cmd)} salió con {result.returncode}\n{result.stdout}\n{result.stderr}"
    )


def test_clean_checkout_installs_with_frozen_lockfiles(tmp_path: Path) -> None:
    # Clona HEAD: lo no commiteado no cuenta como checkout limpio.
    checkout = tmp_path / "checkout"
    _run(["git", "clone", "--quiet", "--no-hardlinks", str(REPO_ROOT), str(checkout)], tmp_path)

    # pnpm y uv buscan manifiestos en los directorios padre: sin esto un checkout
    # incompleto pasaría usando archivos ajenos.
    for name in ("package.json", "pnpm-lock.yaml", "pyproject.toml", "uv.lock"):
        assert (checkout / name).is_file(), f"{name} no está commiteado en HEAD"

    _run(["pnpm", "install", "--frozen-lockfile"], checkout)
    _run(["uv", "sync", "--frozen"], checkout)
