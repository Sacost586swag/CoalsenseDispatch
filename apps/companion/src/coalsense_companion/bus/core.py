"""Validación y entrega local con dos clases de prioridad (REQ-01-004 a 014).

Publicar no ejecuta consumidores. Alto llama al puerto de detención antes de encolar,
fuera del bloqueo de la cola. Un consumidor lento no puede bloquear ese puerto.
Solo movimientos continuos se descartan al alcanzar la capacidad de referencia;
los controles y las aprobaciones no tienen un límite que los descarte.
"""

import threading
from collections import deque
from collections.abc import Callable, Iterable
from copy import deepcopy
from dataclasses import dataclass, field

from coalsense_intents import (
    ContractError,
    Intent,
    intent_types,
    priority_for,
    validate_intent,
)

from .approval_guard import ApprovalFeedback, ApprovalGuard
from .auth import AdapterRegistry, AdapterSession
from .coalescing import coalesce
from .priority import preemptive


@dataclass(frozen=True, slots=True)
class BusRecord:
    event: str
    result: str
    intent_id: str | None = None
    intent_type: str | None = None
    modality: str | None = None
    actor_origin: str | None = None
    adapter: str | None = None


@dataclass(frozen=True, slots=True)
class PublishResult:
    accepted: bool
    status: str


@dataclass(slots=True)
class _DeliveryPermit:
    claimed: bool = False


@dataclass(frozen=True, slots=True)
class BusDelivery:
    intent: Intent = field(repr=False)
    generation: int
    _authority: object = field(repr=False)
    _permit: _DeliveryPermit = field(default_factory=_DeliveryPermit, repr=False)


@dataclass(slots=True)
class _Queued:
    intent: Intent = field(repr=False)
    generation: int


@dataclass(frozen=True, slots=True, eq=False)
class _Subscription:
    types: frozenset[str]
    consumer: Callable[[BusDelivery], None]


class IntentBus:
    def __init__(
        self,
        registry: AdapterRegistry,
        audit: Callable[[BusRecord], None],
        *,
        on_stop: Callable[[], None],
        approval_min_confidence: float,
        on_approval_feedback: Callable[[ApprovalFeedback], None] | None = None,
        normal_capacity: int = 256,  # [SUPUESTO] umbral de coalescencia; no limita controles
    ) -> None:
        if isinstance(normal_capacity, bool) or normal_capacity < 1:
            raise ValueError("Invalid queue capacity")
        self.registry, self.audit, self.on_stop = registry, audit, on_stop
        self.approvals = ApprovalGuard(approval_min_confidence)
        self.on_approval_feedback = on_approval_feedback
        self.normal_capacity = normal_capacity
        self._preemptive: deque[_Queued] = deque()
        self._normal: deque[_Queued] = deque()
        self._subscriptions: list[_Subscription] = []
        self._lock = threading.RLock()
        self._authority = object()
        self._generation = 0
        self._stopping = 0
        self.audit_failures = 0
        self.feedback_failures = 0
        self.last_halt_failed: bool | None = None

    def _record(
        self,
        event: str,
        result: str,
        intention: Intent | None = None,
        session: AdapterSession | None = None,
    ) -> None:
        record = BusRecord(
            event,
            result,
            intention["id"] if intention else None,
            intention["type"] if intention else None,
            intention["modality"] if intention else session.modality if session else None,
            intention["actor_origin"] if intention else session.actor_origin if session else None,
            intention["adapter"] if intention else session.adapter if session else None,
        )
        try:
            self.audit(record)
        except Exception:
            # Alto no depende de la bitácora. La composición debe observar este fallo.
            with self._lock:
                self.audit_failures += 1

    def publish(self, raw: object, credential: str) -> PublishResult:
        session = self.registry.authenticate(credential)
        if session is None:
            self._record("bus.publish", "unauthenticated")
            return PublishResult(False, "unauthenticated")
        try:
            if not isinstance(raw, dict) or not isinstance(raw.get("type"), str):
                raise ContractError("Invalid intention")
            candidate = raw | {
                "modality": session.modality,
                "adapter": session.adapter,
                "actor_origin": session.actor_origin,
                "priority": priority_for(raw["type"]),
            }
            intention = validate_intent(candidate)
        except ContractError:
            self._record("bus.publish", "invalid", session=session)
            return PublishResult(False, "invalid")
        if intention["type"] == "approval.approve" and session.actor_origin == "system":
            self._record("bus.publish", "system_approval", intention)
            return PublishResult(False, "system_approval")
        feedback = self.approvals.check(intention)
        if feedback is not None:
            self._record("bus.publish", "approval_uncertain", intention)
            if self.on_approval_feedback:
                try:
                    self.on_approval_feedback(feedback)
                except Exception:
                    self.feedback_failures += 1
            return PublishResult(False, "approval_uncertain")
        status = "queued"
        if intention["type"] == "control.stop":
            status = self._halt(intention)
            self._record("bus.publish", status, intention)
            return PublishResult(True, status)
        with self._lock:
            generation = self._generation
            queued = _Queued(intention, generation)
            if preemptive(intention["type"]):
                self._preemptive.append(queued)
            elif intention["type"] == "pointer.move" and len(self._normal) >= self.normal_capacity:
                previous = self._normal[-1] if self._normal else None
                merged = (
                    coalesce(previous.intent, intention)
                    if previous is not None and previous.generation == generation
                    else None
                )
                if merged is None:
                    status = "dropped_continuous"
                else:
                    self._normal[-1] = _Queued(merged, generation)
                    status = "coalesced"
            else:
                self._normal.append(queued)
        self._record("bus.publish", status, intention)
        return PublishResult(status != "dropped_continuous", status)

    def _halt(self, intention: Intent | None = None) -> str:
        with self._lock:
            self._generation += 1
            generation = self._generation
            self._stopping += 1
        status = "queued"
        try:
            self.on_stop()
            self.last_halt_failed = False
        except Exception:
            self.last_halt_failed = True
            status = "stop_fault"
        finally:
            with self._lock:
                if intention is not None:
                    self._preemptive.append(_Queued(intention, generation))
                self._stopping -= 1
        return status

    def halt(self) -> bool:
        """Puerto interno de pérdida de salud: invalida también la cola anterior.

        No fabrica una intención de la persona ni expone una ruta a agentes.
        """
        status = self._halt()
        self._record("bus.halt", "halted" if status != "stop_fault" else status)
        return status != "stop_fault"

    def subscribe(
        self, types: Iterable[str], consumer: Callable[[Intent], None]
    ) -> Callable[[], None]:
        return self.subscribe_bound(types, lambda delivery: consumer(delivery.intent))

    def subscribe_bound(
        self, types: Iterable[str], consumer: Callable[[BusDelivery], None]
    ) -> Callable[[], None]:
        requested = frozenset(types)
        if not requested or not requested <= intent_types():
            raise ValueError("Unknown subscription types")
        subscription = _Subscription(requested, consumer)
        with self._lock:
            self._subscriptions.append(subscription)

        def unsubscribe() -> None:
            with self._lock:
                if subscription in self._subscriptions:
                    self._subscriptions.remove(subscription)

        return unsubscribe

    def current_delivery(self, delivery: object) -> bool:
        with self._lock:
            return (
                isinstance(delivery, BusDelivery)
                and delivery._authority is self._authority
                and delivery.generation == self._generation
                and not self._stopping
            )

    def claim_delivery(self, delivery: object) -> bool:
        with self._lock:
            if not isinstance(delivery, BusDelivery) or not self.current_delivery(delivery):
                return False
            if delivery._permit.claimed:
                return False
            delivery._permit.claimed = True
            return True

    def drain_one(self) -> Intent | None:
        with self._lock:
            if not self._preemptive and not self._normal:
                return None
            queued = (self._preemptive or self._normal).popleft()
            intention = queued.intent
            subscribers = tuple(self._subscriptions)
        for subscription in subscribers:
            if intention["type"] not in subscription.types:
                continue
            try:
                subscription.consumer(
                    BusDelivery(
                        deepcopy(intention),
                        queued.generation,
                        self._authority,
                    )
                )
            except Exception:
                self._record("bus.deliver", "consumer_failed", intention)
        self._record("bus.deliver", "delivered", intention)
        return intention

    def drain(self) -> list[Intent]:
        delivered = []
        while (intention := self.drain_one()) is not None:
            delivered.append(intention)
        return delivered
