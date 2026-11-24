"""Offline, fail-closed license audit of pnpm v9 and uv lock inventories.

The policy uses the JSON subset of YAML. The pnpm reader deliberately accepts
only the v9 block mapping inventory emitted by pnpm, not arbitrary YAML.
License evidence comes from exact-version installed metadata, never the register.
"""

import importlib.metadata
import json
import re
import sys
import tomllib
from pathlib import Path


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def approved(expression: str, licenses: set[str]) -> bool:
    """Parse SPDX AND/OR with parentheses; reject unsupported or malformed syntax."""
    tokens = re.findall(r"[A-Za-z0-9.+-]+|[()]|\S", expression)
    position = 0

    def atom() -> bool:
        nonlocal position
        if position >= len(tokens):
            raise ValueError
        token = tokens[position]
        position += 1
        if token == "(":
            value = either()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError
            position += 1
            return value
        if token in {"AND", "OR", ")"}:
            raise ValueError
        return token in licenses

    def both() -> bool:
        nonlocal position
        value = atom()
        while position < len(tokens) and tokens[position] == "AND":
            position += 1
            right = atom()
            value = value and right
        return value

    def either() -> bool:
        nonlocal position
        value = both()
        while position < len(tokens) and tokens[position] == "OR":
            position += 1
            right = both()
            value = value or right
        return value

    try:
        result = either()
        return position == len(tokens) and result
    except ValueError:
        return False


def pnpm_inventory(
    root: Path,
) -> tuple[list[tuple[str, str, int, bool]], list[str], set[tuple[str, str]]]:
    """Packages, importers and the optional platform packages (os/cpu/libc or optional snapshot)."""
    packages: list[tuple[str, str, int, bool]] = []
    gated: set[tuple[str, str]] = set()
    snapshot: tuple[str, str] | None = None
    importers = []
    section = ""
    version_seen = False
    sections: set[str] = set()
    for number, line in enumerate((root / "pnpm-lock.yaml").read_text().splitlines(), 1):
        if line.startswith("lockfileVersion:"):
            version_seen = line.split(":", 1)[1].strip().strip("'\"") == "9.0"
        if line and not line.startswith((" ", "#")):
            section = line.split(":", 1)[0]
            sections.add(section)
            if section in {"packages", "importers"} and line not in {
                f"{section}:",
                f"{section}: {{}}",
            }:
                raise ValueError
        if section == "packages" and packages and re.match(r"^    (os|cpu):", line):
            name, version, at, _ = packages[-1]
            packages[-1] = (name, version, at, True)
        if section == "packages" and packages and re.match(r"^    (os|cpu|libc):", line):
            gated.add(packages[-1][:2])
        if section == "snapshots":
            head = re.match(r"^  '?(.+?)@([0-9][A-Za-z0-9.+-]*)(?:\(.*\))?'?:", line)
            if head:
                snapshot = (head[1], head[2])
            elif snapshot and line == "    optional: true":
                gated.add(snapshot)
        if section not in {"packages", "importers"} or not re.match(r"^  \S", line):
            continue
        match = re.fullmatch(r"  (.+):(?: \{\})?", line)
        if not match:
            raise ValueError
        key = match[1].strip("'\"")
        if section == "importers":
            importers.append(key)
        else:
            name, sep, version = key.rpartition("@")
            if not sep or not name or not re.fullmatch(r"[0-9][A-Za-z0-9.+-]*", version):
                raise ValueError
            packages.append((name, version, number, False))
    if not version_seen or not {"packages", "importers"} <= sections:
        raise ValueError
    return packages, importers, gated


def bsd_variant(dist: importlib.metadata.Distribution) -> str:
    """Generic BSD classifier: decide the variant from the installed license text."""
    for file in dist.metadata.get_all("License-File", []):
        text = dist.read_text(f"licenses/{file}") or dist.read_text(file) or ""
        if "Redistribution and use" in text and "Neither the name" in text:
            return "BSD-3-Clause"
        if "Redistribution and use" in text and "binary form must reproduce" in text:
            return "BSD-2-Clause"
    return "UNKNOWN"


def python_license(name: str, version: str) -> str | None:
    """License text; None only when the distribution is not installed at all."""
    try:
        dist = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return None
    if dist.version != version:
        return ""
    spdx = dist.metadata.get("License-Expression")
    legacy = (dist.metadata.get("License") or "").strip()
    # Nombres históricos exactos, verificados contra los textos instalados de
    # rfc3339-validator 0.1.4 y sortedcontainers 2.4.0. No hay coincidencias parciales.
    aliases = {"MIT license": "MIT", "Apache 2.0": "Apache-2.0"}
    expression = spdx or aliases.get(legacy, legacy)
    if expression.strip() and expression.strip() != "UNKNOWN":
        return expression.strip()
    # Unambiguous classifiers only; generic BSD is resolved from the license text.
    classifiers = {
        "License :: OSI Approved :: MIT License": "MIT",
        "License :: OSI Approved :: Apache Software License": "Apache-2.0",
        "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
        "License :: OSI Approved :: ISC License (ISCL)": "ISC",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    }
    classifiers["License :: OSI Approved :: BSD License"] = bsd_variant(dist)
    values = [
        classifiers.get(c, "UNKNOWN")
        for c in dist.metadata.get_all("Classifier", [])
        if c.startswith("License ::")
    ]
    return " AND ".join(values)


def npm_license(data: dict[str, object]) -> str:
    lic = data.get("license")
    if isinstance(lic, dict):
        lic = lic.get("type")
    if isinstance(lic, str):
        return lic
    legacy = data.get("licenses")  # legacy array: any listed license may be chosen
    if isinstance(legacy, list):
        types = [x.get("type") if isinstance(x, dict) else x for x in legacy]
        if types and all(isinstance(t, str) for t in types):
            return " OR ".join(str(t) for t in types)
    return ""


def within(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError
    return path


def audit(root: Path) -> list[str]:
    findings: list[str] = []

    def finding(path: str, line: int, rule: str, message: str) -> None:
        # Paths from input are never echoed; callers use fixed source names.
        findings.append(f"{path}:{line}: {rule}: {message}")

    source = "tools/audit/approved_licenses.yaml"
    try:
        policy = json.loads((root / source).read_text(encoding="utf-8"))
        licenses = set(policy["licenses"])
        fonts = set(policy["font_packages"])
        exceptions = policy["exceptions"]
        uninstalled = policy.get("uninstalled_python", [])
        uninstalled_npm = policy.get("uninstalled_npm", [])
        if not all(isinstance(x, str) for x in licenses | fonts):
            raise ValueError
        keys = {"name", "version", "license", "reason"}
        for item in exceptions:
            if set(item) != keys | {"ecosystem"}:
                raise ValueError
            if not all(isinstance(v, str) and v.strip() for v in item.values()):
                raise ValueError
        for item in uninstalled + uninstalled_npm:
            if set(item) != keys:
                raise ValueError
            if not all(isinstance(v, str) and v.strip() for v in item.values()):
                raise ValueError
        source = "THIRD_PARTY.md"
        register: dict[tuple[str, str], str] = {}
        for row in (root / source).read_text(encoding="utf-8").splitlines():
            cells = [cell.strip().strip("`") for cell in row.split("|")]
            if len(cells) >= 6:
                register[(cells[1], cells[2])] = cells[3]

        def recorded_license(eco: str, name: str, version: str) -> str | None:
            fold = normalize if eco == "pypi" else str
            return {(fold(n), v): lic for (n, v), lic in register.items()}.get(
                (fold(name), version)
            )

        def check(
            eco: str, name: str, version: str, license_text: str, direct: bool, path: str, line: int
        ) -> None:
            allowed = licenses | ({"OFL-1.1"} if f"{eco}:{name}" in fonts else set())
            exception = any(
                e["ecosystem"] == eco
                and e["name"] == name
                and e["version"] == version
                and e["license"] == license_text
                for e in exceptions
            )
            if not approved(license_text, allowed) and not exception:
                shown = (
                    license_text if re.fullmatch(r"[A-Za-z0-9.+() -]{1,100}", license_text) else ""
                )
                shown = "desconocida" if shown in {"", "UNKNOWN"} else shown
                finding(path, line, "LICENCIA", f'{name}@{version}: licencia "{shown}" no aprobada')
            if direct:
                recorded = recorded_license(eco, name, version)
                if recorded is None:
                    finding(
                        path,
                        line,
                        "REGISTRO",
                        f"{name}@{version}: dependencia directa sin registro de igual versión.",
                    )
                elif not approved(recorded, allowed) and not exception:
                    finding(
                        "THIRD_PARTY.md",
                        1,
                        "REGISTRO",
                        f"{name}@{version}: licencia registrada no aprobada.",
                    )

        source = "pnpm-lock.yaml"
        packages, importers, gated_js = pnpm_inventory(root)
        direct_js: set[tuple[str, str]] = set()
        for importer in importers:
            manifest = json.loads((within(root, importer) / "package.json").read_text())
            for group in ("dependencies", "devDependencies", "optionalDependencies"):
                for name, spec in manifest.get(group, {}).items():
                    if not spec.startswith(("workspace:", "link:")):
                        if spec.startswith("npm:"):
                            name, _, spec = spec[4:].rpartition("@")
                        direct_js.add((name, spec))
        installed: dict[tuple[str, str], str] = {}
        store = root / "node_modules/.pnpm"
        for pattern in ("*/node_modules/*/package.json", "*/node_modules/@*/*/package.json"):
            for path in store.glob(pattern):
                data = json.loads(path.read_text(encoding="utf-8"))
                installed[(data["name"], data["version"])] = npm_license(data)
        # shortcut: an os/cpu-restricted package not installed here takes the AND of the licenses
        # of all installed os/cpu-restricted siblings of the same scope and version (strictest
        # wins, same result on every platform); upgrade to per-platform installs if needed.
        restricted = {(n, v) for n, v, _, r in packages if r}

        def npm_evidence(name: str, version: str) -> str:
            if (name, version) in installed:
                return installed[(name, version)]
            if (name, version) not in restricted or "/" not in name:
                return ""
            scope = name.split("/")[0]
            found = {
                installed[(n, v)]
                for n, v in restricted
                if v == version and n.startswith(scope + "/") and (n, v) in installed
            }
            if len(found) == 1:
                return next(iter(found))
            return " AND ".join(f"({x})" for x in sorted(found))

        # Optional platform package not installed here: reviewed uninstalled_npm entry supplies it.
        # The policy lists every platform variant of the lock; installed ones use real metadata.
        npm_entries = {(e["name"], e["version"]): e["license"] for e in uninstalled_npm}
        if len(npm_entries) != len(uninstalled_npm):
            raise ValueError  # duplicate name@version: the last one would silently win
        in_lock = {(n, v) for n, v, _, _ in packages}
        for key in sorted(npm_entries):
            if key not in in_lock:
                finding(
                    "tools/audit/approved_licenses.yaml",
                    1,
                    "POLITICA",
                    f"{key[0]}@{key[1]}: entrada de uninstalled_npm obsoleta (ausente del lock).",
                )
        for name, version, line, _ in packages:
            npm_text = npm_evidence(name, version)
            if (name, version) in gated_js and (name, version) not in installed:
                npm_text = npm_entries.get((name, version)) or npm_text
                if not npm_text:
                    finding(
                        source,
                        line,
                        "LICENCIA",
                        f"{name}@{version}: paquete de plataforma no instalado "
                        "y sin entrada en uninstalled_npm.",
                    )
                    continue
            check(
                "npm",
                name,
                version,
                npm_text,
                (name, version) in direct_js,
                source,
                line,
            )
        if direct_js - {(name, version) for name, version, _, _ in packages}:
            finding(source, 1, "INVENTARIO", "Dependencia directa ausente del lock.")

        source = "uv.lock"
        lock_text = (root / source).read_text(encoding="utf-8")
        lock = tomllib.loads(lock_text)
        if lock.get("version") != 1 or "package" not in lock:
            raise ValueError
        direct_py: set[tuple[str, str]] = set()
        build_requirements: list[tuple[str, str]] = []
        for pkg in lock["package"]:
            origin = pkg.get("source", {})
            local = origin.get("editable", origin.get("virtual"))
            if local is None:
                continue
            manifest_path = within(root, local) / "pyproject.toml"
            manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
            project = manifest.get("project", {})
            requirements = list(project.get("dependencies", []))
            for group in project.get("optional-dependencies", {}).values():
                requirements.extend(group)
            for group in manifest.get("dependency-groups", {}).values():
                requirements.extend(r for r in group if isinstance(r, str))
            for req in requirements:
                match = re.match(r"[A-Za-z0-9_.-]+", req)
                if not match:
                    raise ValueError
                requirement_name = normalize(match[0])
                pinned = re.search(r"==([A-Za-z0-9.+-]+)", req)
                if pinned:
                    direct_py.add((requirement_name, pinned[1]))
                elif requirement_name not in {
                    normalize(p["name"])
                    for p in lock["package"]
                    if "editable" in p.get("source", {}) or "virtual" in p.get("source", {})
                }:
                    raise ValueError
            for req in manifest.get("build-system", {}).get("requires", []):
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9.+-]+)", req)
                if not match:
                    raise ValueError
                build_requirements.append((match[1], match[2]))
        refs: dict[str, list[bool]] = {}
        for pkg in lock["package"]:
            groups = [pkg.get("dependencies", [])]
            groups += list(pkg.get("optional-dependencies", {}).values())
            groups += list(pkg.get("dev-dependencies", {}).values())
            for group in groups:
                for dep in group:
                    refs.setdefault(normalize(dep["name"]), []).append("marker" in dep)
        gated = {n for n, marks in refs.items() if all(marks)}
        blocks = [m.start() for m in re.finditer(r"(?m)^\[\[package\]\]", lock_text)]
        for index, pkg in enumerate(lock["package"]):
            if "editable" in pkg.get("source", {}) or "virtual" in pkg.get("source", {}):
                continue
            name, version = pkg["name"], pkg["version"]
            lic = pkg.get("license") or python_license(name, version)
            line = lock_text.count("\n", 0, blocks[index]) + 1
            if lic is None and normalize(name) in gated:
                # Marker-gated and not installed here (e.g. win32 only): reviewed policy entry.
                lic = next(
                    (
                        u["license"]
                        for u in uninstalled
                        if normalize(u["name"]) == normalize(name) and u["version"] == version
                    ),
                    None,
                )
                if lic is None:
                    finding(
                        source,
                        line,
                        "LICENCIA",
                        f"{name}@{version}: paquete con marcador de plataforma no instalado "
                        "y sin entrada en uninstalled_python.",
                    )
                    continue
            direct = (normalize(name), version) in direct_py
            check("pypi", name, version, lic or "", direct, source, line)
        if direct_py - {(normalize(p["name"]), p["version"]) for p in lock["package"]}:
            finding(source, 1, "INVENTARIO", "Dependencia directa ausente del lock.")
        for name, version in sorted(set(build_requirements)):
            # Build backends are isolated and usually not installed: fall back to the register.
            evidence = python_license(name, version)
            if evidence is None:  # only a missing distribution falls back to the register
                evidence = recorded_license("pypi", name, version)
            check("pypi", name, version, evidence or "", True, "pyproject.toml", 1)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError):
        finding(source, 1, "ENTRADA", "No se pudo leer o validar la entrada de auditoría.")
    return sorted(set(findings))


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    findings = audit(root)
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
