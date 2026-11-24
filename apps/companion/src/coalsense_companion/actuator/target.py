"""Puerto local de destino: no recoge títulos, documentos ni contenido de campos."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Target:
    window: int
    focus: int
    process: int
    allowed: bool
    reason: str = "unavailable"
    foreground: int = 0
    foreground_process: int = 0


class TargetProbe(Protocol):
    def capture(self, *, pointer: bool) -> Target: ...


class TargetBlocked(RuntimeError):
    def __init__(self, reason: str = "unavailable") -> None:
        self.reason = reason if reason in {"elevated", "changed"} else "unavailable"
        super().__init__("The local input target is not controllable")


class TargetGuard:
    def __init__(self, probe: TargetProbe) -> None:
        self.probe = probe

    def capture(self, *, pointer: bool) -> Target:
        try:
            target = self.probe.capture(pointer=pointer)
        except Exception:
            raise TargetBlocked() from None
        if not target.allowed or not target.window or not target.process:
            raise TargetBlocked(target.reason)
        return target

    def check(self, expected: Target, *, pointer: bool) -> None:
        if self.capture(pointer=pointer) != expected:
            raise TargetBlocked("changed")
