"""Spanish catalog and visible JSX copy audit, without evaluating source code."""

import ast
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

POLICY = "tools/audit/forbidden_words.yaml"
TS_CATALOG = "packages/ui/src/i18n/es.ts"
PY_CATALOG = "packages/common-py/src/coalsense_common/i18n_es.py"


def normalize(text: str) -> str:
    return " ".join(
        "".join(
            c for c in unicodedata.normalize("NFD", text.casefold()) if not unicodedata.combining(c)
        ).split()
    )


def audit(root: Path) -> list[str]:
    findings: list[str] = []
    try:
        policy = json.loads((root / POLICY).read_text(encoding="utf-8"))
        if (
            not isinstance(policy, dict)
            or set(policy) != {"words"}
            or not isinstance(policy["words"], list)
            or not policy["words"]
            or not all(isinstance(w, str) and w.strip() for w in policy["words"])
        ):
            raise ValueError("Política inválida")
        patterns = [
            re.compile(r"(?<!\w)" + re.escape(normalize(w)) + r"(?!\w)") for w in policy["words"]
        ]
    except (OSError, ValueError):
        return [f"{POLICY}:1: ENTRADA: No se pudo leer o validar la política."]

    def check(path: str, line: int, value: str) -> None:
        if any(pattern.search(normalize(value)) for pattern in patterns):
            findings.append(f"{path}:{line}: PALABRA_PROHIBIDA: Revisar el texto del catálogo.")

    py_values: dict[str, str] = {}
    try:
        tree = ast.parse((root / PY_CATALOG).read_text(encoding="utf-8"))
        catalogs = [
            n.value
            for n in tree.body
            if (
                isinstance(n, ast.AnnAssign)
                and isinstance(n.target, ast.Name)
                and n.target.id == "es"
            )
            or (
                isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "es" for t in n.targets)
            )
        ]
        if len(catalogs) != 1 or not isinstance(catalogs[0], ast.Dict):
            raise ValueError("Falta catálogo literal")
        for key, value in zip(catalogs[0].keys, catalogs[0].values, strict=True):
            if (
                not isinstance(key, ast.Constant)
                or not isinstance(key.value, str)
                or not isinstance(value, ast.Constant)
                or not isinstance(value.value, str)
                or key.value in py_values
            ):
                raise ValueError("Entrada inválida o duplicada")
            py_values[key.value] = value.value
            check(PY_CATALOG, value.lineno, value.value)
    except (OSError, ValueError, SyntaxError):
        findings.append(f"{PY_CATALOG}:1: ENTRADA: No se pudo leer o validar el catálogo.")

    files: list[dict[str, str | bool]] = []
    try:
        files.append(
            {
                "path": TS_CATALOG,
                "source": (root / TS_CATALOG).read_text(encoding="utf-8"),
                "catalog": True,
            }
        )
    except (OSError, UnicodeError):
        findings.append(f"{TS_CATALOG}:1: ENTRADA: No se pudo leer el catálogo.")
    # Walk only the two specified source roots; unreadable files are findings (fail closed).
    for base in ("apps/web/src", "packages/ui/src"):
        for directory, dirs, names in os.walk(root / base, followlinks=False):
            dirs[:] = sorted(
                d
                for d in dirs
                if d not in {"i18n", "node_modules"} and not (Path(directory) / d).is_symlink()
            )
            for name in sorted(names):
                path = Path(directory) / name
                if path.suffix != ".tsx" or path.is_symlink():
                    continue
                try:
                    files.append(
                        {
                            "path": path.relative_to(root).as_posix(),
                            "source": path.read_text(encoding="utf-8"),
                            "catalog": False,
                        }
                    )
                except (OSError, UnicodeError):
                    rel = path.relative_to(root).as_posix()
                    findings.append(f"{rel}:1: ENTRADA: No se pudo leer el archivo.")
    try:
        result = subprocess.run(
            ["node", str(Path(__file__).with_name("copy_ast.mjs"))],
            input=json.dumps(files),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=True,
        )
        output = json.loads(result.stdout)
        findings.extend(output["findings"])
        ts_values: dict[str, str] = {}
        for entry in output["catalog"]:
            key, value = entry["key"], entry["value"]
            if key in ts_values:
                findings.append(f"{TS_CATALOG}:{entry['line']}: ENTRADA: Clave duplicada.")
            ts_values[key] = value
            check(TS_CATALOG, entry["line"], value)
        if not ts_values or ts_values != py_values:
            findings.append(
                f"{TS_CATALOG}:1: CATALOGO: Los catálogos deben coincidir y no estar vacíos."
            )
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        findings.append("tools/audit:1: ENTRADA: No se pudo ejecutar el analizador TypeScript.")
    return sorted(set(findings))


def main() -> int:
    findings = audit(Path(__file__).resolve().parents[4])
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
