"""Ciclo interno de aprobación. La vista y el sello viven en memoria del servidor."""

import asyncio
import hmac
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from uuid import UUID

from coalsense_common import new_id
from coalsense_intents import ContractError, validate_intent

from coalsense_orchestrator.audit.events import AuditDraft, AuditRefs, EventResult
from coalsense_orchestrator.auth.scopes import APPROVAL_DECIDE, CONTENT_READ
from coalsense_orchestrator.auth.sessions import Principal
from coalsense_orchestrator.gateway.registry import ToolRegistry

from .engine import PolicyEngine
from .grant import ApprovalGrant, GrantSigner
from .pending_action import PendingAction, prepare_action
from .rules import EvaluationRequest, PolicyDecision, PolicyError
from .versions import AuditSink


def _identity(actor: Principal, scope: str) -> tuple[UUID, UUID]:
    if type(actor) is Principal and actor.role == "person" and scope in actor.scopes:
        try:
            return UUID(actor.account_id), UUID(actor.session_id)
        except (ValueError, TypeError, AttributeError):
            pass
    raise PolicyError("approval.actor.denied")


@dataclass
class _Entry:
    owner: UUID
    action: PendingAction = field(repr=False)
    decision: PolicyDecision
    grant: ApprovalGrant | None = field(default=None, repr=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class ApprovalService:
    """Instancia para un único event loop. Reiniciar invalida toda aprobación pendiente."""

    def __init__(
        self, registry: ToolRegistry, policy: PolicyEngine, audit: AuditSink, signer: GrantSigner
    ) -> None:
        self._registry, self._policy, self._audit, self._signer = registry, policy, audit, signer
        self._entries: dict[UUID, _Entry] = {}
        self._stops: dict[UUID, int] = {}

    async def propose(
        self,
        actor: Principal,
        task_id: UUID,
        tool_name: str,
        summary: str,
        destinations: tuple[str, ...],
        value: object,
    ) -> PendingAction:
        owner, _ = _identity(actor, CONTENT_READ)
        generation = self._stops.get(owner, 0)
        action_id = UUID(new_id())
        request = EvaluationRequest(action_id, task_id, tool_name)
        manifest = self._registry.get(tool_name)
        action = prepare_action(action_id, task_id, manifest, summary, destinations, value)
        decision = await self._policy.evaluate(actor, request)
        if (
            decision.verdict != "require_approval"
            or decision.policy_digest is None
            or decision.effect_class != manifest.effect_class
            or self._stops.get(owner, 0) != generation
        ):
            raise PolicyError("approval.proposal.denied")
        self._entries[action_id] = _Entry(owner, action, decision)
        return action

    def preview(self, actor: Principal, action_id: UUID) -> PendingAction:
        owner, _ = _identity(actor, CONTENT_READ)
        return self._owned(owner, action_id).action

    def invalidate(self, actor: Principal, action_id: UUID) -> None:
        """Retira la vista y el sello antes de proponer una edición con un ID nuevo."""
        owner, _ = _identity(actor, CONTENT_READ)
        self._owned(owner, action_id)
        del self._entries[action_id]

    async def revise(
        self,
        actor: Principal,
        action_id: UUID,
        summary: str,
        destinations: tuple[str, ...],
        value: object,
    ) -> PendingAction:
        previous = self.preview(actor, action_id)
        self.invalidate(actor, action_id)
        return await self.propose(
            actor, previous.task_id, previous.tool_name, summary, destinations, value
        )

    def stop(self, actor: Principal) -> None:
        owner, _ = _identity(actor, CONTENT_READ)
        self._stops[owner] = self._stops.get(owner, 0) + 1
        for action_id in [i for i, entry in self._entries.items() if entry.owner == owner]:
            del self._entries[action_id]

    async def decide(self, actor: Principal, value: object) -> ApprovalGrant | None:
        """Recibe una intención validada, atribuida por el transporte autenticado."""
        try:
            intent = validate_intent(value)
        except ContractError:
            intent = None
        if intent is None or intent["type"] not in ("approval.approve", "approval.reject"):
            raise PolicyError("approval.intent.invalid")
        if intent["actor_origin"] != "person":
            await self._record(actor, "denied", None)
            raise PolicyError("approval.actor.denied")
        try:
            owner, session = _identity(actor, APPROVAL_DECIDE)
            entry = self._owned(owner, UUID(intent["pending_action_id"]))
        except PolicyError:
            await self._record(actor, "denied", None)
            raise
        async with entry.lock:
            self._current(entry)
            if entry.grant is not None or not hmac.compare_digest(
                entry.action.content_digest, intent["content_digest"]
            ):
                await self._record(actor, "denied", entry)
                raise PolicyError("approval.intent.mismatch")
            if intent["type"] == "approval.reject":
                del self._entries[entry.action.id]
                await self._record(actor, "denied", entry)
                return None
            await self._revalidate(actor, entry)
            decision = entry.decision
            assert decision.policy_digest is not None and decision.context_revision is not None
            grant = self._signer.sign(
                ApprovalGrant(
                    entry.action.id,
                    owner,
                    session,
                    entry.action.content_digest,
                    decision.policy_digest,
                    decision.context_revision,
                )
            )
            await self._record(actor, "ok", entry)
            self._current(entry)
            entry.grant = grant
            return grant

    async def claim(
        self,
        actor: Principal,
        grant: ApprovalGrant,
        *,
        before_consume: Callable[[], Awaitable[None]] | None = None,
    ) -> PendingAction:
        """Consume el sello una vez y devuelve la única entrada que se aprobó."""
        owner, session = _identity(actor, APPROVAL_DECIDE)
        if not self._signer.verify(grant) or (grant.person_id, grant.session_id) != (
            owner,
            session,
        ):
            raise PolicyError("approval.grant.denied")
        entry = self._owned(owner, grant.pending_action_id)
        async with entry.lock:
            self._current(entry)
            if entry.grant != grant:
                raise PolicyError("approval.grant.denied")
            await self._revalidate(actor, entry)
            if before_consume is not None:
                await before_consume()
            self._current(entry)
            del self._entries[entry.action.id]
            return entry.action

    def _owned(self, owner: UUID, action_id: UUID) -> _Entry:
        entry = self._entries.get(action_id)
        if entry is None or entry.owner != owner:
            raise PolicyError("approval.action.unavailable")
        return entry

    def _current(self, entry: _Entry) -> None:
        if self._entries.get(entry.action.id) is not entry:
            raise PolicyError("approval.action.unavailable")

    async def _revalidate(self, actor: Principal, entry: _Entry) -> None:
        action = entry.action
        current = await self._policy.evaluate(
            actor, EvaluationRequest(action.id, action.task_id, action.tool_name)
        )
        self._current(entry)
        original = entry.decision
        if (
            current.verdict != "require_approval"
            or current.policy_digest != original.policy_digest
            or current.context_revision != original.context_revision
            or current.effect_class != original.effect_class
        ):
            del self._entries[action.id]
            raise PolicyError("approval.context.changed")

    async def _record(self, actor: Principal, result: EventResult, entry: _Entry | None) -> None:
        recorded = False
        try:
            refs = AuditRefs(
                pending_action_id=entry.action.id if entry else None,
                task_id=entry.action.task_id if entry else None,
                tool_name=entry.action.tool_name if entry else None,
                effect_class=entry.decision.effect_class if entry else None,
                policy_version=entry.decision.policy_version if entry else None,
                actor_id=UUID(actor.account_id),
                session_id=UUID(actor.session_id),
                actor_origin=(
                    "person"
                    if actor.role == "person"
                    else "caregiver"
                    if actor.role == "caregiver"
                    else None
                ),
            )
            # [SUPUESTO] Plazo técnico del registro, no de la decisión humana.
            async with asyncio.timeout(2):
                recorded = (
                    type(await self._audit.append(actor, AuditDraft("approval", result, refs)))
                    is UUID
                )
        except Exception:
            pass
        if not recorded:
            raise PolicyError("approval.audit.unavailable")
