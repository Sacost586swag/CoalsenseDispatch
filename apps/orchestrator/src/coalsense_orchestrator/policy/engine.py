"""Evaluación cerrada y auditada. El gateway deberá revalidar antes de despachar."""

import asyncio
import math
from uuid import UUID

from coalsense_intents.models import ToolEffectClass

from coalsense_orchestrator.audit.events import AuditDraft, AuditRefs, EventResult
from coalsense_orchestrator.auth.scopes import CONTENT_READ, CONTENT_WRITE
from coalsense_orchestrator.auth.sessions import Principal
from coalsense_orchestrator.gateway.registry import ToolRegistry

from .autonomy import choose_rule
from .contexts import ContextLookup, ExecutionContext
from .health import StopHealth
from .loader import PolicySnapshot
from .rules import EvaluationRequest, PolicyDecision, PolicyError, Verdict
from .versions import AuditSink, PolicyLookup

_RESULTS: dict[Verdict, EventResult] = {
    "allow": "ok",
    "require_approval": "pending",
    "deny": "denied",
}


class PolicyEngine:
    def __init__(
        self,
        registry: ToolRegistry,
        policies: PolicyLookup,
        contexts: ContextLookup,
        health: StopHealth,
        audit: AuditSink,
        *,
        timeout_s: float = 2.0,
    ) -> None:
        # [SUPUESTO] Plazo técnico de consulta y de registro, nunca de una decisión humana.
        if type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or timeout_s <= 0:
            raise PolicyError("policy.configuration.invalid")
        self._registry, self._policies, self._contexts = registry, policies, contexts
        self._health, self._audit, self._timeout = health, audit, timeout_s

    async def evaluate(self, principal: Principal, request: EvaluationRequest) -> PolicyDecision:
        verdict: Verdict = "deny"
        rule_id = "guard.unavailable"
        snapshot: PolicySnapshot | None = None
        context: ExecutionContext | None = None
        tool_name: str | None = None
        effect: ToolEffectClass = "external_effect"
        action_id = request.action_id if type(request) is EvaluationRequest else None
        requested_task = request.task_id if type(request) is EvaluationRequest else None
        try:
            async with asyncio.timeout(self._timeout):
                if (
                    type(principal) is not Principal
                    or principal.role != "person"
                    or CONTENT_READ not in principal.scopes
                ):
                    rule_id = "guard.actor"
                elif type(request) is not EvaluationRequest:
                    rule_id = "guard.request"
                else:
                    manifest = self._registry.get(request.tool_name)
                    tool_name, effect = manifest.name, manifest.effect_class
                    candidate = await self._policies.active_policy(principal)
                    if type(candidate) is not PolicySnapshot:
                        rule_id = "guard.policy_missing"
                    else:
                        snapshot = candidate
                        candidate_context = await self._contexts.lookup(principal, request)
                        if (
                            type(candidate_context) is not ExecutionContext
                            or candidate_context.person_id != UUID(principal.account_id)
                            or candidate_context.task_id != request.task_id
                        ):
                            rule_id = "guard.context"
                        else:
                            context = candidate_context
                            if context.paused:
                                rule_id = "guard.paused"
                            elif effect != "read" and CONTENT_WRITE not in principal.scopes:
                                rule_id = "guard.scope"
                            elif await self._health.reachable(principal) is not True:
                                rule_id = "guard.stop_unreachable"
                            else:
                                verdict, rule_id = choose_rule(snapshot, context, effect)
        except Exception:
            verdict, rule_id = "deny", "guard.unavailable"
        audit_id: UUID | None = None
        try:
            event = AuditDraft(
                "policy",
                _RESULTS[verdict],
                AuditRefs(
                    task_id=context.task_id if context else None,
                    action_id=action_id,
                    tool_name=tool_name,
                    effect_class=effect,
                    rule_id=rule_id,
                    policy_version=snapshot.version if snapshot else None,
                    actor_id=UUID(principal.account_id),
                    actor_origin=(
                        "person"
                        if principal.role == "person"
                        else "caregiver"
                        if principal.role == "caregiver"
                        else None
                    ),
                ),
            )
            async with asyncio.timeout(self._timeout):
                candidate_id = await self._audit.append(principal, event)
                if type(candidate_id) is not UUID:
                    raise PolicyError("policy.audit.unavailable")
                audit_id = candidate_id
        except Exception:
            verdict, rule_id = "deny", "guard.audit_unavailable"
        return PolicyDecision(
            verdict,
            rule_id,
            snapshot.version if snapshot else None,
            audit_id,
            action_id,
            requested_task,
            tool_name,
            effect,
            context.revision if context else None,
            snapshot.digest if snapshot else None,
        )
