"""Offline AST import audit. Policy is the JSON subset of YAML; no code is executed."""

import ast
import json
import os
import sys
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path

POLICY = "tools/audit/forbidden_imports.yaml"


@dataclass(frozen=True)
class Rule:
    id: str
    paths: list[str]
    exclude: list[str]
    modules: list[str]


def matches(path: str, pattern: str) -> bool:
    """Root-relative, case-sensitive globs: ** matches zero or more path segments."""
    parts, glob = path.split("/"), pattern.split("/")

    @cache
    def match(i: int, j: int) -> bool:
        if j == len(glob):
            return i == len(parts)
        if glob[j] == "**":
            return match(i, j + 1) or (i < len(parts) and match(i + 1, j))
        return i < len(parts) and fnmatchcase(parts[i], glob[j]) and match(i + 1, j + 1)

    return match(0, 0)


def read_policy(root: Path) -> list[Rule]:
    data = json.loads((root / POLICY).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"rules"}:
        raise ValueError
    if not isinstance(data["rules"], list) or not data["rules"]:
        raise ValueError
    rules = []
    for item in data["rules"]:
        if not isinstance(item, dict) or set(item) != {"id", "paths", "exclude", "modules"}:
            raise ValueError
        name = item["id"]
        if (
            not isinstance(name, str)
            or not name
            or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789" for c in name)
        ):
            raise ValueError
        for key in ("paths", "exclude", "modules"):
            values = item[key]
            if not isinstance(values, list) or (key != "exclude" and not values):
                raise ValueError
            if any(not isinstance(v, str) or not v or not v.isprintable() for v in values):
                raise ValueError
        rules.append(Rule(**item))
    return rules


def package_parts(path: str) -> list[str]:
    """Resolve relative imports in src-layout and conventional Python packages."""
    parts = path.split("/")[:-1]
    if "src" in parts:
        return parts[parts.index("src") + 1 :]
    if parts and parts[0] in {"apps", "packages"}:
        return parts[2:]
    return parts


def imports(tree: ast.AST, path: str) -> Iterator[tuple[int, str]]:
    # Include straightforward importlib aliases without executing or importing anything.
    libraries = {"importlib"}
    loaders = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            libraries.update(a.asname or a.name for a in node.names if a.name == "importlib")
        elif isinstance(node, ast.ImportFrom) and node.module == "importlib" and not node.level:
            loaders.update(a.asname or a.name for a in node.names if a.name == "import_module")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package_parts(path)
                prefix = parts[: len(parts) - node.level + 1]
                base = ".".join(prefix + ([base] if base else []))
            if base:
                yield node.lineno, base
            for alias in node.names:
                if alias.name != "*":
                    yield node.lineno, ".".join(filter(None, (base, alias.name)))
        elif isinstance(node, ast.Call):
            func = node.func
            recognized = isinstance(func, ast.Name) and func.id in loaders
            recognized |= (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in libraries
                and func.attr == "import_module"
            )
            argument = (
                node.args[0]
                if node.args
                else next((kw.value for kw in node.keywords if kw.arg == "name"), None)
            )
            if (
                recognized
                and isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
            ):
                yield node.lineno, argument.value


def audit(root: Path) -> list[str]:
    findings: set[str] = set()

    def finding(path: str, line: int, rule: str, message: str) -> None:
        safe_path = path.encode("unicode_escape").decode("ascii")
        findings.add(f"{safe_path}:{line}: {rule}: {message}")

    try:
        rules = read_policy(root)
    except (OSError, ValueError, TypeError, KeyError):
        finding(POLICY, 1, "ENTRADA", "No se pudo leer o validar la política de importaciones.")
        return sorted(findings)

    def walk_error(error: OSError) -> None:
        finding(".", 1, "ENTRADA", "No se pudo recorrer el árbol de fuentes.")

    for directory, dirs, files in os.walk(root, onerror=walk_error, followlinks=False):
        dirs[:] = sorted(
            d
            for d in dirs
            if not d.startswith(".")
            and d not in {"node_modules", "__pycache__", "venv", "dist", "build"}
        )
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            source = Path(directory) / name
            path = source.relative_to(root).as_posix()
            active = [
                r
                for r in rules
                if any(matches(path, p) for p in r.paths)
                and not any(matches(path, p) for p in r.exclude)
            ]
            if not active:
                continue
            try:
                if source.is_symlink():
                    raise ValueError
                with tokenize.open(source) as stream:
                    tree = ast.parse(stream.read())
            except (OSError, SyntaxError, ValueError, UnicodeError, LookupError) as error:
                line = (error.lineno or 1) if isinstance(error, SyntaxError) else 1
                finding(path, line, "ENTRADA", "No se pudo leer o analizar el archivo Python.")
                continue
            for line, module in imports(tree, path):
                for rule in active:
                    if any(module == m or module.startswith(m + ".") for m in rule.modules):
                        finding(path, line, rule.id, "Importación prohibida en esta ubicación.")
    return sorted(findings)


def main() -> int:
    findings = audit(Path(__file__).resolve().parents[4])
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
