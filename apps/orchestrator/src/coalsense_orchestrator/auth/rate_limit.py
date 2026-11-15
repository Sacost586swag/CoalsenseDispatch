"""Espera creciente por clave (cuenta, IP). Nunca bloqueo permanente (REQ-00-025)."""

from collections import deque
from math import ceil

from .ports import Clock


class RateLimiter:
    """Cada fallo seguido duplica la espera (2, 4, 8... s) hasta `cap_s`.

    Intentar durante la espera no la alarga. Tras `cap_s` de descanso sin fallos, la cuenta
    vuelve a cero. Solo avanza con el reloj inyectado, sin dormir.
    shortcut: estado en memoria de un solo proceso; con varias réplicas pasa a la BD (H2).
    """

    def __init__(self, clock: Clock, *, cap_s: int = 900, base_s: int = 2) -> None:
        self._clock = clock
        self._cap_s = cap_s
        self._base_s = base_s
        self._state: dict[str, tuple[int, float]] = {}  # clave -> (fallos seguidos, libre desde)
        self._events: dict[str, deque[float]] = {}  # presupuestos por ventana deslizante

    def retry_after(self, *keys: str) -> int:
        now = self._clock.monotonic_s()
        waits = [self._state[k][1] - now for k in keys if k in self._state]
        return max(0, ceil(round(max(waits, default=0.0), 6)))

    def fail(self, *keys: str) -> None:
        now = self._clock.monotonic_s()
        for key in keys:
            count, until = self._state.get(key, (0, 0.0))
            if now >= until + self._cap_s:
                count = 0
            count += 1
            wait = min(self._cap_s, self._base_s ** min(count, 30))
            self._state[key] = (count, now + wait)
        if len(self._state) > 10_000:
            self._state = {k: v for k, v in self._state.items() if now < v[1] + self._cap_s}

    def window_wait(self, key: str, limit: int, window_s: int) -> int:
        """Segundos hasta que la ventana vuelva a tener cupo; 0 si hay cupo. Siempre se desliza."""
        now = self._clock.monotonic_s()
        events = self._events.get(key)
        while events and events[0] <= now - window_s:
            events.popleft()
        if not events:
            self._events.pop(key, None)
            return 0
        return ceil(round(events[0] + window_s - now, 6)) if len(events) >= limit else 0

    def window_hit(self, key: str, limit: int) -> None:
        events = self._events.setdefault(key, deque(maxlen=limit))
        events.append(self._clock.monotonic_s())

    def reset(self, *keys: str) -> None:
        for key in keys:
            self._state.pop(key, None)
