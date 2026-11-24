"""Control síncrono de Alto (REQ-01-018 a 020).

Cada primitiva usa una autorización local que se invalida al detener. Las operaciones
del backend y los callbacks de cancelación deben ser locales, acotados y no esperar
a otros trabajadores. La bandera se activa antes de esperar una operación ya iniciada.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


class InputBackend(Protocol):
    def key_down(self, key: str) -> bool:
        """True si esta actuación adquirió la tecla; False si ya estaba pulsada."""
        ...

    def key_up(self, key: str) -> None: ...
    def button_down(self, button: str) -> bool: ...
    def button_up(self, button: str) -> None: ...


class ActuationBlocked(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Actuation is paused or its authorization is no longer valid")


@dataclass(frozen=True, slots=True)
class ActuationLease:
    identifier: int
    epoch: int
    kind: str
    while_paused: bool = False


@dataclass(frozen=True, slots=True)
class HaltReport:
    keys_remaining: int
    buttons_remaining: int
    cancellations_remaining: int

    @property
    def safe(self) -> bool:
        return not (self.keys_remaining or self.buttons_remaining or self.cancellations_remaining)


class HaltFailure(RuntimeError):
    def __init__(self, report: HaltReport) -> None:
        self.report = report
        super().__init__("Some local resources could not be stopped")


class HaltController:
    def __init__(self, backend: InputBackend) -> None:
        self.backend = backend
        self._paused = threading.Event()
        self._paused.set()  # cerrado hasta que la composición permita reanudar explícitamente
        self._control_lock = threading.Lock()
        self._step_lock = threading.RLock()
        self._halt_lock = threading.Lock()
        self._pending_halts = 0
        self._halting = threading.Event()
        self._epoch = 0
        self._sequence = 0
        self._leases: dict[int, ActuationLease] = {}
        self._cancellations: dict[int, Callable[[], None]] = {}
        self._cancel_pending: dict[int, Callable[[], None]] = {}
        self._keys: set[str] = set()
        self._buttons: set[str] = set()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    @property
    def active_count(self) -> int:
        with self._step_lock:
            return len(self._leases)

    def wait_until_paused(self, timeout: float) -> bool:
        return self._paused.wait(timeout)

    def resume(self) -> None:
        with self._control_lock:
            if self._pending_halts:
                raise ActuationBlocked()
            with self._step_lock:
                if not self.paused:
                    return
                if self._keys or self._buttons or self._cancel_pending:
                    raise ActuationBlocked()
                self._paused.clear()

    def begin(
        self,
        kind: str,
        *,
        cancel: Callable[[], None] | None = None,
        while_paused: bool = False,
    ) -> ActuationLease:
        if self._halting.is_set() or (self.paused and not while_paused):
            raise ActuationBlocked()
        with self._step_lock:
            if (
                self._halting.is_set()
                or (self.paused and not while_paused)
                or (
                    while_paused
                    and self.paused
                    and (self._keys or self._buttons or self._cancel_pending)
                )
            ):
                raise ActuationBlocked()
            self._sequence += 1
            lease = ActuationLease(self._sequence, self._epoch, kind, while_paused)
            self._leases[lease.identifier] = lease
            if cancel is not None:
                self._cancellations[lease.identifier] = cancel
            return lease

    def finish(self, lease: ActuationLease) -> None:
        with self._step_lock:
            if self._leases.get(lease.identifier) is lease:
                self._leases.pop(lease.identifier)
                self._cancellations.pop(lease.identifier, None)

    def step[T](self, lease: ActuationLease, operation: Callable[[], T]) -> T:
        if self._halting.is_set() or (self.paused and not lease.while_paused):
            raise ActuationBlocked()
        with self._step_lock:
            if (
                self._halting.is_set()
                or (self.paused and not lease.while_paused)
                or lease.epoch != self._epoch
                or self._leases.get(lease.identifier) is not lease
            ):
                raise ActuationBlocked()
            return operation()

    def key_down(self, lease: ActuationLease, key: str) -> None:
        def press() -> None:
            if key in self._keys:
                return
            self._keys.add(key)  # ante fallo incierto, Alto intentará soltarla
            if not self.backend.key_down(key):
                self._keys.discard(key)  # ya estaba pulsada fuera de este controlador

        self.step(lease, press)

    def key_up(self, lease: ActuationLease, key: str) -> None:
        def release() -> None:
            if key in self._keys:
                self.backend.key_up(key)
                self._keys.remove(key)

        self.step(lease, release)

    def button_down(self, lease: ActuationLease, button: str) -> None:
        def press() -> None:
            if button in self._buttons:
                return
            self._buttons.add(button)
            if not self.backend.button_down(button):
                self._buttons.discard(button)

        self.step(lease, press)

    def button_up(self, lease: ActuationLease, button: str) -> None:
        def release() -> None:
            if button in self._buttons:
                self.backend.button_up(button)
                self._buttons.remove(button)

        self.step(lease, release)

    def halt(self) -> HaltReport:
        with self._control_lock:
            self._pending_halts += 1
            self._halting.set()
            self._paused.set()
        try:
            with self._halt_lock:
                with self._step_lock:
                    self._paused.set()
                    self._epoch += 1
                    self._cancel_pending.update(self._cancellations)
                    self._cancellations.clear()
                    self._leases.clear()
                    for key in tuple(self._keys):
                        try:
                            self.backend.key_up(key)
                        except Exception:
                            continue
                        self._keys.remove(key)
                    for button in tuple(self._buttons):
                        try:
                            self.backend.button_up(button)
                        except Exception:
                            continue
                        self._buttons.remove(button)
                # Nunca esperar a que un trabajador termine dentro de estos callbacks.
                for identifier, cancel in tuple(self._cancel_pending.items()):
                    try:
                        cancel()
                    except Exception:
                        continue
                    self._cancel_pending.pop(identifier)
                report = HaltReport(len(self._keys), len(self._buttons), len(self._cancel_pending))
                if not report.safe:
                    raise HaltFailure(report)
                return report
        finally:
            with self._control_lock:
                self._pending_halts -= 1
                if not self._pending_halts:
                    self._halting.clear()
