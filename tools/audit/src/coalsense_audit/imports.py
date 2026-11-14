"""Offline AST import audit. Policy is the JSON subset of YAML; no code is executed."""

import ast
import json
import os
import sys
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path

POLICY = "tools/audit/forbidden_imports.yaml"
REQUIRED = {"id", "paths", "exclude", "modules"}
OPTIONAL = {"allowlist", "allowed", "own_prefixes", "forbid_dynamic", "forbid_calls"}
# Never source: tooling caches and environments. build/dist are pruned only at package roots.
PRUNED = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".turbo",
}
ROOT_PRUNED = {"build", "dist"}
ROOT_MARKERS = {"pyproject.toml", "package.json"}
EXECUTORS = {"exec", "eval"}
OS_MODULES = {"os", "posix", "nt"}


def process_call(name: str) -> bool:
    """os attributes that run programs or replace the process."""
    return name in {"system", "popen", "startfile"} or name.startswith(
        ("exec", "spawn", "posix_spawn")
    )


@dataclass(frozen=True)
class Rule:
    id: str
    paths: list[str]
    exclude: list[str]
    modules: list[str]  # denied even when stdlib or explicitly allowed
    allowlist: bool = False  # True: reject anything not stdlib, own package or in `allowed`
    allowed: list[str] = field(default_factory=list)  # reviewed third-party modules
    own_prefixes: list[str] = field(default_factory=list)
    forbid_dynamic: bool = False  # flag non-literal dynamic imports and exec/eval
    forbid_calls: bool = False  # flag os.system/popen/exec*/spawn* and friends


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


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.isprintable()


def read_policy(root: Path) -> list[Rule]:
    data = json.loads((root / POLICY).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"rules"}:
        raise ValueError
    if not isinstance(data["rules"], list) or not data["rules"]:
        raise ValueError
    rules = []
    for item in data["rules"]:
        if not isinstance(item, dict) or not REQUIRED <= set(item) <= REQUIRED | OPTIONAL:
            raise ValueError
        name = item["id"]
        if not text(name) or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789" for c in name):
            raise ValueError
        for key in ("paths", "exclude", "modules", "own_prefixes"):
            values = item.get(key, [])
            if not isinstance(values, list) or (key in {"paths", "modules"} and not values):
                raise ValueError
            if not all(text(v) for v in values):
                raise ValueError
        allowed = item.get("allowed", [])
        if not isinstance(allowed, list) or not all(
            isinstance(a, dict) and set(a) == {"module", "reason"} and all(map(text, a.values()))
            for a in allowed
        ):
            raise ValueError
        for flag in ("allowlist", "forbid_dynamic", "forbid_calls"):
            if not isinstance(item.get(flag, False), bool):
                raise ValueError
        rules.append(
            Rule(
                id=name,
                paths=item["paths"],
                exclude=item["exclude"],
                modules=item["modules"],
                allowlist=item.get("allowlist", False),
                allowed=[a["module"] for a in allowed],
                own_prefixes=item.get("own_prefixes", []),
                forbid_dynamic=item.get("forbid_dynamic", False),
                forbid_calls=item.get("forbid_calls", False),
            )
        )
    return rules


def package_parts(path: str) -> list[str]:
    """Resolve relative imports in src-layout and conventional Python packages."""
    parts = path.split("/")[:-1]
    if "src" in parts:
        return parts[parts.index("src") + 1 :]
    if parts and parts[0] in {"apps", "packages"}:
        return parts[2:]
    return parts


def imports(tree: ast.AST, path: str) -> Iterator[tuple[int, str, str]]:
    """Yield (line, module, kind): abs, rel (resolved relative), dyn (not statically known)
    or call (process execution)."""
    # Include straightforward importlib/builtins aliases without executing anything.
    libraries = {"importlib", "builtins", "__builtins__"}
    oslibs = set(OS_MODULES)
    loaders = {"__import__"}
    nodes = list(ast.walk(tree))
    for node in nodes:
        if isinstance(node, ast.Import):
            libraries.update(
                a.asname or a.name for a in node.names if a.name in {"importlib", "builtins"}
            )
            oslibs.update(a.asname or a.name for a in node.names if a.name in OS_MODULES)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            wanted = {"importlib": "import_module", "builtins": "__import__"}.get(node.module or "")
            loaders.update(a.asname or a.name for a in node.names if a.name == wanted)
    callees = {id(n.func) for n in nodes if isinstance(n, ast.Call)}

    def is_loader(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return isinstance(node.ctx, ast.Load) and (node.id in loaders or node.id in EXECUTORS)
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in libraries
            and node.attr in {"import_module", "__import__", "exec", "eval"}
        )

    def os_attribute(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in oslibs
            and process_call(node.attr)
        )

    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name, "abs"
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            kind = "abs"
            if node.level:
                kind = "rel"
                parts = package_parts(path)
                prefix = parts[: max(0, len(parts) - node.level + 1)]
                base = ".".join(prefix + ([base] if base else []))
            if base:
                yield node.lineno, base, kind
                for alias in node.names:
                    if alias.name != "*":
                        yield node.lineno, f"{base}.{alias.name}", kind
            if node.module in OS_MODULES and not node.level:
                for alias in node.names:
                    if process_call(alias.name):
                        yield node.lineno, "", "call"
        elif isinstance(node, ast.Call) and is_loader(node.func):
            argument = (
                node.args[0]
                if node.args
                else next((kw.value for kw in node.keywords if kw.arg == "name"), None)
            )
            name = (
                node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            )
            if (
                name not in EXECUTORS
                and isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
                and not argument.value.startswith(".")
            ):
                yield node.lineno, argument.value, "abs"
            else:
                yield node.lineno, "", "dyn"
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in libraries
        ):  # getattr(builtins, name) reaches __import__/exec without naming them
            yield node.lineno, "", "dyn"
        elif isinstance(node, ast.Attribute) and os_attribute(node):
            yield node.lineno, "", "call"
        elif is_loader(node) and id(node) not in callees:  # alias such as `f = __import__`
            yield getattr(node, "lineno", 1), "", "dyn"


def verdict(rule: Rule, module: str, kind: str) -> str | None:
    if kind == "call":
        if not rule.forbid_calls:
            return None
        return "Llamada de ejecución o proceso prohibida en esta ubicación."
    if kind == "dyn":
        return "Importación dinámica no literal en esta ubicación." if rule.forbid_dynamic else None
    hit = next((m for m in rule.modules if module == m or module.startswith(m + ".")), None)
    if hit:
        return f"Importación prohibida en esta ubicación: {hit}."
    top = module.split(".")[0]
    if (
        rule.allowlist
        and kind == "abs"
        and top not in sys.stdlib_module_names
        and not top.startswith(tuple(rule.own_prefixes))
        and not any(module == a or module.startswith(a + ".") for a in rule.allowed)
    ):
        # The unknown name comes from source, so it is deliberately not echoed.
        return "Importación fuera de la lista permitida en esta ubicación."
    return None


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
        package_root = bool(ROOT_MARKERS & set(files))
        at_root = Path(directory) == root
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in PRUNED
            and not (package_root and d in ROOT_PRUNED)
            # Root-level hidden dirs are tooling (agents, vendored skills), except CI scripts.
            and not (at_root and d.startswith(".") and d != ".github")
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
            for line, module, kind in imports(tree, path):
                for rule in active:
                    if message := verdict(rule, module, kind):
                        finding(path, line, rule.id, message)
    return sorted(findings)


def main() -> int:
    findings = audit(Path(__file__).resolve().parents[4])
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
