"""Operaciones de puntero y estado consultable del arrastre, sin bucle de red."""

from collections.abc import Callable
from typing import Protocol

from .guard import ActuationGate, ActuationTicket
from .halt import ActuationBlocked


class PointerBackend(Protocol):
    def move(self, x: float, y: float, *, absolute: bool = False) -> None: ...
    def scroll(self, dx: float, dy: float) -> None: ...


class Pointer:
    def __init__(self, gate: ActuationGate, backend: PointerBackend) -> None:
        self.gate, self.backend = gate, backend
        self._drag: tuple[ActuationTicket, str] | None = None

    @property
    def dragging(self) -> bool:
        return self._drag is not None

    def cancel_drag(self) -> None:
        # Alto ya intenta soltar los botones antes de llamar este callback.
        self._drag = None

    def same_drag(self, ticket: ActuationTicket) -> bool:
        return self._drag is not None and self._drag[0] is ticket

    def move(
        self,
        ticket: ActuationTicket,
        x: float,
        y: float,
        *,
        absolute: bool,
        check_target: Callable[[], None],
    ) -> None:
        def move() -> None:
            check_target()
            self.backend.move(x, y, absolute=absolute)

        self.gate.step(ticket, move)

    def scroll(
        self,
        ticket: ActuationTicket,
        dx: float,
        dy: float,
        check_target: Callable[[], None],
    ) -> None:
        def scroll() -> None:
            check_target()
            self.backend.scroll(dx, dy)

        self.gate.step(ticket, scroll)

    def click(
        self,
        ticket: ActuationTicket,
        button: str,
        check_target: Callable[[], None],
        *,
        double: bool = False,
    ) -> None:
        if self.dragging:
            raise ActuationBlocked()
        for _ in range(2 if double else 1):

            def down() -> None:
                check_target()
                self.gate.controller.button_down(ticket.lease, button)

            self.gate.step(ticket, down)
            self.gate.controller.button_up(ticket.lease, button)

    def toggle(
        self,
        ticket: ActuationTicket,
        button: str,
        check_target: Callable[[], None],
    ) -> bool:
        if self._drag is not None:
            self.end_drag(ticket)
            return False

        def start() -> None:
            check_target()
            self.gate.controller.button_down(ticket.lease, button)
            self._drag = (ticket, button)

        self.gate.step(ticket, start)
        return True

    def end_drag(self, ticket: ActuationTicket) -> None:
        def end() -> None:
            previous = self._drag
            if previous is None:
                return
            self.gate.controller.button_up(ticket.lease, previous[1])
            self._drag = None
            self.gate.finish(previous[0])

        self.gate.step(ticket, end)

    def reversal(self, ticket: Callable[[], ActuationTicket]) -> Callable[[], None]:
        return lambda: self.end_drag(ticket())
