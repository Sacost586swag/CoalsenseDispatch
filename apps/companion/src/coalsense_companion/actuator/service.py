"""Consumidor exclusivo del bus. Los adaptadores no reciben acceso al backend."""

import threading
from collections.abc import Callable
from typing import Protocol

from ..bus.core import BusDelivery, IntentBus
from .action_classes import ActionKind
from .guard import ActuationGate, ActuationTicket
from .halt import ActuationBlocked, InputBackend
from .keys import press
from .pointer import Pointer, PointerBackend
from .results import ActuationResult, result
from .target import TargetBlocked, TargetGuard
from .text import TextBackend, insert
from .undo_stack import UndoEntry, UndoNotApplied, UndoStack


class Backend(InputBackend, PointerBackend, TextBackend, Protocol):
    pass


_TYPES = frozenset(
    kind.value
    for kind in ActionKind
    if kind not in {ActionKind.MODE_SET, ActionKind.PROFILE_SWITCH}
) | {"control.undo", "input.pause", "input.resume"}


class NativeActuator:
    def __init__(
        self,
        bus: IntentBus,
        gate: ActuationGate,
        backend: Backend,
        target: TargetGuard,
        feedback: Callable[[ActuationResult], None],
        *,
        undo: UndoStack | None = None,
    ) -> None:
        if gate.bus is not bus or gate.controller.backend is not backend:
            raise ValueError("The actuator must share its bus and backend with its gate")
        self.gate, self.backend, self.target, self.feedback = gate, backend, target, feedback
        self.undo = undo if undo is not None else UndoStack()
        self.pointer = Pointer(gate, backend)
        self._serial = threading.Lock()
        self._undo_ticket: ActuationTicket | None = None
        self.feedback_failures = 0
        self._unsubscribe = bus.subscribe_bound(_TYPES, self._receive)

    @property
    def dragging(self) -> bool:
        return self.pointer.dragging

    def close(self) -> None:
        self.gate.controller.halt()
        self._unsubscribe()

    def _current_undo(self) -> ActuationTicket:
        if self._undo_ticket is None:
            raise UndoNotApplied()
        return self._undo_ticket

    def _receive(self, delivery: BusDelivery) -> None:
        with self._serial:
            outcome = self._execute(delivery)
        try:
            self.feedback(outcome)
        except Exception:
            self.feedback_failures += 1

    def _execute(self, delivery: BusDelivery) -> ActuationResult:
        intention = delivery.intent
        kind = intention["type"]
        identifier = intention["id"]
        ticket: ActuationTicket | None = None
        attempted = False
        retain = False
        action: ActionKind | None = None
        failed = False
        try:
            if kind == "input.resume":
                self.gate.resume(delivery)
                return result(identifier, kind, "resumed")
            ticket = self.gate.begin(
                delivery,
                kind,
                cancel=self.pointer.cancel_drag
                if kind == "pointer.drag_toggle"
                else self.backend.release_text
                if kind.startswith("text.")
                else None,
            )
            if kind == "input.pause":
                self.gate.step(ticket, lambda: None)
                self.gate.controller.halt()
                return result(identifier, kind, "paused")
            if kind == "control.undo":
                self._undo_ticket = ticket
                self.gate.step(ticket, lambda: None)
                outcome = self.undo.undo()
                return ActuationResult(identifier, kind, outcome.code, outcome.message_es)
            if intention["type"] == "text.dictation" and not intention["payload"]["final"]:
                return result(identifier, kind, "interim")
            action = ActionKind(kind)
            if kind == "pointer.drag_toggle" and self.pointer.dragging:
                self.pointer.end_drag(ticket)
                self.undo.push(UndoEntry(action, reversible=False))
                return result(identifier, kind, "done")
            pointer = kind.startswith("pointer.")
            expected = self.target.capture(pointer=pointer)

            def check() -> None:
                nonlocal attempted
                self.target.check(expected, pointer=pointer)
                attempted = True

            if intention["type"] == "pointer.move":
                p = intention["payload"]
                self.pointer.move(
                    ticket,
                    p["x"],
                    p["y"],
                    absolute=p["mode"] == "absolute",
                    check_target=check,
                )
            elif intention["type"] == "pointer.scroll":
                scroll = intention["payload"]
                self.pointer.scroll(ticket, scroll["dx"], scroll["dy"], check)
            elif intention["type"] in {"pointer.click", "pointer.double_click"}:
                button = intention["payload"]["button"]
                self.pointer.click(ticket, button, check, double=kind == "pointer.double_click")
            elif intention["type"] == "pointer.drag_toggle":
                button = intention["payload"]["button"]

                retain = self.pointer.toggle(ticket, button, check)
                if retain:
                    self.undo.push(
                        UndoEntry(
                            action,
                            self.pointer.reversal(self._current_undo),
                            can_revert=lambda: self.pointer.same_drag(ticket),
                        )
                    )
                    return result(identifier, kind, "dragging")
            elif intention["type"] == "key.press":
                press(self.gate, ticket, intention["payload"]["keys"], check)
            elif intention["type"] in {"text.insert", "text.dictation"}:
                insert(self.gate, ticket, self.backend, intention["payload"]["text"], check)
            if attempted:
                # No backspace genérico: sin verificador de edición, texto es irreversible.
                self.undo.push(UndoEntry(action, reversible=False))
            return result(identifier, kind, "done")
        except ActuationBlocked:
            failed = True
            code = "blocked"
        except TargetBlocked as error:
            failed = True
            code = error.reason
        except Exception:
            failed = True
            code = "failed"
        finally:
            self._undo_ticket = None
            if failed and (attempted or self.pointer.dragging):
                if attempted and action is not None:
                    self.undo.push(UndoEntry(action, reversible=False))
                try:
                    self.gate.controller.halt()
                except Exception:
                    code = "halt_failed"
            if ticket is not None and not retain:
                self.gate.finish(ticket)
        return result(identifier, kind, code, partial=attempted)
