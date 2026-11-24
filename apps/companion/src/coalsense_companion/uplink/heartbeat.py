"""Latido periódico sin biometría ni texto (REQ-01-128).

El puerto send debe conectarse al WebSocket autenticado sobre TLS. Este módulo no
abre conexiones ni acepta mensajes remotos para el actuador. El intervalo y el
timeout de salud son plazos técnicos, no límites para decisiones de la persona.
"""

import math
import threading
from collections.abc import Callable

from coalsense_common.ids import new_id, wall_clock_iso
from coalsense_intents import HeartbeatEvent, validate_heartbeat

from ..bus.stop_state import StopState


class HeartbeatPublisher:
    def __init__(
        self,
        state: StopState,
        send: Callable[[HeartbeatEvent], None],
        *,
        interval_seconds: float = 1.0,  # [SUPUESTO] periodo técnico del enlace
    ) -> None:
        if (
            isinstance(interval_seconds, bool)
            or not math.isfinite(interval_seconds)
            or interval_seconds <= 0
        ):
            raise ValueError("Invalid heartbeat interval")
        self.state, self.send, self.interval_seconds = state, send, interval_seconds
        self.instance_id = new_id()
        self._sequence = 0
        self._lock = threading.RLock()
        self.send_failures = 0

    def tick(self) -> bool:
        with self._lock:
            snapshot = self.state.snapshot()
            self._sequence += 1
            event = validate_heartbeat(
                {
                    "event": "heartbeat",
                    "schema_version": 1,
                    "instance_id": self.instance_id,
                    "sequence": self._sequence,
                    "wall_ts": wall_clock_iso(),
                    "state": {
                        "stop_reachable": snapshot.stop_reachable,
                        "revision": snapshot.revision,
                        "updated_at": snapshot.updated_at,
                        "routes": [
                            {
                                "identifier": route.identifier,
                                "modality": route.modality,
                                "healthy": route.healthy,
                                "reason": route.reason,
                            }
                            for route in snapshot.routes
                        ],
                    },
                }
            )
            try:
                self.send(event)
            except Exception:
                self.send_failures += 1
                return False
            return True

    def run(self, stopped: threading.Event) -> None:
        """Bucle del trabajador del enlace; la persona puede detenerlo sin esperar el periodo."""
        while not stopped.is_set():
            self.tick()
            stopped.wait(self.interval_seconds)
