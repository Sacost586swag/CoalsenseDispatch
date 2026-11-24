"""REQ-02-042/043/044: revisión exacta, consumo único y revocación."""

import asyncio
from dataclasses import replace
from uuid import UUID

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.auth.scopes import APPROVAL_DECIDE
from coalsense_orchestrator.policy.approvals import ApprovalService
from coalsense_orchestrator.policy.contexts import ExecutionContext
from coalsense_orchestrator.policy.engine import PolicyEngine
from coalsense_orchestrator.policy.grant import GrantSigner
from coalsense_orchestrator.policy.pending_action import PendingAction
from coalsense_orchestrator.policy.rules import PolicyError
from hypothesis import given
from hypothesis import strategies as st

from .test_engine import Audit, Contexts, Health, Store, principal, registry


def setup(approval_audit=None, health=None, tools=None):
    actor = principal()
    actor = replace(actor, scopes=actor.scopes | {APPROVAL_DECIDE})
    task = UUID(new_id())
    contexts = Contexts(
        ExecutionContext(UUID(actor.account_id), task, "email", "N0", "step", False, False, 1)
    )
    tools = registry() if tools is None else tools
    audit = Audit()
    policy = PolicyEngine(tools, Store(), contexts, health or Health(), audit)
    service = ApprovalService(tools, policy, approval_audit or audit, GrantSigner(b"t" * 32))
    return actor, task, service, contexts, audit


def intent(action: PendingAction, **changes: object) -> dict[str, object]:
    return {
        "id": new_id(),
        "type": "approval.approve",
        "priority": "normal",
        "actor_origin": "person",
        "modality": "keyboard_mouse",
        "adapter": "keyboard@1.0.0",
        "monotonic_ts": 0,
        "wall_ts": "2020-01-01T00:00:00.000Z",
        "confidence": 1,
        "payload": {},
        "pending_action_id": str(action.id),
        "content_digest": action.content_digest,
    } | changes


async def proposal(actor, task, service, body="Original"):
    return await service.propose(
        actor,
        task,
        "sample.action",
        "Enviar el borrador",
        ("destino@example.test",),
        {"body": body},
    )


def test_only_exact_preview_can_be_claimed_once_even_concurrently() -> None:
    async def run() -> None:
        actor, task, service, _, audit = setup()
        content = {"body": ["Original"]}
        action = await service.propose(actor, task, "sample.action", "Enviar", ("A",), content)
        content["body"][0] = "Cambiado"
        view = service.preview(actor, action.id).tool_input()
        assert isinstance(view, dict) and isinstance(view["body"], list)
        view["body"].clear()
        grant = await service.decide(actor, intent(action))
        assert grant is not None
        results = await asyncio.gather(
            service.claim(actor, grant), service.claim(actor, grant), return_exceptions=True
        )
        assert sum(isinstance(result, PendingAction) for result in results) == 1
        assert sum(isinstance(result, PolicyError) for result in results) == 1
        accepted = next(result for result in results if isinstance(result, PendingAction))
        assert accepted.tool_input() == {"body": ["Original"]}
        assert "Original" not in repr(action) + repr(audit.events)
        assert grant.signature not in repr(grant)
        assert "expires_at" not in vars(grant)

    asyncio.run(run())


@given(st.text(max_size=30))
def test_content_change_retires_existing_grant_and_requires_new_review(text: str) -> None:
    async def run() -> None:
        actor, task, service, _, _ = setup()
        original = await proposal(actor, task, service, text)
        grant = await service.decide(actor, intent(original))
        assert grant is not None
        changed = await service.revise(
            actor, original.id, original.summary, original.destinations, {"body": text + "a"}
        )
        assert changed.content_digest != original.content_digest
        with pytest.raises(PolicyError):
            await service.claim(actor, grant)
        with pytest.raises(PolicyError, match="approval.intent.mismatch"):
            await service.decide(actor, intent(changed, content_digest=original.content_digest))

    asyncio.run(run())


def test_foreign_actor_edit_and_tampered_signature_cannot_consume() -> None:
    async def run() -> None:
        actor, task, service, _, _ = setup()
        action = await proposal(actor, task, service)
        stranger = replace(actor, account_id=new_id(), session_id=new_id())
        with pytest.raises(PolicyError):
            service.preview(stranger, action.id)
        with pytest.raises(PolicyError):
            await service.decide(stranger, intent(action))
        with pytest.raises(PolicyError, match="approval.actor.denied"):
            await service.decide(actor, intent(action, actor_origin="system"))
        grant = await service.decide(actor, intent(action))
        assert grant is not None
        for claimant, seal in (
            (actor, replace(grant, content_digest="0" * 64)),
            (replace(actor, session_id=new_id()), grant),
            (stranger, grant),
        ):
            with pytest.raises(PolicyError, match="approval.grant.denied"):
                await service.claim(claimant, seal)
        assert await service.claim(actor, grant) == action

    asyncio.run(run())


@pytest.mark.parametrize("change", ["stop", "revision", "pause"])
def test_live_context_revokes_an_issued_grant(change: str) -> None:
    async def run() -> None:
        actor, task, service, contexts, _ = setup()
        action = await proposal(actor, task, service)
        grant = await service.decide(actor, intent(action))
        assert grant is not None
        if change == "stop":
            service.stop(actor)
        elif change == "revision":
            contexts.context = replace(contexts.context, revision=2)
        else:
            contexts.context = replace(contexts.context, paused=True)
        with pytest.raises(PolicyError):
            await service.claim(actor, grant)

    asyncio.run(run())


def test_stop_during_audit_prevents_returning_a_grant() -> None:
    class BlockingAudit(Audit):
        def __init__(self) -> None:
            super().__init__()
            self.started = asyncio.Event()
            self.released = asyncio.Event()

        async def append(self, actor, draft):
            self.started.set()
            await self.released.wait()
            return await super().append(actor, draft)

    async def run() -> None:
        audit = BlockingAudit()
        actor, task, service, _, _ = setup(approval_audit=audit)
        action = await proposal(actor, task, service)
        approval = asyncio.create_task(service.decide(actor, intent(action)))
        await asyncio.wait_for(audit.started.wait(), timeout=1)
        service.stop(actor)
        audit.released.set()
        with pytest.raises(PolicyError, match="approval.action.unavailable"):
            await approval

    asyncio.run(run())


def test_rejection_removes_preview_and_audit_failure_cannot_issue_seal() -> None:
    class BrokenAudit(Audit):
        async def append(self, actor, draft):
            raise RuntimeError("contenido privado")

    async def run() -> None:
        actor, task, service, _, _ = setup(approval_audit=BrokenAudit())
        action = await proposal(actor, task, service)
        with pytest.raises(PolicyError, match="approval.audit.unavailable"):
            await service.decide(actor, intent(action))
        with pytest.raises(PolicyError, match="approval.audit.unavailable"):
            await service.decide(actor, intent(action, type="approval.reject"))
        with pytest.raises(PolicyError, match="approval.action.unavailable"):
            service.preview(actor, action.id)
        actor, task, service, _, _ = setup()
        action = await proposal(actor, task, service)
        assert await service.decide(actor, intent(action, type="approval.reject")) is None
        with pytest.raises(PolicyError, match="approval.action.unavailable"):
            await service.decide(actor, intent(action))

    asyncio.run(run())
