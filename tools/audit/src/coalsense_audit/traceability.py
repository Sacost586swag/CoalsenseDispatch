"""Deterministic Markdown traceability and curated glossary audit (stdlib only).

The glossary check enforces tools/audit/glossary_forbidden.yaml, a reviewed subset
of GLOSARIO.md's "No usar" column (each entry: term, canonical, reason; generic or
contextual terms are listed under "excluded" with the rule; "exceptions" waive one
kept term on the lines of one exact file path that contain the exception's text, and
an exception that matches nothing is itself a finding). Kept plus excluded terms must
equal that column, so the list cannot drift in either direction. glossary_terms() extracts
the column: parenthesized explanations are removed before comma splitting and a
quoted term at the start of an item supplies the term. Match whole words (an
optional plural s/es is accepted) ignoring case/accents. Scan Markdown in
specs/steering, except GLOSARIO.md (case insensitive), fenced and indented code,
and paired «», double quotes or backticks; preserve line numbers.
"""

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SPECS = Path(".kiro/specs")
OUTPUT = SPECS / "TRAZABILIDAD.md"
POLICY = Path("tools/audit/glossary_forbidden.yaml")
TYPES = "unit integration contract e2e a11y security perf replay audit manual".split()
INTRO = (
    "# Trazabilidad: requisito → tarea → prueba\n\n"
    "Generado a partir de los `requirements.md` y `tasks.md` de cada spec. "
    "La auditoría `tools/audit/audit_traceability.py` (tarea T-00-006) lo regenera "
    "y falla si un requisito queda sin tarea o sin prueba. La spec 08 es de la "
    "fase 2 y no tiene tareas del MVP.\n\n## Resumen\n\n"
)


@dataclass
class Entry:
    id: str
    line: int
    body: str


def entries(source: str, pattern: str) -> list[Entry]:
    matches = list(re.finditer(pattern, source, re.M))
    return [
        Entry(
            m[1],
            source.count("\n", 0, m.start()) + 1,
            source[m.end() : matches[i + 1].start() if i + 1 < len(matches) else len(source)],
        )
        for i, m in enumerate(matches)
    ]


def field(body: str, name: str) -> str:
    match = re.search(r"^- \*\*" + name + r":\*\*[ \t]*([^\n]*)", body, re.M)
    if not match:
        match = re.search(r"(?<![`\w])" + name + r":[ \t]*([^\n]*)", body)
    return match[1] if match else ""


def proof_types(value: str) -> str:
    return ", ".join(t for t in TYPES if re.search(r"\b" + t + r"\b", value))


def generate(root: Path) -> tuple[str, list[str]]:
    findings: list[str] = []
    summaries: list[str] = []
    sections: list[str] = []
    totals = [0, 0, 0]
    orphans = untested = 0
    directories = sorted(
        p for p in (root / SPECS).iterdir() if p.is_dir() and re.match(r"^\d{2}-", p.name)
    )
    if not directories:
        raise ValueError("No hay specs")
    for directory in directories:
        future = directory.name.startswith("08-")
        req_path = directory / "requirements.md"
        task_path = directory / "tasks.md"
        req_source = req_path.read_text(encoding="utf-8")
        reqs = entries(req_source, r"^- \*\*(REQ-\d{2}-\d{3})\*\*")
        for line, text in enumerate(req_source.splitlines(), 1):
            match = re.match(r"^\| (REQ-\d{2}-\d{3}) \|", text)
            if match:
                reqs.append(Entry(match[1], line, "Prueba: " + text.split("|")[-2]))
        reqs.sort(key=lambda r: r.id)
        tasks = (
            entries(task_path.read_text(encoding="utf-8"), r"^### (T-\d{2}-\d{3})\b")
            if task_path.exists() or not future
            else []
        )
        if not reqs or (not tasks and not future):
            raise ValueError(f"{directory.name}: sin requisitos o tareas reconocibles")

        def report(path: Path, entry: Entry, reason: str) -> None:
            findings.append(
                f"{path.relative_to(root).as_posix()}:{entry.line}: "
                f"TRAZABILIDAD: {entry.id} {reason}"
            )

        for records, path in ((reqs, req_path), (tasks, task_path)):
            seen: set[str] = set()
            for record in records:
                if record.id in seen:
                    report(path, record, "duplicado")
                seen.add(record.id)
        tokens = {
            t.id: [x.rstrip(".)") for x in re.split(r"[,;\s]+", field(t.body, "Requisitos")) if x]
            for t in tasks
        }
        links = {
            k: [x for x in v if re.fullmatch(r"REQ-\d{2}-\d{3}", x)] for k, v in tokens.items()
        }
        files = {
            t.id: list(
                dict.fromkeys(
                    v
                    for v in re.findall(r"`([^`]+)`", field(t.body, "Prueba"))
                    if re.search(r"\.(?:py|tsx?|jsx?)$", v)
                )
            )
            for t in tasks
        }
        for task in tasks:
            for token in tokens[task.id]:
                if token not in links[task.id]:
                    report(task_path, task, f"id mal formado en Requisitos: {token}")
            if not links[task.id] or set(links[task.id]) - {r.id for r in reqs}:
                report(task_path, task, "referencia requisitos ausentes o desconocidos")
            if not future and (not files[task.id] or not proof_types(field(task.body, "Prueba"))):
                untested += 1
                report(task_path, task, "sin prueba")
        rows: list[str] = []
        covered = 0
        for req in reqs:
            linked = [t.id for t in tasks if req.id in links[t.id]]
            proof = proof_types(field(req.body, "Prueba"))
            covered += bool(linked)
            if not future:
                if not linked:
                    orphans += 1
                    report(req_path, req, "sin tarea")
                if not proof:
                    report(req_path, req, "sin tipo de prueba")
            paths = list(dict.fromkeys(p for t in linked for p in files[t]))
            task_cell = ", ".join(linked) or ("fase 2" if future else "—")
            file_cell = "<br>".join(f"`{p}`" for p in paths) or ("n/a" if future else "—")
            rows.append(f"| {req.id} | {proof} | {task_cell} | {file_cell} |")
        label = directory.name + (" (fase 2)" if future else "")
        summaries.append(f"| {label} | {len(reqs)} | {covered} | {len(tasks)} |")
        for i, value in enumerate((len(reqs), covered, len(tasks))):
            totals[i] += value
        sections.append(
            f"## {directory.name}\n\n"
            "| Requisito | Prueba | Tareas | Archivos de prueba |\n"
            "| --- | --- | --- | --- |\n" + "\n".join(rows)
        )
    result = INTRO + "| Spec | Requisitos | Con tarea | Tareas |\n| --- | --- | --- | --- |\n"
    result += (
        "\n".join(summaries)
        + "\n| **Total** | "
        + " | ".join(f"**{n}**" for n in totals)
        + " |\n\n"
    )
    result += f"Requisitos del MVP sin tarea: **{orphans}**. Tareas sin prueba: **{untested}**.\n\n"
    return result + "\n\n".join(sections) + "\n", findings


def normalize(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", value.casefold()) if not unicodedata.combining(c)
    )


def glossary_terms(source: str) -> list[str]:
    terms: set[str] = set()
    column: int | None = None
    for line in source.splitlines():
        if not line.startswith("|"):
            column = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if "No usar" in cells:
            column = cells.index("No usar")
            continue
        if column is None or column >= len(cells) or re.fullmatch(r"[-: ]+", cells[column]):
            continue
        cell = cells[column]
        while re.search(r"\([^()]*\)", cell):
            cell = re.sub(r"\([^()]*\)", "", cell)
        for item in cell.split(","):
            item = item.strip()
            quoted = re.match(r'^(?:«([^»]+)»|"([^"]+)"|`([^`]+)`)', item)
            if quoted:
                item = next(g for g in quoted.groups() if g is not None)
            item = item.strip("* ").strip()
            if item and item not in {"—", "-", "n/a"}:
                terms.add(normalize(item))
    if not terms:
        raise ValueError("Glosario sin términos No usar")
    return sorted(terms)


def mask(source: str) -> str:
    def blank(value: str) -> str:
        return "".join("\n" if c == "\n" else " " for c in value)

    lines = []
    fence = ""
    for line in source.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            lines.append(blank(line))
            if re.fullmatch(
                r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line
            ):
                fence = ""
        elif match:
            fence = match[1]
            lines.append(blank(line))
        elif line.startswith(("    ", "\t")):
            lines.append(blank(line))
        else:
            lines.append(line)
    return re.sub(
        r'«[^»\n]*»|"(?:\\.|[^"\\\n])*"|(`+)(?!`)[^\n]*?(?<!`)\1(?!`)',
        lambda m: blank(m[0]),
        "".join(lines),
    )


def _fields(item: object, keys: tuple[str, ...]) -> list[str]:
    return [str(item.get(k) or "").strip() if isinstance(item, dict) else "" for k in keys]


def forbidden_terms(root: Path) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Kept terms plus reviewed exceptions (path, term, text); raises on any drift."""
    where = POLICY.as_posix()
    data = json.loads((root / POLICY).read_text(encoding="utf-8"))
    listed = data.get("forbidden") if isinstance(data, dict) else None
    groups = data.get("excluded") if isinstance(data, dict) else None
    if not isinstance(listed, list) or not listed or not isinstance(groups, list):
        raise ValueError(f"{where}: faltan 'forbidden' (no vacía) o 'excluded'")
    column = set(glossary_terms((root / SPECS / "GLOSARIO.md").read_text(encoding="utf-8")))
    kept: set[str] = set()
    for entry in listed:
        fields = _fields(entry, ("term", "canonical", "reason"))
        if not all(fields):
            raise ValueError(f"{where}: entrada sin term, canonical o reason")
        kept.add(normalize(fields[0]))
    excluded: set[str] = set()
    for group in groups:
        names = group.get("terms") if isinstance(group, dict) else None
        if not all(_fields(group, ("rule", "reason"))) or not isinstance(names, list):
            raise ValueError(f"{where}: grupo excluido sin rule, reason o terms")
        excluded |= {normalize(str(n).strip()) for n in names}
    if unknown := (kept | excluded) - column:
        raise ValueError(f"{where}: no están en «No usar» de GLOSARIO.md: {sorted(unknown)}")
    if both := kept & excluded:
        raise ValueError(f"{where}: términos conservados y excluidos a la vez: {sorted(both)}")
    if missing := column - kept - excluded:
        raise ValueError(f"{where}: términos de GLOSARIO.md sin clasificar: {sorted(missing)}")
    exceptions = []
    for item in data.get("exceptions", []):
        path, term, text, reason = _fields(item, ("path", "term", "text", "reason"))
        if not all((path, term, text, reason)) or normalize(term) not in kept:
            raise ValueError(f"{where}: excepción sin path, text, reason o término conservado")
        exceptions.append((path, normalize(term), text))
    return sorted(kept), exceptions


def glossary(root: Path) -> list[str]:
    terms, exceptions = forbidden_terms(root)
    patterns = [
        (t, re.compile(r"(?<!\w)" + r"\s+".join(map(re.escape, t.split())) + r"(?:e?s)?(?!\w)"))
        for t in terms
    ]
    findings = []
    used: set[tuple[str, str, str]] = set()
    for base in (SPECS, Path(".kiro/steering")):
        for path in sorted((root / base).rglob("*.md")):
            if path.stem.casefold() == "glosario":
                continue
            raw = path.read_text(encoding="utf-8")
            source = normalize(mask(raw))
            rel = path.relative_to(root).as_posix()
            lines = raw.split("\n")
            for term, pattern in patterns:
                for match in pattern.finditer(source):
                    line = source.count("\n", 0, match.start()) + 1
                    # reviewed exception: exact path + term + text of the excepted line
                    waiver = next(
                        (e for e in exceptions if e[:2] == (rel, term) and e[2] in lines[line - 1]),
                        None,
                    )
                    if waiver:
                        used.add(waiver)
                    else:
                        findings.append(f"{rel}:{line}:{term}")
    findings += [
        f"{POLICY.as_posix()}:1:excepción obsoleta: {p} {t} «{x}»"
        for p, t, x in exceptions
        if (p, t, x) not in used
    ]
    return sorted(set(findings))


def audit(root: Path, *, write: bool = False) -> list[str]:
    try:
        generated, findings = generate(root)
        findings.extend(glossary(root))
        if write:
            (root / OUTPUT).write_text(generated, encoding="utf-8", newline="\n")
        elif (
            not (root / OUTPUT).exists() or (root / OUTPUT).read_text(encoding="utf-8") != generated
        ):
            findings.append(f"{OUTPUT.as_posix()}:1: DESACTUALIZADO: regenerar con --write")
        return sorted(set(findings))
    except (OSError, UnicodeError, ValueError, KeyError, AttributeError) as exc:
        return [f"{SPECS.as_posix()}:1: ENTRADA: {exc}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="default; never write")
    mode.add_argument("--write", action="store_true", help="write generated traceability")
    args = parser.parse_args(argv)
    findings = audit(args.root.resolve(), write=args.write)
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
