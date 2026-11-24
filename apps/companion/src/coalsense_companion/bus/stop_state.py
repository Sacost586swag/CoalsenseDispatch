"""Salud local de rutas de Alto (REQ-01-026 y 129), sin datos de sensores.

El supervisor conserva los tokens; un proceso reiniciado necesita evidencia nueva.
Registrar una ruta no demuestra salud. `snapshot` comprueba también la caducidad:
el supervisor debe llamarlo periódicamente, además de cada autorización de actuación.
Los puertos de aviso son locales, acotados y no deben esperar trabajo de interfaz.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass

from coalsense_common.ids import monotonic_ns, wall_clock_iso
from coalsense_intents.models import MODALITIES, Modality
from coalsense_intents.models import StopRouteReason as Reason

_FAILURES = frozenset(
    {
        "device_unavailable",
        "model_loading",
        "adapter_unresponsive",
        "stop_unbound",
        "stale",
        "stopped",
    }
)


@dataclass(frozen=True, slots=True)
class RouteEvidence:
    device_streaming: bool
    model_loaded: bool
    adapter_responding: bool
    stop_bound: bool

    def __post_init__(self) -> None:
        if any(
            type(value) is not bool
            for value in (
                self.device_streaming,
                self.model_loaded,
                self.adapter_responding,
                self.stop_bound,
            )
        ):
            raise ValueError("Invalid route health evidence")


@dataclass(frozen=True, slots=True, eq=False)
class RouteToken:
    identifier: str


@dataclass(frozen=True, slots=True)
class RouteState:
    identifier: str
    modality: Modality
    healthy: bool
    reason: Reason


@dataclass(frozen=True, slots=True)
class StopSnapshot:
    stop_reachable: bool
    routes: tuple[RouteState, ...]
    revision: int
    updated_at: str


@dataclass(slots=True)
class _Route:
    token: RouteToken
    modality: Modality
    evidence: RouteEvidence | None = None
    seen_ns: int | None = None
    forced_reason: Reason = "starting"


class StopState:
    def __init__(
        self,
        *,
        on_unreachable: Callable[[StopSnapshot], None],
        on_change: Callable[[StopSnapshot], None] | None = None,
        clock: Callable[[], int] = monotonic_ns,
        max_age_ns: int = 2_000_000_000,  # [SUPUESTO] frescura técnica, no plazo para decidir
    ) -> None:
        if type(max_age_ns) is not int or max_age_ns <= 0:
            raise ValueError("Invalid route health deadline")
        self.on_unreachable, self.on_change = on_unreachable, on_change
        self.clock, self.max_age_ns = clock, max_age_ns
        self._lock = threading.RLock()
        self._routes: dict[str, _Route] = {}
        self._snapshot = StopSnapshot(False, (), 0, wall_clock_iso())
        self.notification_failures = 0
        self.halt_failures = 0

    def register(self, identifier: str, modality: Modality) -> RouteToken:
        if not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 128:
            raise ValueError("Invalid route identifier")
        if modality not in MODALITIES:
            raise ValueError("Invalid route modality")
        with self._lock:
            if identifier in self._routes:
                raise ValueError("Duplicate route")
            token = RouteToken(identifier)
            self._routes[identifier] = _Route(token, modality)
        self.snapshot()
        return token

    def _route(self, token: RouteToken) -> _Route:
        route = self._routes.get(token.identifier) if isinstance(token, RouteToken) else None
        if route is None or route.token is not token:
            raise ValueError("Unknown route")
        return route

    def renew(self, token: RouteToken) -> RouteToken:
        self.snapshot()
        with self._lock:
            route = self._route(token)
            replacement = RouteToken(token.identifier)
            self._routes[token.identifier] = _Route(replacement, route.modality)
        self.snapshot()
        return replacement

    def observe(
        self,
        token: RouteToken,
        evidence: RouteEvidence,
        *,
        observed_ns: int | None = None,
    ) -> None:
        self.snapshot()
        with self._lock:
            route = self._route(token)
            now = self.clock()
            received = now if observed_ns is None else observed_ns
            valid = (
                type(evidence) is RouteEvidence and type(received) is int and 0 <= received <= now
            )
            route.evidence = evidence if valid else None
            route.seen_ns = received if valid else None
            route.forced_reason = "starting" if valid else "adapter_unresponsive"
        self.snapshot()
        if not valid:
            raise ValueError("Invalid route health evidence")

    def fail(self, token: RouteToken, reason: Reason) -> None:
        if reason not in _FAILURES:
            raise ValueError("Invalid route failure reason")
        self.snapshot()
        with self._lock:
            route = self._route(token)
            route.evidence, route.seen_ns, route.forced_reason = None, None, reason
        self.snapshot()

    def remove(self, token: RouteToken) -> None:
        self.snapshot()
        with self._lock:
            self._route(token)
            del self._routes[token.identifier]
        self.snapshot()

    def _status(self, route: _Route, now: int) -> RouteState:
        evidence, seen = route.evidence, route.seen_ns
        reason = route.forced_reason
        if evidence is not None and seen is not None:
            if now < seen or now - seen >= self.max_age_ns:
                reason = "stale"
            elif not evidence.adapter_responding:
                reason = "adapter_unresponsive"
            elif not evidence.device_streaming:
                reason = "device_unavailable"
            elif route.modality in {"voice", "head_gesture", "gaze"} and not evidence.model_loaded:
                reason = "model_loading"
            elif not evidence.stop_bound:
                reason = "stop_unbound"
            else:
                reason = "healthy"
        return RouteState(route.token.identifier, route.modality, reason == "healthy", reason)

    def snapshot(self) -> StopSnapshot:
        with self._lock:
            now = self.clock()
            routes = tuple(self._status(route, now) for _, route in sorted(self._routes.items()))
            reachable = any(route.healthy for route in routes)
            previous = self._snapshot
            changed = routes != previous.routes or reachable != previous.stop_reachable
            if changed:
                self._snapshot = StopSnapshot(
                    reachable, routes, previous.revision + 1, wall_clock_iso()
                )
            current = self._snapshot
            lost = previous.stop_reachable and not reachable
        if lost:
            try:
                self.on_unreachable(current)
            except Exception:
                with self._lock:
                    self.halt_failures += 1
        if changed and self.on_change:
            try:
                self.on_change(current)
            except Exception:
                with self._lock:
                    self.notification_failures += 1
        return current
