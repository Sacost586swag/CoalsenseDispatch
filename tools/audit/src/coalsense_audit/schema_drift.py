"""Regenera en memoria los tipos y esquemas embebidos; la deriva falla la CI."""

import subprocess
import sys
from pathlib import Path


def audit(root: Path) -> list[str]:
    generator = root / "packages/intents/gen/generate.py"
    if not generator.is_file():
        return ["packages/intents: SCHEMA_DRIFT: Falta el generador de tipos."]
    try:
        result = subprocess.run(
            [sys.executable, str(generator), "--check"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ["packages/intents: SCHEMA_DRIFT: No se pudo verificar el contrato."]
    if result.returncode:
        return ["packages/intents: SCHEMA_DRIFT: Regenera los tipos y esquemas embebidos."]
    return []


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    findings = audit(root)
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
