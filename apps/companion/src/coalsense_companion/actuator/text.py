"""Texto Unicode por carácter, con comprobación de foco y Alto entre caracteres."""

from collections.abc import Callable
from typing import Protocol

from .guard import ActuationGate, ActuationTicket


class TextBackend(Protocol):
    def write_character(self, character: str) -> None: ...
    def release_text(self) -> None: ...


def insert(
    gate: ActuationGate,
    ticket: ActuationTicket,
    backend: TextBackend,
    value: str,
    check_target: Callable[[], None],
) -> None:
    # Rechazar sustitutos aislados antes de introducir cualquier carácter.
    value.encode("utf-16-le")
    for character in value:

        def write(character: str = character) -> None:
            check_target()
            backend.write_character(character)

        gate.step(ticket, write)
