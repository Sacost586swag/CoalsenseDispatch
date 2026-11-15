"""All audit inputs and generated outputs are isolated in tmp_path."""

import json
from pathlib import Path

import pytest
from coalsense_audit.traceability import (
    audit,
    forbidden_terms,
    generate,
    glossary,
    glossary_terms,
    main,
    normalize,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def policy(
    *terms: str,
    exclude: tuple[str, ...] = ("tarea",),
    exceptions: list[dict[str, str]] | None = None,
) -> str:
    return json.dumps(
        {
            "forbidden": [{"term": t, "canonical": "c", "reason": "r"} for t in terms],
            "excluded": [{"rule": "b", "reason": "r", "terms": list(exclude)}],
            "exceptions": exceptions or [],
        }
    )


def put(root: Path, name: str, value: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return path


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    put(
        tmp_path,
        ".kiro/specs/GLOSARIO.md",
        "| Término | No usar |\n| --- | --- |\n"
        "| persona | usuario, modo autónomo, tarea (en ese contexto) |\n",
    )
    put(tmp_path, "tools/audit/glossary_forbidden.yaml", policy("usuario", "Modo autónomo"))
    put(
        tmp_path,
        ".kiro/specs/00-demo/requirements.md",
        "- **REQ-00-001** Texto. Prueba: `a11y` y `e2e`.\n",
    )
    put(
        tmp_path,
        ".kiro/specs/00-demo/tasks.md",
        "### T-00-001 Ejemplo\n- **Requisitos:** REQ-00-001\n"
        "- **Qué hacer:** extraer `Prueba:`.\n"
        "- **Prueba:** `tests/test_a.py` (e2e) y `test_b.ts` (a11y).\n",
    )
    return tmp_path


def test_exact_format_and_modes(tree: Path) -> None:
    expected = (
        "# Trazabilidad: requisito → tarea → prueba\n\n"
        "Generado a partir de los `requirements.md` y `tasks.md` de cada spec. "
        "La auditoría `tools/audit/audit_traceability.py` (tarea T-00-006) lo regenera "
        "y falla si un requisito queda sin tarea o sin prueba. La spec 08 es de la "
        "fase 2 y no tiene tareas del MVP.\n\n## Resumen\n\n"
        "| Spec | Requisitos | Con tarea | Tareas |\n| --- | --- | --- | --- |\n"
        "| 00-demo | 1 | 1 | 1 |\n| **Total** | **1** | **1** | **1** |\n\n"
        "Requisitos del MVP sin tarea: **0**. Tareas sin prueba: **0**.\n\n"
        "## 00-demo\n\n| Requisito | Prueba | Tareas | Archivos de prueba |\n"
        "| --- | --- | --- | --- |\n"
        "| REQ-00-001 | e2e, a11y | T-00-001 | `tests/test_a.py`<br>`test_b.ts` |\n"
    )
    target = tree / ".kiro/specs/TRAZABILIDAD.md"
    assert main(["--root", str(tree)]) == 1
    assert not target.exists()
    assert generate(tree) == (expected, [])
    assert main(["--root", str(tree), "--write"]) == 0
    assert target.read_text(encoding="utf-8") == expected
    before = target.stat().st_mtime_ns
    assert main(["--root", str(tree), "--check"]) == 0
    assert target.stat().st_mtime_ns == before
    target.write_text("stale", encoding="utf-8")
    assert main(["--root", str(tree)]) == 1
    assert target.read_text() == "stale"


@pytest.mark.parametrize("fault", ["orphan", "req-proof", "task-proof", "unknown", "duplicate"])
def test_traceability_failures(tree: Path, fault: str) -> None:
    req = tree / ".kiro/specs/00-demo/requirements.md"
    task = tree / ".kiro/specs/00-demo/tasks.md"
    if fault == "orphan":
        req.write_text(req.read_text() + "- **REQ-00-002** Texto. Prueba: `unit`.\n")
    elif fault == "req-proof":
        req.write_text("- **REQ-00-001** Texto.\n")
    elif fault == "task-proof":
        task.write_text("### T-00-001 Texto\n- **Requisitos:** REQ-00-001\n")
    elif fault == "unknown":
        task.write_text(task.read_text().replace("REQ-00-001", "REQ-00-999"))
    else:
        req.write_text(req.read_text() * 2)
    assert any("TRAZABILIDAD:" in f for f in audit(tree, write=True))


def test_table_and_phase_two(tree: Path) -> None:
    put(
        tree,
        ".kiro/specs/08-future/requirements.md",
        "| REQ-08-001 | presupuesto | `perf` |\n- **REQ-08-002** Futuro sin prueba.\n",
    )
    result, findings = generate(tree)
    assert findings == []
    assert "| 08-future (fase 2) | 2 | 0 | 0 |" in result
    assert "| REQ-08-001 | perf | fase 2 | n/a |" in result


def test_glossary_extraction_and_curated_subset(tree: Path) -> None:
    source = (
        "| No usar | Definición |\n| --- | --- |\n"
        "| cancelar (descarta un paso, no detiene), «cliente» a secas, "
        "modo autónomo | ignorado |\n"
    )
    put(tree, ".kiro/specs/GLOSARIO.md", source)
    assert glossary_terms(source) == ["cancelar", "cliente", "modo autonomo"]
    put(
        tree,
        "tools/audit/glossary_forbidden.yaml",
        policy("modo autónomo", exclude=("cancelar", "cliente")),
    )
    put(tree, ".kiro/steering/policy.md", "CANCELAR, cliente y MODO AUTONOMO.\n")
    assert glossary(tree) == [".kiro/steering/policy.md:1:modo autonomo"]


def test_plural_and_whole_word(tree: Path) -> None:
    put(tree, ".kiro/steering/policy.md", "los usuarios, usuarioX y Usuario.\n")
    assert glossary(tree) == [".kiro/steering/policy.md:1:usuario"]


@pytest.mark.parametrize(
    "bad",
    [
        '{"forbidden": []}',
        "[]",
        policy("inventado"),
        policy("usuario", "modo autónomo", exclude=("tarea", "inventado")),
        policy("usuario", "modo autónomo", exclude=("tarea", "usuario")),
        policy("usuario"),  # "modo autónomo" is in the column but neither kept nor excluded
        "{",
        '{"forbidden":[{"term":"usuario"}],"excluded":[]}',
    ],
)
def test_policy_must_match_glosario(tree: Path, bad: str) -> None:
    put(tree, "tools/audit/glossary_forbidden.yaml", bad)
    assert any("ENTRADA:" in f for f in audit(tree))


def test_policy_drift_when_glosario_gains_a_term(tree: Path) -> None:
    put(
        tree,
        ".kiro/specs/GLOSARIO.md",
        "| Término | No usar |\n| --- | --- |\n| p | usuario, modo autónomo, tarea, nuevo |\n",
    )
    assert any("sin clasificar" in f and "nuevo" in f for f in audit(tree))


def test_real_policy_matches_glosario() -> None:
    kept, exceptions = forbidden_terms(REPO_ROOT)  # raises on any drift in either direction
    data = json.loads((REPO_ROOT / "tools/audit/glossary_forbidden.yaml").read_text("utf-8"))
    column = set(glossary_terms((REPO_ROOT / ".kiro/specs/GLOSARIO.md").read_text("utf-8")))
    excluded = {normalize(t) for group in data["excluded"] for t in group["terms"]}
    assert kept and kept == sorted(set(kept)) and not set(kept) & excluded
    assert set(kept) | excluded == column
    assert exceptions and {t for _, t, _ in exceptions} <= set(kept)
    assert all((REPO_ROOT / path).is_file() for path, _, _ in exceptions)
    assert glossary(REPO_ROOT) == []


def waiver(text: str, path: str = ".kiro/specs/a.md") -> dict[str, str]:
    return {"path": path, "term": "Usuario", "text": text, "reason": "cuenta de Windows"}


def test_exception_waives_only_the_excepted_line_of_one_path(tree: Path) -> None:
    put(
        tree,
        "tools/audit/glossary_forbidden.yaml",
        policy("usuario", "modo autónomo", exceptions=[waiver("ACL al usuario actual")]),
    )
    put(tree, ".kiro/specs/a.md", "ACL al usuario actual y modo autónomo\nel usuario nuevo\n")
    put(tree, ".kiro/specs/sub/a.md", "ACL al usuario actual\n")
    put(tree, ".kiro/specs/b.md", "usuario\n")
    assert glossary(tree) == [
        ".kiro/specs/a.md:1:modo autonomo",
        ".kiro/specs/a.md:2:usuario",
        ".kiro/specs/b.md:1:usuario",
        ".kiro/specs/sub/a.md:1:usuario",
    ]


def test_stale_exception_is_a_finding(tree: Path) -> None:
    put(
        tree,
        "tools/audit/glossary_forbidden.yaml",
        policy("usuario", "modo autónomo", exceptions=[waiver("ACL al usuario actual")]),
    )
    put(tree, ".kiro/specs/a.md", "ya sin el término\n")
    assert any("excepción obsoleta" in f for f in glossary(tree))
    put(tree, ".kiro/specs/a.md", "ACL al usuario actual\n")
    assert glossary(tree) == []
    (tree / ".kiro/specs/a.md").unlink()  # path removed: stale as well
    assert any("excepción obsoleta" in f for f in glossary(tree))


@pytest.mark.parametrize(
    "bad",
    [
        {"path": "x.md", "term": "tarea", "text": "t", "reason": "r"},  # excluded, not kept
        {"path": "x.md", "term": "usuario", "text": "t", "reason": ""},
        {"path": "x.md", "term": "usuario", "text": "", "reason": "r"},
        {"path": "", "term": "usuario", "text": "t", "reason": "r"},
        {"path": "x.md", "term": "usuario", "reason": "r"},
        "x.md",
    ],
)
def test_exceptions_must_be_reviewed(tree: Path, bad: object) -> None:
    raw = json.loads(policy("usuario", "modo autónomo"))
    raw["exceptions"] = [bad]
    put(tree, "tools/audit/glossary_forbidden.yaml", json.dumps(raw))
    assert any("ENTRADA:" in f for f in audit(tree))


def test_glossary_scope_quotes_fences_and_lines(tree: Path) -> None:
    put(
        tree,
        ".kiro/specs/nested/example.md",
        '«usuario» "usuario" `usuario` ``usuario``\n'
        "```txt\nusuario\n```\n~~~\nusuario\n~~~\n"
        '    usuario\n"usuario\nusuario"\n'
        "usuarios superusuario\nUSUARIO y MÓDO AUTÓNOMO\n",
    )
    put(tree, ".kiro/steering/policy.md", "usuario\n")
    put(tree, ".kiro/steering/GLOSARIO.md", "usuario\n")
    put(tree, "apps/example.md", "usuario\n")
    # quote and inline-code spans end at the line: an unbalanced quote hides nothing
    assert glossary(tree) == [
        ".kiro/specs/nested/example.md:10:usuario",
        ".kiro/specs/nested/example.md:11:usuario",
        ".kiro/specs/nested/example.md:12:modo autonomo",
        ".kiro/specs/nested/example.md:12:usuario",
        ".kiro/specs/nested/example.md:9:usuario",
        ".kiro/steering/policy.md:1:usuario",
    ]
    assert main(["--root", str(tree), "--write"]) == 1
    assert (tree / ".kiro/specs/TRAZABILIDAD.md").exists()


@pytest.mark.parametrize("stray", ['una pantalla de 5" y', "un `acento", "«abre sin cerrar"])
def test_stray_quote_does_not_hide_later_lines(tree: Path, stray: str) -> None:
    put(tree, ".kiro/steering/policy.md", f"{stray}\n\notro párrafo\n\n- usuario\n")
    assert glossary(tree) == [".kiro/steering/policy.md:5:usuario"]


@pytest.mark.parametrize("token", ["REQ-01-0100", "REQ-01-02", "REQ-1-001", "REQ-00-0010x"])
def test_malformed_requirement_ids_are_reported(tree: Path, token: str) -> None:
    task = tree / ".kiro/specs/00-demo/tasks.md"
    task.write_text(task.read_text().replace("REQ-00-001", f"REQ-00-001, {token}"))
    findings = audit(tree, write=True)
    assert any("id mal formado" in f and token in f for f in findings)


def test_valid_requirement_list_formats_pass(tree: Path) -> None:
    task = tree / ".kiro/specs/00-demo/tasks.md"
    task.write_text(task.read_text().replace("REQ-00-001", "REQ-00-001, REQ-00-001."))
    assert audit(tree, write=True) == []


def test_missing_inputs_fail_closed(tmp_path: Path, tree: Path) -> None:
    (tree / ".kiro/specs/GLOSARIO.md").unlink()
    assert any("ENTRADA:" in f for f in audit(tree))
    assert not (tree / ".kiro/specs/TRAZABILIDAD.md").exists()
