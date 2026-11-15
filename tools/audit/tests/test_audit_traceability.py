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


def policy(*terms: str) -> str:
    return json.dumps({"forbidden": [{"term": t, "canonical": "c", "reason": "r"} for t in terms]})


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
    put(tree, "tools/audit/glossary_forbidden.yaml", policy("modo autónomo"))
    put(tree, ".kiro/steering/policy.md", "CANCELAR, cliente y MODO AUTONOMO.\n")
    assert glossary(tree) == [".kiro/steering/policy.md:1:modo autonomo"]


def test_plural_and_whole_word(tree: Path) -> None:
    put(tree, ".kiro/steering/policy.md", "los usuarios, usuarioX y Usuario.\n")
    assert glossary(tree) == [".kiro/steering/policy.md:1:usuario"]


@pytest.mark.parametrize(
    "bad",
    ['{"forbidden": []}', "[]", policy("inventado"), "{", '{"forbidden":[{"term":"usuario"}]}'],
)
def test_policy_must_be_honest(tree: Path, bad: str) -> None:
    put(tree, "tools/audit/glossary_forbidden.yaml", bad)
    assert any("ENTRADA:" in f for f in audit(tree))


def test_real_policy_is_subset_of_glosario() -> None:
    listed = forbidden_terms(REPO_ROOT)
    data = json.loads((REPO_ROOT / "tools/audit/glossary_forbidden.yaml").read_text("utf-8"))
    column = set(glossary_terms((REPO_ROOT / ".kiro/specs/GLOSARIO.md").read_text("utf-8")))
    excluded = {normalize(t) for group in data["excluded"] for t in group["terms"]}
    assert listed and not excluded - column
    assert not excluded & set(listed)


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
    assert glossary(tree) == [
        ".kiro/specs/nested/example.md:11:usuario",
        ".kiro/specs/nested/example.md:12:modo autonomo",
        ".kiro/specs/nested/example.md:12:usuario",
        ".kiro/steering/policy.md:1:usuario",
    ]
    assert main(["--root", str(tree), "--write"]) == 1
    assert (tree / ".kiro/specs/TRAZABILIDAD.md").exists()


def test_missing_inputs_fail_closed(tmp_path: Path, tree: Path) -> None:
    (tree / ".kiro/specs/GLOSARIO.md").unlink()
    assert any("ENTRADA:" in f for f in audit(tree))
    assert not (tree / ".kiro/specs/TRAZABILIDAD.md").exists()
