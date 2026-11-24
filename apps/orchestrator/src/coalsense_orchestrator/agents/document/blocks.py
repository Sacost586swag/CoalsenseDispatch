"""Bloques inmutables. Este módulo no persiste ni registra contenido."""

from dataclasses import dataclass, field
from typing import Literal

BlockKind = Literal["paragraph", "heading", "list"]


class BlockError(ValueError):
    """Código estable de dominio; nunca contiene el texto de una persona."""


@dataclass(frozen=True)
class Block:
    id: str
    kind: BlockKind
    text: str = field(repr=False)
    order: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.id, str)
            or not self.id.strip()
            or self.kind not in ("paragraph", "heading", "list")
            or not isinstance(self.text, str)
            or not self.text.strip()
            or type(self.order) is not int
            or self.order < 1
        ):
            raise BlockError("document.block.invalid")


def validate_blocks(blocks: tuple[Block, ...]) -> None:
    """El orden es explícito, contiguo y empieza en uno; no hay IDs repetidos."""
    if not isinstance(blocks, tuple) or not blocks:
        raise BlockError("document.blocks.invalid")
    seen: set[str] = set()
    for number, block in enumerate(blocks, 1):
        if not isinstance(block, Block) or block.order != number or block.id in seen:
            raise BlockError("document.blocks.invalid")
        seen.add(block.id)
