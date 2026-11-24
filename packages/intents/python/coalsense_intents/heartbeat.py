"""Vigencia local de latidos para consumidores. Ningún reloj remoto prolonga la salud.

`bind` solo debe invocarse tras autenticar la conexión y el arranque del companion.
El instance_id nunca se adopta desde un mensaje recibido. Cada consulta comprueba
caducidad; el consumidor debe consultar antes de actuar y en su propio monitor.
"""

import re
import threading
from collections.abc import Callable
from time import monotonic_ns

from .validation import ContractError, validate_heartbeat

_INSTANCE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class HeartbeatReceiver:
    def __init__(
        self,
        *,
        on_unreachable: Callable[[], None],
        clock: Callable[[], int] = monotonic_ns,
        timeout_ns: int = 3_000_000_000,  # [SUPUESTO] tres periodos nominales de un segundo
    ) -> None:
        if type(timeout_ns) is not int or timeout_ns <= 0:
            raise ValueError("Invalid heartbeat timeout")
        self.on_unreachable, self.clock, self.timeout_ns = on_unreachable, clock, timeout_ns
        self._lock = threading.RLock()
        self._instance: str | None = None
        self._bound = False
        self._sequence = 0
        self._revision = -1
        self._received_ns: int | None = None
        self._reachable = False
        self.notification_failures = 0

    def _notify(self, lost: bool) -> None:
        if lost:
            try:
                self.on_unreachable()
            except Exception:
                with self._lock:
                    self.notification_failures += 1

    def bind(self, instance_id: str) -> None:
        if not isinstance(instance_id, str) or not _INSTANCE.fullmatch(instance_id):
            raise ValueError("Invalid companion instance")
        with self._lock:
            lost = self._reachable
            if self._instance != instance_id:
                self._sequence, self._revision = 0, -1
            self._instance, self._received_ns, self._reachable = instance_id, None, False
            self._bound = True
        self._notify(lost)

    def disconnect(self) -> None:
        with self._lock:
            lost = self._reachable
            self._received_ns, self._reachable = None, False
            self._bound = False
        self._notify(lost)

    @property
    def stop_reachable(self) -> bool:
        with self._lock:
            now, received = self.clock(), self._received_ns
            lost = self._reachable and (
                received is None or now < received or now - received >= self.timeout_ns
            )
            if lost:
                self._reachable = False
            reachable = self._reachable
        self._notify(lost)
        return reachable

    def receive(self, raw: object) -> bool:
        # Expirar el estado anterior antes de considerar una recuperación tardía.
        _ = self.stop_reachable
        try:
            event = validate_heartbeat(raw)
        except ContractError:
            self.disconnect()
            return False
        with self._lock:
            if (
                not self._bound
                or event["instance_id"] != self._instance
                or event["sequence"] <= self._sequence
                or event["state"]["revision"] < self._revision
            ):
                return False
            reachable = event["state"]["stop_reachable"]
            lost = self._reachable and not reachable
            self._sequence, self._revision = event["sequence"], event["state"]["revision"]
            self._received_ns, self._reachable = self.clock(), reachable
        self._notify(lost)
        return True
