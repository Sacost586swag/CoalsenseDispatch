"""All mutation fixtures are confined to pytest tmp_path."""

import json
from pathlib import Path

import pytest
from coalsense_audit.copy import POLICY, PY_CATALOG, TS_CATALOG, audit

REPO = Path(__file__).resolve().parents[3]


def write(root: Path, path: str, source: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    for path in (POLICY, TS_CATALOG, PY_CATALOG):
        write(tmp_path, path, (REPO / path).read_text(encoding="utf-8"))
    return tmp_path


def test_seed_catalogs_match_and_pass(tree: Path) -> None:
    assert audit(tree) == []


@pytest.mark.parametrize("path", [TS_CATALOG, PY_CATALOG])
@pytest.mark.parametrize(
    "word",
    [
        "TERAPIA",
        "TERAPEUTICO",
        "tratamiento",
        "cura",
        "curar",
        "DIAGNOSTICO",
        "diagnosticar",
        "¡MEJORA TU DEPRESIÓN!",
        "fallaste",
        "es tu culpa",
        "date prisa",
        "APURATE",
        "diagno\u0301stico",
    ],
)
def test_forbidden_words(tree: Path, path: str, word: str) -> None:
    source = (tree / path).read_text(encoding="utf-8").replace('"Alto"', json.dumps(word))
    write(tree, path, source)
    assert any(f"{path}:" in f and "PALABRA_PROHIBIDA" in f for f in audit(tree))


@pytest.mark.parametrize("base", ["apps/web/src", "packages/ui/src"])
@pytest.mark.parametrize(
    "jsx",
    [
        "<button>Enviar</button>",
        '<button>{"Enviar"}</button>',
        "<button>{`Enviar`}</button>",
        "<>Sí</>",
        '<input aria-label="Enviar" />',
        '<input title={"Enviar"} />',
        '<input placeholder="Enviar" />',
        "<img alt={`Imagen`} />",
        '<input title="" />',
        "<button>\n  Enviar\n</button>",
        "<button>{/* comment */}Enviar</button>",
        "<button>&#69;nviar</button>",
        "<button>{`Hola ${name}`}</button>",
        '<button>{ok ? "Enviar" : "Cancelar"}</button>',
        '<button>{ok && "Enviar"}</button>',
        '<input title={ok ? "Enviar" : undefined} />',
    ],
)
def test_visible_strings(tree: Path, base: str, jsx: str) -> None:
    path = f"{base}/nested/component.tsx"
    write(tree, path, f"export const view = {jsx};")
    assert any(f"{path}:" in f and "CADENA_VISIBLE" in f for f in audit(tree))


def test_nonvisible_and_catalog_references(tree: Path) -> None:
    write(
        tree,
        "apps/web/src/clean.tsx",
        """
// <button>Enviar</button>
const debug = "<button>Enviar</button>";
const technical = /Enviar/;
export const view = <div className="layout" data-testid="view">
  {/* Enviar */}<button title={es["stop.label"]}>{es["stop.label"]}</button>
  <span>{" "}123 +&nbsp;&mdash;</span>
  <span>{`${count}`}</span>
</div>;
""",
    )
    assert audit(tree) == []


@pytest.mark.parametrize(
    "path",
    [
        "apps/web/src/i18n/example.tsx",
        "packages/ui/src/i18n/example.tsx",
        "apps/other/src/example.tsx",
        "packages/ui/tests/example.tsx",
        "apps/web/src/example.ts",
    ],
)
def test_outside_scope(tree: Path, path: str) -> None:
    write(tree, path, "const view = <button>Enviar</button>;")
    assert audit(tree) == []


def test_word_boundaries_and_comments(tree: Path) -> None:
    for path in (TS_CATALOG, PY_CATALOG):
        source = (
            (tree / path)
            .read_text(encoding="utf-8")
            .replace('"Alto"', '"Lectura segura, procurar"')
        )
        write(tree, path, source)
    assert audit(tree) == []


def test_drift(tree: Path) -> None:
    write(tree, PY_CATALOG, 'es = {"stop.label": "Otro texto"}')
    assert any("CATALOGO" in f for f in audit(tree))


@pytest.mark.parametrize(
    "path,source",
    [
        (POLICY, '{"words": []}'),
        (POLICY, "not json"),
        (TS_CATALOG, "export const es = load();"),
        (PY_CATALOG, "es = load()"),
        ("apps/web/src/broken.tsx", "const view = <button>"),
    ],
)
def test_invalid_input_fails(tree: Path, path: str, source: str) -> None:
    write(tree, path, source)
    assert any("ENTRADA" in f for f in audit(tree))


def test_missing_catalog(tree: Path) -> None:
    (tree / TS_CATALOG).unlink()
    assert any("ENTRADA" in f for f in audit(tree))
