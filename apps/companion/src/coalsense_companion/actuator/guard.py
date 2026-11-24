"""Una actuación requiere entrega del bus, generación vigente y autorización local."""

from collections.abc import Callable
from dataclasses import dataclass, field

from ..bus.core import BusDelivery, IntentBus
from .halt import ActuationBlocked, ActuationLease, HaltController


@dataclass(frozen=True, slots=True)
class ActuationTicket:
    lease: ActuationLease
    delivery: BusDelivery = field(repr=False)


class ActuationGate:
    def __init__(
        self,
        bus: IntentBus,
        controller: HaltController,
        *,
        stop_available: Callable[[], bool] | None = None,
    ) -> None:
        self.bus, self.controller = bus, controller
        self.stop_available = stop_available

    def _check_stop(self, kind: str) -> None:
        if kind in {"control.undo", "input.pause"} or self.stop_available is None:
            return
        try:
            available = self.stop_available() is True
        except Exception:
            available = False
        if not available:
            raise ActuationBlocked()

    def begin(
        self,
        delivery: object,
        kind: str,
        *,
        cancel: Callable[[], None] | None = None,
    ) -> ActuationTicket:
        if (
            not isinstance(delivery, BusDelivery)
            or (
                delivery.intent["actor_origin"] == "system"
                and delivery.intent["type"] != "input.pause"
            )
            or not self.bus.claim_delivery(delivery)
        ):
            raise ActuationBlocked()
        self._check_stop(delivery.intent["type"])
        lease = self.controller.begin(
            kind,
            cancel=cancel,
            while_paused=delivery.intent["type"] == "control.undo",
        )
        if not self.bus.current_delivery(delivery):
            self.controller.finish(lease)
            raise ActuationBlocked()
        return ActuationTicket(lease, delivery)

    def step[T](self, ticket: ActuationTicket, operation: Callable[[], T]) -> T:
        # Consultar salud antes de tomar el bloqueo de primitivas: expirar una ruta
        # puede invocar Alto y no debe invertir los bloqueos del controlador.
        self._check_stop(ticket.delivery.intent["type"])

        def guarded() -> T:
            if not self.bus.current_delivery(ticket.delivery):
                raise ActuationBlocked()
            return operation()

        return self.controller.step(ticket.lease, guarded)

    def finish(self, ticket: ActuationTicket) -> None:
        self.controller.finish(ticket.lease)

    def resume(self, delivery: object) -> None:
        if (
            not isinstance(delivery, BusDelivery)
            or delivery.intent["type"] != "input.resume"
            or delivery.intent["actor_origin"] == "system"
            or not self.bus.claim_delivery(delivery)
        ):
            raise ActuationBlocked()
        self._check_stop("input.resume")
        self.controller.resume()
        try:
            self._check_stop("input.resume")
            current = self.bus.current_delivery(delivery)
        except ActuationBlocked:
            current = False
        if not current:
            self.controller.halt()
            raise ActuationBlocked()
