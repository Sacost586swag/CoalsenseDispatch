"""Composición local cerrada al inicio; no inicia adaptadores ni expone un servidor."""

from collections.abc import Callable
from dataclasses import dataclass

from coalsense_common.ids import monotonic_ns

from ..bus.auth import AdapterRegistry
from ..bus.core import BusRecord, IntentBus
from ..bus.stop_guard import StopGuard
from ..bus.stop_state import StopSnapshot, StopState
from .guard import ActuationGate
from .halt import HaltController
from .results import ActuationResult
from .service import Backend, NativeActuator
from .target import TargetGuard, TargetProbe
from .windows import WindowsInputBackend
from .windows_target import WindowsTargetProbe


@dataclass(frozen=True, slots=True)
class ActuatorRuntime:
    bus: IntentBus
    controller: HaltController
    actuator: NativeActuator
    stop: StopGuard
    state: StopState


def create_runtime(
    registry: AdapterRegistry,
    backend: Backend,
    target: TargetProbe,
    audit: Callable[[BusRecord], None],
    feedback: Callable[[ActuationResult], None],
    *,
    approval_min_confidence: float,
    on_health: Callable[[StopSnapshot], None] | None = None,
    clock: Callable[[], int] = monotonic_ns,
) -> ActuatorRuntime:
    controller = HaltController(backend)
    stop = StopGuard(controller)
    bus = IntentBus(
        registry,
        audit,
        on_stop=stop.halt,
        approval_min_confidence=approval_min_confidence,
    )

    def lost_route(_: StopSnapshot) -> None:
        if not bus.halt():
            raise RuntimeError("Local stop cleanup failed")

    state = StopState(on_unreachable=lost_route, on_change=on_health, clock=clock)
    actuator = NativeActuator(
        bus,
        ActuationGate(bus, controller, stop_available=lambda: state.snapshot().stop_reachable),
        backend,
        TargetGuard(target),
        feedback,
    )
    return ActuatorRuntime(bus, controller, actuator, stop, state)


def create_windows_runtime(
    registry: AdapterRegistry,
    audit: Callable[[BusRecord], None],
    feedback: Callable[[ActuationResult], None],
    *,
    approval_min_confidence: float,
) -> ActuatorRuntime:
    return create_runtime(
        registry,
        WindowsInputBackend(),
        WindowsTargetProbe(),
        audit,
        feedback,
        approval_min_confidence=approval_min_confidence,
    )
