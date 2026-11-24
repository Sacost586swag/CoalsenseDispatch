"""REQ-02-040/041/047/049/052/053: política independiente del agente y auditada."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.audit.events import AuditDraft
from coalsense_orchestrator.auth.scopes import CONTENT_READ, CONTENT_WRITE
from coalsense_orchestrator.auth.sessions import Principal
from coalsense_orchestrator.gateway.registry import ToolRegistry
from coalsense_orchestrator.policy.contexts import ExecutionContext
from coalsense_orchestrator.policy.engine import EvaluationRequest, PolicyEngine
from coalsense_orchestrator.policy.loader import load_policy, parse_policy
from coalsense_orchestrator.policy.rules import PolicyError
from hypothesis import given
from hypothesis import strategies as st

CONFIG = Path(__file__).resolve().parents[2] / "config/policies/default.yaml"


def principal() -> Principal:
    return Principal(
        new_id(), new_id(), new_id(), "person", frozenset({CONTENT_READ, CONTENT_WRITE})
    )


def registry(effect: str = "external_effect") -> ToolRegistry:
    result = ToolRegistry()
    result.register(
        {
            "name": "sample.action",
            "input_schema": {},
            "output_schema": {},
            "effect_class": effect,
            "reversible": False,
            "data_categories": [],
            "provider": "local",
        }
    )
    return result


class Store:
    async def active_policy(self, actor: Principal):
        return load_policy(CONFIG)


class Contexts:
    def __init__(self, context: ExecutionContext) -> None:
        self.context = context

    async def lookup(self, actor: Principal, request: EvaluationRequest) -> ExecutionContext:
        return self.context


class Health:
    async def reachable(self, actor: Principal) -> bool:
        return True


class Audit:
    def __init__(self) -> None:
        self.events: list[AuditDraft] = []

    async def append(self, actor: Principal, draft: AuditDraft) -> UUID:
        self.events.append(draft)
        return UUID(new_id())


def scenario(effect: str = "external_effect", *, level: str = "N0", stage: str = "step"):
    actor = principal()
    request = EvaluationRequest(UUID(new_id()), UUID(new_id()), "sample.action")
    context = ExecutionContext(
        UUID(actor.account_id),
        request.task_id,
        "email",
        level,
        stage,
        False,
        False,
        1,
    )
    audit = Audit()
    engine = PolicyEngine(registry(effect), Store(), Contexts(context), Health(), audit)
    return actor, request, context, audit, engine


@pytest.mark.parametrize("level", ["N0", "N1", "N2"])
@pytest.mark.parametrize("stage", ["step", "final"])
def test_external_effect_requires_approval_at_every_level(level: str, stage: str) -> None:
    actor, request, _, audit, engine = scenario(level=level, stage=stage)
    decision = asyncio.run(engine.evaluate(actor, request))
    assert decision.verdict == "require_approval" and decision.audit_event_id is not None
    assert audit.events[-1].refs.action_id == request.action_id
    assert audit.events[-1].refs.rule_id == decision.rule_id
    assert audit.events[-1].refs.policy_version == decision.policy_version == 1


@pytest.mark.parametrize("effect", ["read", "internal_write"])
@pytest.mark.parametrize("level", ["N0", "N1", "N2"])
@pytest.mark.parametrize("stage", ["step", "final"])
def test_internal_steps_follow_the_declared_autonomy_table(
    effect: str, level: str, stage: str
) -> None:
    actor, request, _, _, engine = scenario(effect, level=level, stage=stage)
    decision = asyncio.run(engine.evaluate(actor, request))
    expected = "require_approval" if level == "N0" or stage == "final" else "allow"
    assert decision.verdict == expected


def test_first_task_never_uses_a_higher_level() -> None:
    actor, request, context, audit, _ = scenario("read", level="N2")
    engine = PolicyEngine(
        registry("read"), Store(), Contexts(replace(context, first_task=True)), Health(), audit
    )
    assert asyncio.run(engine.evaluate(actor, request)).verdict == "require_approval"


@pytest.mark.parametrize(
    "field", ["effect_class", "autonomy", "stop_reachable", "stage", "profile"]
)
def test_request_cannot_claim_an_effect_health_or_an_autonomy_level(field: str) -> None:
    with pytest.raises(PolicyError, match="^policy.request.invalid$"):
        EvaluationRequest.from_payload(
            {
                "action_id": new_id(),
                "task_id": new_id(),
                "tool_name": "sample.action",
                field: True,
            }
        )


def test_permissive_external_policy_is_rejected_before_activation() -> None:
    payload = json.loads(CONFIG.read_text("utf-8"))
    payload["rules"]["external_effect"]["decision"] = "allow"
    with pytest.raises(PolicyError, match="^policy.configuration.invalid$"):
        parse_policy(payload)


@given(st.sampled_from(["N0", "N1", "N2"]), st.sampled_from(["step", "final"]))
def test_external_approval_is_not_a_configurable_autonomy_exception(level: str, stage: str) -> None:
    actor, request, _, _, engine = scenario(level=level, stage=stage)
    assert asyncio.run(engine.evaluate(actor, request)).verdict != "allow"


def test_unreachable_or_failing_stop_health_denies_and_records_no_private_error() -> None:
    class Missing:
        async def reachable(self, actor: Principal) -> bool:
            return False

    class Broken:
        async def reachable(self, actor: Principal) -> bool:
            raise RuntimeError("Contenido privado")

    for health in (Missing(), Broken()):
        actor, request, context, audit, _ = scenario("read", level="N1")
        engine = PolicyEngine(registry("read"), Store(), Contexts(context), health, audit)
        decision = asyncio.run(engine.evaluate(actor, request))
        assert decision.verdict == "deny" and audit.events[-1].result == "denied"
        assert "privado" not in repr(decision) + repr(audit.events)


def test_policy_failure_or_no_response_denies_without_a_cached_permission() -> None:
    class BrokenStore:
        async def active_policy(self, actor: Principal):
            raise RuntimeError("Contenido privado")

    class UnresponsiveStore:
        async def active_policy(self, actor: Principal):
            await asyncio.Event().wait()

    for store in (BrokenStore(), UnresponsiveStore()):
        actor, request, context, audit, _ = scenario("read", level="N1")
        engine = PolicyEngine(
            registry("read"), store, Contexts(context), Health(), audit, timeout_s=0.02
        )
        decision = asyncio.run(engine.evaluate(actor, request))
        assert decision.verdict == "deny" and decision.audit_event_id is not None


def test_audit_failure_or_timeout_never_returns_allow_or_approval() -> None:
    class BrokenAudit:
        async def append(self, actor: Principal, draft: AuditDraft) -> UUID:
            raise RuntimeError("Contenido privado")

    class UnresponsiveAudit:
        async def append(self, actor: Principal, draft: AuditDraft) -> UUID:
            await asyncio.Event().wait()
            return UUID(new_id())

    for audit in (BrokenAudit(), UnresponsiveAudit()):
        actor, request, context, _, _ = scenario("read", level="N1")
        engine = PolicyEngine(
            registry("read"), Store(), Contexts(context), Health(), audit, timeout_s=0.02
        )
        decision = asyncio.run(engine.evaluate(actor, request))
        assert decision.verdict == "deny" and decision.audit_event_id is None
        assert decision.rule_id == "guard.audit_unavailable"


def test_a_context_for_another_person_or_task_is_not_trusted() -> None:
    actor, request, context, audit, _ = scenario("read", level="N1")
    for changed in (
        replace(context, person_id=UUID(new_id())),
        replace(context, task_id=UUID(new_id())),
    ):
        engine = PolicyEngine(registry("read"), Store(), Contexts(changed), Health(), audit)
        decision = asyncio.run(engine.evaluate(actor, request))
        assert decision.verdict == "deny"
        assert audit.events[-1].refs.task_id is None


@pytest.mark.parametrize("role", ["operator", "caregiver", "company", "system"])
def test_other_roles_do_not_gain_permissions_or_get_misattributed_as_the_person(role: str) -> None:
    actor, request, _, audit, engine = scenario("read", level="N1")
    decision = asyncio.run(engine.evaluate(replace(actor, role=role), request))
    assert decision.verdict == "deny"
    assert audit.events[-1].refs.actor_origin != "person"


def test_unknown_tool_is_denied_without_recording_a_client_supplied_name() -> None:
    actor, request, _, audit, engine = scenario("read", level="N1")
    decision = asyncio.run(
        engine.evaluate(actor, replace(request, tool_name="unregistered.private"))
    )
    assert decision.verdict == "deny" and decision.tool_name is None
    assert audit.events[-1].refs.tool_name is None


def test_cancellation_during_evaluation_does_not_turn_into_a_permission() -> None:
    class CancelledHealth:
        async def reachable(self, actor: Principal) -> bool:
            raise asyncio.CancelledError

    actor, request, context, audit, _ = scenario("read", level="N1")
    engine = PolicyEngine(registry("read"), Store(), Contexts(context), CancelledHealth(), audit)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(engine.evaluate(actor, request))
    assert not audit.events
