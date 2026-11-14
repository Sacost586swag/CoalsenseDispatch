"""UUIDv7 ordenables dentro del proceso y relojes con unidades explícitas."""

import secrets
import threading
import time
from datetime import UTC, datetime
from uuid import UUID

_lock = threading.Lock()
_last_ms = -1
_random = 0
_mask = (1 << 74) - 1


def new_id() -> str:
    """RFC 9562: 48 bits de ms, 74 aleatorios, versión y variante.

    Mismo ms o retroceso: incrementar los 74 bits; al agotarlos avanzar
    un ms lógico. La monotonía es local al proceso, no entre procesos.
    """
    global _last_ms, _random
    with _lock:
        now = time.time_ns() // 1_000_000
        if now > _last_ms:
            _last_ms, _random = now, secrets.randbits(74)
        elif _random == _mask:
            _last_ms += 1
            _random = secrets.randbits(74)
        else:
            _random += 1
        if not 0 <= _last_ms < (1 << 48):
            raise OverflowError("El reloj está fuera del rango de UUIDv7.")
        value = (_last_ms << 80) | (7 << 76) | ((_random >> 62) << 64)
        value |= (2 << 62) | (_random & ((1 << 62) - 1))
        return str(UUID(int=value))


def monotonic_ns() -> int:
    """Nanosegundos para medir intervalos; origen local no persistible."""
    return time.monotonic_ns()


def wall_clock_iso() -> str:
    """Hora UTC con precisión de milisegundos, igual que TypeScript."""
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
