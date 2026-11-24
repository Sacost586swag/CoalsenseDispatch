"""Ciclo de vida de procesos de adaptadores (REQ-01-127).

Las factorías son configuración confiable, nunca comandos recibidos del bus. Cada
puerto debe consultar y señalar un proceso hijo sin bloquear ni esperar su cierre.
El host Windows/named pipe todavía debe implementar ese puerto y su ACL. Credenciales
y excepciones no se incluyen en estados. El bucle de aplicación debe llamar tick.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol

from coalsense_common.ids import monotonic_ns
from coalsense_intents.models import ACTOR_ORIGINS, MODALITIES, ActorOrigin, Modality

from .bus.auth import AdapterCredential, AdapterRegistry
from .bus.session import HealthReceipt
from .bus.stop_state import RouteEvidence, RouteToken, StopState

Phase = Literal["starting", "running", "backoff", "stopping", "stopped"]


@dataclass(frozen=True, slots=True)
class AdapterSpec:
    identifier: str
    modality: Modality
    actor_origin: ActorOrigin

    def __post_init__(self) -> None:
        if (
            not isinstance(self.identifier, str)
            or not self.identifier.strip()
            or len(self.identifier) > 128
            or self.modality not in MODALITIES
            or self.actor_origin not in ACTOR_ORIGINS
        ):
            raise ValueError("Invalid adapter configuration")


class AdapterProcess(Protocol):
    def is_alive(self) -> bool: ...
    def poll_health(self) -> RouteEvidence | HealthReceipt | None:
        """Solo evidencia nueva del hijo; None si no llegó un informe nuevo, sin caché."""
        ...

    def stop(self) -> None:
        """Solicitar terminación sin esperar ni invocar otros procesos del supervisor."""
        ...


type ProcessFactory = Callable[[AdapterSpec, AdapterCredential], AdapterProcess]


@dataclass(frozen=True, slots=True)
class AdapterStatus:
    identifier: str
    modality: Modality
    phase: Phase
    consecutive_failures: int


@dataclass(slots=True)
class _Managed:
    spec: AdapterSpec
    factory: ProcessFactory = field(repr=False)
    token: RouteToken
    process: AdapterProcess | None = field(default=None, repr=False)
    credential: AdapterCredential | None = field(default=None, repr=False)
    enabled: bool = True
    phase: Phase = "starting"
    failures: int = 0
    retry_at_ns: int = 0
    response_at_ns: int = 0
    reported: bool = False
    healthy_since_ns: int | None = None


class Supervisor:
    def __init__(
        self,
        registry: AdapterRegistry,
        state: StopState,
        *,
        clock: Callable[[], int] = monotonic_ns,
        on_status: Callable[[AdapterStatus], None] | None = None,
        retry_base_ns: int = 250_000_000,
        retry_cap_ns: int = 30_000_000_000,
        startup_timeout_ns: int = 30_000_000_000,
        stable_ns: int = 30_000_000_000,
        # [SUPUESTO] espera exponencial 250 ms→30 s, arranque y estabilidad 30 s.
    ) -> None:
        if (
            any(
                type(value) is not int or value <= 0
                for value in (
                    retry_base_ns,
                    retry_cap_ns,
                    startup_timeout_ns,
                    stable_ns,
                )
            )
            or retry_cap_ns < retry_base_ns
        ):
            raise ValueError("Invalid adapter lifecycle timing")
        self.registry, self.state, self.clock, self.on_status = registry, state, clock, on_status
        self.retry_base_ns, self.retry_cap_ns = retry_base_ns, retry_cap_ns
        self.startup_timeout_ns, self.stable_ns = startup_timeout_ns, stable_ns
        self._adapters: dict[str, _Managed] = {}
        self._lock = threading.RLock()
        self.notification_failures = 0
        self.cleanup_failures = 0

    def add(self, spec: AdapterSpec, factory: ProcessFactory) -> None:
        with self._lock:
            if spec.identifier in self._adapters:
                raise ValueError("Duplicate adapter")
            token = self.state.register(spec.identifier, spec.modality)
            self._adapters[spec.identifier] = _Managed(spec, factory, token)

    def snapshot(self) -> tuple[AdapterStatus, ...]:
        with self._lock:
            return tuple(self._status(item) for _, item in sorted(self._adapters.items()))

    @staticmethod
    def _status(item: _Managed) -> AdapterStatus:
        return AdapterStatus(item.spec.identifier, item.spec.modality, item.phase, item.failures)

    def _notify(self, item: _Managed) -> None:
        if self.on_status:
            try:
                self.on_status(self._status(item))
            except Exception:
                self.notification_failures += 1

    def _release_process(self, item: _Managed) -> None:
        if item.process is None:
            return
        try:
            item.process.stop()
            if item.process.is_alive() is False:
                item.process = None
        except Exception:
            self.cleanup_failures += 1

    def _failed(self, item: _Managed, now: int) -> None:
        if item.credential is not None:
            self.registry.revoke(item.credential.credential)
            item.credential = None
        self.state.fail(item.token, "adapter_unresponsive" if item.enabled else "stopped")
        item.healthy_since_ns = None
        if item.enabled:
            item.failures += 1
            delay = min(self.retry_base_ns * 2 ** min(item.failures - 1, 30), self.retry_cap_ns)
            item.retry_at_ns = now + delay
        self._release_process(item)
        item.phase = (
            "stopping" if item.process is not None else "backoff" if item.enabled else "stopped"
        )
        self._notify(item)

    def _launch(self, item: _Managed, now: int) -> None:
        item.token = self.state.renew(item.token)
        item.phase, item.reported, item.response_at_ns = "starting", False, now
        item.credential = self.registry.register(
            item.spec.identifier,
            item.spec.modality,
            item.spec.actor_origin,
        )
        try:
            item.process = item.factory(item.spec, item.credential)
            if item.process.is_alive() is not True:
                raise RuntimeError("Adapter process did not start")
        except Exception:
            self._failed(item, now)
            return
        self._notify(item)

    def stop(self, identifier: str) -> None:
        with self._lock:
            item = self._adapters[identifier]
            item.enabled = False
            self._failed(item, self.clock())

    def start(self, identifier: str) -> None:
        with self._lock:
            item = self._adapters[identifier]
            if item.enabled:
                return
            item.enabled, item.retry_at_ns, item.failures = True, self.clock(), 0
            item.phase = "stopping" if item.process is not None else "backoff"
            self._notify(item)

    def tick(self) -> None:
        with self._lock:
            for item in tuple(self._adapters.values()):
                now = self.clock()
                if item.phase == "stopping":
                    self._release_process(item)
                    if item.process is not None:
                        continue  # no duplicar un proceso que aún puede retener dispositivos
                    item.phase = "backoff" if item.enabled else "stopped"
                    self._notify(item)
                if not item.enabled:
                    continue
                if item.process is None:
                    if now < item.retry_at_ns:
                        continue
                    self._launch(item, now)
                    if item.phase != "starting":
                        continue
                if item.process is None:
                    continue
                try:
                    if item.process.is_alive() is not True:
                        raise RuntimeError("Adapter process is unavailable")
                    evidence = item.process.poll_health()
                    if evidence is None:
                        timeout = (
                            self.state.max_age_ns if item.reported else self.startup_timeout_ns
                        )
                        if now < item.response_at_ns or now - item.response_at_ns >= timeout:
                            raise RuntimeError("Adapter health response timed out")
                        continue
                    observed = evidence.received_ns if isinstance(evidence, HealthReceipt) else now
                    report = evidence.evidence if isinstance(evidence, HealthReceipt) else evidence
                    self.state.observe(item.token, report, observed_ns=observed)
                    if now - observed >= self.state.max_age_ns:
                        raise RuntimeError("Adapter health report was already stale")
                    item.response_at_ns, item.reported = observed, True
                    previous_phase = item.phase
                    previous_failures = item.failures
                    item.phase = "running"
                    healthy = any(
                        route.identifier == item.spec.identifier and route.healthy
                        for route in self.state.snapshot().routes
                    )
                    if not healthy:
                        item.healthy_since_ns = None
                    elif item.healthy_since_ns is None:
                        item.healthy_since_ns = now
                    elif now - item.healthy_since_ns >= self.stable_ns:
                        item.failures = 0
                    if item.phase != previous_phase or item.failures != previous_failures:
                        self._notify(item)
                except Exception:
                    self._failed(item, now)
        self.state.snapshot()
