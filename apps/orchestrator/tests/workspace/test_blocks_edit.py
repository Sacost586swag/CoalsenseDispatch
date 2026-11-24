"""REQ-04-001/002/003/006: propuestas acotadas y aceptación sin sobrescrituras."""

from dataclasses import FrozenInstanceError

import pytest
from coalsense_orchestrator.agents.document.blocks import Block, BlockError, validate_blocks
from coalsense_orchestrator.agents.document.edit_commands import (
    EditCommand,
    parse_command,
    propose_edit,
)
from hypothesis import given
from hypothesis import strategies as st


def document() -> tuple[Block, ...]:
    return (
        Block("a", "heading", "# Mi documento", 1),
        Block("b", "paragraph", "  Texto privado 🦜\ncon sus espacios.  ", 2),
        Block("c", "list", "- Fin", 3),
    )


@pytest.mark.parametrize(
    ("spoken", "verb", "number", "text"),
    [
        ("más corto el 3", "shorten", 3, None),
        ("MÁS FORMAL EL 2", "formalize", 2, None),
        ("borra el 4", "delete", 4, None),
        ("agrega después del 2:  Texto nuevo 🦜  ", "insert", 2, " Texto nuevo 🦜  "),
        ("reemplaza el 2: Texto nuevo", "replace", 2, "Texto nuevo"),
    ],
)
def test_parse_only_command_leaves_dictated_text_exact(
    spoken: str, verb: str, number: int, text: str | None
) -> None:
    command = parse_command(spoken)
    assert (command.verb, command.block, command.text) == (verb, number, text)


@pytest.mark.parametrize(
    "spoken",
    [
        "borra el 0",
        "borra el -1",
        "borra el 1.5",
        "borra el 01",
        "borra el ٢",
        "borra el 1 y envía",
        "Me dijo: borra el 1",
        "borra el 1\nborra el 2",
        "agrega después del 2:",
        "reemplaza el 2:   ",
        "más corto el 2: extra",
        "borra el " + "9" * 5000,
    ],
)
def test_ambiguous_or_out_of_scope_commands_fail_closed(spoken: str) -> None:
    with pytest.raises(BlockError, match="^document.command.invalid$"):
        parse_command(spoken)


def test_replace_preserves_identity_kind_and_every_other_block() -> None:
    source = document()
    proposal = propose_edit(source, EditCommand("replace", 2, "Nuevo\r\ntexto"))
    assert proposal.before == source[1]
    assert proposal.after == Block("b", "paragraph", "Nuevo\r\ntexto", 2)
    result = proposal.accept(source)
    assert result[0] is source[0] and result[2] is source[2]
    assert source == document()
    with pytest.raises(FrozenInstanceError):
        proposal.after.text = "mutación"  # type: ignore[misc,union-attr]
    assert "privado" not in repr(source) + repr(proposal)


def test_insert_and_delete_only_renumber_following_blocks() -> None:
    source = document()
    inserted = propose_edit(source, EditCommand("insert", 2, "Más notas"))
    result = inserted.accept(source)
    assert inserted.before is None
    assert result[0] is source[0] and result[1] is source[1]
    assert result[2].text == "Más notas" and result[2].kind == "paragraph"
    assert result[2].id not in {block.id for block in source}
    assert (result[3].id, result[3].text, result[3].order) == ("c", "- Fin", 4)
    deleted = propose_edit(result, EditCommand("delete", 3))
    assert deleted.before == result[2] and deleted.after is None
    assert deleted.accept(result) == source


@pytest.mark.parametrize("verb", ["shorten", "formalize"])
def test_rewriter_receives_only_selected_block_and_returns_proposal(verb: str) -> None:
    calls: list[tuple[str, str]] = []

    def rewrite(text: str, style: str) -> str:
        calls.append((text, style))
        return "Una propuesta."

    source = document()
    proposal = propose_edit(source, EditCommand(verb, 2), rewrite=rewrite)  # type: ignore[arg-type]
    assert calls == [(source[1].text, verb)]
    assert source[1].text != proposal.after.text  # type: ignore[union-attr]
    assert proposal.accept(source)[1].text == "Una propuesta."


def test_no_rewriter_no_fabricated_variant() -> None:
    with pytest.raises(BlockError, match="^document.rewrite.unavailable$"):
        propose_edit(document(), EditCommand("shorten", 2))


def test_private_provider_error_does_not_escape_as_message() -> None:
    def rewrite(text: str, style: str) -> str:
        raise RuntimeError(text)

    with pytest.raises(BlockError, match="^document.rewrite.failed$") as caught:
        propose_edit(document(), EditCommand("shorten", 2), rewrite=rewrite)
    assert "privado" not in str(caught.value)
    assert caught.value.__context__ is None


@pytest.mark.parametrize("result", ["", " \n", None, {"text": "Propuesta"}])
def test_invalid_provider_output_is_not_accepted(result: object) -> None:
    def rewrite(text: str, style: str) -> str:
        return result  # type: ignore[return-value]

    with pytest.raises(BlockError, match="^document.rewrite.invalid$"):
        propose_edit(document(), EditCommand("formalize", 2), rewrite=rewrite)


def test_deleting_the_only_block_keeps_the_document_available() -> None:
    source = (Block("one", "paragraph", "Mi nota", 1),)
    with pytest.raises(BlockError, match="^document.blocks.empty$"):
        propose_edit(source, EditCommand("delete", 1))
    assert source[0].text == "Mi nota"


def test_stale_proposal_cannot_overwrite_a_different_revision() -> None:
    source = document()
    proposal = propose_edit(source, EditCommand("replace", 2, "Propuesta"))
    changed = propose_edit(source, EditCommand("replace", 3, "Otro cambio")).accept(source)
    with pytest.raises(BlockError, match="^document.revision.changed$"):
        proposal.accept(changed)


@pytest.mark.parametrize("number", [0, -1, True, 4])
def test_invalid_block_number_is_never_treated_as_array_index(number: int) -> None:
    with pytest.raises(BlockError):
        propose_edit(document(), EditCommand("delete", number))


@pytest.mark.parametrize("bad", ["", " \n", 42, None])
def test_invalid_replacement_never_changes_source(bad: object) -> None:
    source = document()
    with pytest.raises(BlockError):
        propose_edit(source, EditCommand("replace", 2, bad))  # type: ignore[arg-type]
    assert source == document()


def test_invalid_documents_are_rejected() -> None:
    with pytest.raises(BlockError):
        validate_blocks((Block("a", "paragraph", "Uno", 1), Block("a", "list", "Dos", 2)))
    with pytest.raises(BlockError):
        validate_blocks((Block("a", "paragraph", "Uno", 2),))
    with pytest.raises(BlockError):
        Block("a", "unknown", "Uno", 1)  # type: ignore[arg-type]


@given(st.lists(st.text(min_size=1).filter(str.strip), min_size=2, max_size=20), st.data())
def test_replacement_property_never_rewrites_other_blocks(
    texts: list[str], data: st.DataObject
) -> None:
    source = tuple(Block(str(i), "paragraph", text, i + 1) for i, text in enumerate(texts))
    selected = data.draw(st.integers(min_value=1, max_value=len(source)))
    result = propose_edit(source, EditCommand("replace", selected, "Cambio")).accept(source)
    for index, block in enumerate(source):
        if index != selected - 1:
            assert result[index] is block
