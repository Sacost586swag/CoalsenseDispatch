"""Gramática explícita y propuestas. Aceptar exige la misma revisión completa.

`rewrite` es un puerto de propuesta: su futura implementación debe pasar por el
gateway y comprobar consentimiento. Aquí no se instancian clientes ni proveedores.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Literal
from uuid import uuid4

from .blocks import Block, BlockError, validate_blocks

EditVerb = Literal["replace", "insert", "delete", "shorten", "formalize"]
Rewrite = Callable[[str, str], str]


@dataclass(frozen=True)
class EditCommand:
    verb: EditVerb
    block: int
    text: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if (
            self.verb not in ("replace", "insert", "delete", "shorten", "formalize")
            or type(self.block) is not int
            or self.block < 1
        ):
            raise BlockError("document.command.invalid")
        if self.verb in ("replace", "insert"):
            if not isinstance(self.text, str) or not self.text.strip():
                raise BlockError("document.command.invalid")
        elif self.text is not None:
            raise BlockError("document.command.invalid")


def parse_command(spoken: str) -> EditCommand:
    """Se reconoce la orden completa; nunca se busca una orden dentro de notas.

    [SUPUESTO] El reconocimiento entrega números decimales ASCII, sin ceros
    iniciales. Tras dos puntos se consume un espacio de separación; el resto del
    texto se conserva exactamente. Las órdenes desconocidas no se adivinan.
    """
    patterns: tuple[tuple[EditVerb, str], ...] = (
        ("shorten", r"más corto el ([1-9][0-9]{0,8})"),
        ("formalize", r"más formal el ([1-9][0-9]{0,8})"),
        ("delete", r"borra el ([1-9][0-9]{0,8})"),
        ("insert", r"agrega después del ([1-9][0-9]{0,8}): ?([\s\S]+)"),
        ("replace", r"reemplaza el ([1-9][0-9]{0,8}): ?([\s\S]+)"),
    )
    for verb, pattern in patterns:
        match = re.fullmatch(pattern, spoken, flags=re.IGNORECASE)
        if match:
            return EditCommand(verb, int(match[1]), match[2] if match.lastindex == 2 else None)
    raise BlockError("document.command.invalid")


@dataclass(frozen=True)
class EditProposal:
    before: Block | None
    after: Block | None
    _base: tuple[Block, ...] = field(repr=False)
    _result: tuple[Block, ...] = field(repr=False)

    def accept(self, current: tuple[Block, ...]) -> tuple[Block, ...]:
        """No hace I/O. El servicio de versiones debe guardar atómicamente."""
        validate_blocks(current)
        if current != self._base:
            raise BlockError("document.revision.changed")
        return self._result


def propose_edit(
    blocks: tuple[Block, ...], command: EditCommand, *, rewrite: Rewrite | None = None
) -> EditProposal:
    validate_blocks(blocks)
    if command.block > len(blocks):
        raise BlockError("document.block.not_found")
    index = command.block - 1
    selected = blocks[index]
    before: Block | None = selected
    after: Block | None
    if command.verb == "delete":
        if len(blocks) == 1:
            raise BlockError("document.blocks.empty")
        after = None
        result = blocks[:index] + tuple(replace(b, order=b.order - 1) for b in blocks[index + 1 :])
    elif command.verb == "insert":
        assert command.text is not None  # Validado en EditCommand.
        before = None
        new_id = str(uuid4())
        while any(b.id == new_id for b in blocks):
            new_id = str(uuid4())
        after = Block(new_id, "paragraph", command.text, command.block + 1)
        result = (
            blocks[: index + 1]
            + (after,)
            + tuple(replace(b, order=b.order + 1) for b in blocks[index + 1 :])
        )
    else:
        text = command.text
        if command.verb in ("shorten", "formalize"):
            if rewrite is None:
                raise BlockError("document.rewrite.unavailable")
            failed = False
            try:
                text = rewrite(selected.text, command.verb)
            except Exception:
                # Se sale del manejador antes de elevar: sin encadenar errores
                # del proveedor que podrían incluir el texto privado.
                failed = True
            if failed:
                raise BlockError("document.rewrite.failed")
        if not isinstance(text, str) or not text.strip():
            raise BlockError("document.rewrite.invalid")
        after = replace(selected, text=text)
        result = blocks[:index] + (after,) + blocks[index + 1 :]
    validate_blocks(result)
    return EditProposal(before, after, blocks, result)
