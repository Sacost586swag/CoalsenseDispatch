"""Pila acotada de Deshacer (REQ-01-022 a 024).

Una acción irreversible o de resultado incierto es una barrera: nunca se busca una
acción anterior para aparentar que se deshizo la última. Los callbacks deben ser
locales; el ejecutor debe serializar actuaciones nuevas con la operación de deshacer.
"""

import threading
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from coalsense_common.i18n_es import es

from .action_classes import ACTION_POLICIES, ActionKind, Reversibility


class UndoBusy(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Undo is already in progress")


class UndoNotApplied(RuntimeError):
    """El callback garantiza que no realizó ningún efecto antes de interrumpirse."""


@dataclass(frozen=True, slots=True)
class UndoEntry:
    kind: ActionKind
    revert: Callable[[], None] | None = field(default=None, repr=False)
    can_revert: Callable[[], bool] | None = field(default=None, repr=False)
    reversible: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ActionKind):
            raise ValueError("Unknown local action class")
        policy = ACTION_POLICIES[self.kind]
        if self.reversible is not None and type(self.reversible) is not bool:
            raise ValueError("Invalid reversibility flag")
        if self.reversible is None:
            object.__setattr__(self, "reversible", policy != Reversibility.NEVER)
        if policy == Reversibility.NEVER and self.reversible:
            raise ValueError("An irreversible class cannot register a reversal")
        if not self.reversible:
            if self.revert is not None or self.can_revert is not None:
                raise ValueError("An irreversible action cannot register a reversal")
        elif self.revert is None:
            raise ValueError("A reversible action requires a reversal")
        elif policy == Reversibility.VERIFIED and self.can_revert is None:
            raise ValueError("Text reversal requires a verified target")


@dataclass(frozen=True, slots=True)
class UndoResult:
    code: str
    message_es: str
    changed: bool
    kind: ActionKind | None = None


@dataclass(slots=True)
class _Stored:
    entry: UndoEntry
    uncertain: bool = False


_LABELS = {
    ActionKind.POINTER_DRAG_TOGGLE: "input.action.drag",
    ActionKind.TEXT_INSERT: "input.action.text",
    ActionKind.TEXT_DICTATION: "input.action.dictation",
    ActionKind.MODE_SET: "input.action.mode",
    ActionKind.PROFILE_SWITCH: "input.action.profile",
}


def _result(code: str, kind: ActionKind | None = None) -> UndoResult:
    if code == "done":
        assert kind is not None
        message = es["input.undo.done.message"].format(action=es[_LABELS[kind]])
    else:
        message = es[f"input.undo.{code}.message"]
    return UndoResult(f"input.undo.{code}", message, code == "done", kind)


class UndoStack:
    def __init__(self, capacity: int = 100) -> None:  # [SUPUESTO] número de entradas en memoria
        if type(capacity) is not int or capacity < 1:
            raise ValueError("Invalid undo capacity")
        self._entries: deque[_Stored] = deque(maxlen=capacity)
        self._lock = threading.RLock()
        self._busy = False
        self.evictions = 0

    def push(self, entry: UndoEntry) -> None:
        with self._lock:
            if self._busy:
                raise UndoBusy()
            if len(self._entries) == self._entries.maxlen:
                self.evictions += 1
            self._entries.append(_Stored(entry))

    def clear(self) -> None:
        with self._lock:
            if self._busy:
                raise UndoBusy()
            self._entries.clear()
            self.evictions = 0

    def undo(self) -> UndoResult:
        with self._lock:
            if self._busy:
                return _result("busy")
            if not self._entries:
                return _result("empty")
            stored = self._entries[-1]
            entry = stored.entry
            if stored.uncertain:
                return _result("uncertain", entry.kind)
            if not entry.reversible:
                return _result("irreversible", entry.kind)
            self._busy = True
        try:
            if entry.can_revert is not None:
                try:
                    verified = entry.can_revert()
                except Exception:
                    verified = False
                if verified is not True:
                    return _result("unverified", entry.kind)
            try:
                assert entry.revert is not None
                entry.revert()
            except UndoNotApplied:
                return _result("blocked", entry.kind)
            except Exception:
                with self._lock:
                    stored.uncertain = True
                return _result("uncertain", entry.kind)
            with self._lock:
                self._entries.pop()
            return _result("done", entry.kind)
        finally:
            with self._lock:
                self._busy = False
