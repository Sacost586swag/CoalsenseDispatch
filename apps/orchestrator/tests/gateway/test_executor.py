"""Efectos simulados, con aprobaciones y políticas reales."""

import asyncio
from uuid import uuid4

import pytest
from coalsense_intents.models import JsonValue
from coalsense_orchestrator.consent.models import ConsentNotice
from coalsense_orchestrator.consent.service import ConsentService
from coalsense_orchestrator.gateway.executor import DispatchError, ExternalExecutor
from coalsense_orchestrator.gateway.registry import ToolRegistry
from coalsense_orchestrator.policy.grant import GrantSigner
from coalsense_orchestrator.policy.rules import PolicyError

from ..consent.test_consent import Store
from ..policy.test_grant import intent, proposal, setup


class Adapter:
    def __init__(self) -> None:
        self.sent: list[tuple[JsonValue, str]] = []

    async def execute(self, value: JsonValue, *, idempotency_key: str) -> object:
        self.sent.append((value, idempotency_key))
        return {"accepted": True}


class Consent:
    async def check(self, person_id: str, category: str, provider: str) -> bool:
        return category == "task" and provider == "local"


async def configured(*, consent=True, fail_audit=False, checker=None, audit_override=None):
    registry = ToolRegistry()
    registry.register(
        {
            "name": "sample.action",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "effect_class": "external_effect",
            "reversible": False,
            "provider": "local",
            "data_categories": ["task"],
        }
    )
    actor, task, approvals, _, audit = setup(tools=registry)
    action = await proposal(actor, task, approvals)
    grant = await approvals.decide(actor, intent(action))
    assert grant is not None
    adapter = Adapter()

    class BrokenAudit:
        async def append(self, principal, draft):
            raise RuntimeError("detalle privado")

    executor = ExternalExecutor(
        registry,
        approvals,
        GrantSigner(b"t" * 32),
        BrokenAudit() if fail_audit else audit_override or audit,
        {"sample.action": adapter},
        checker if checker is not None else Consent() if consent else None,
    )
    return actor, action, grant, adapter, executor, audit


def test_only_the_approved_payload_is_sent_once() -> None:
    async def run() -> None:
        actor, action, grant, adapter, executor, audit = await configured()
        result = await executor.dispatch(actor, grant, hold_seconds=0)
        assert result == {"accepted": True}
        with pytest.raises(PolicyError):
            await executor.dispatch(actor, grant, hold_seconds=0)
        assert adapter.sent == [({"body": "Original"}, str(action.id))]
        assert [event.result for event in audit.events if event.kind == "tool"] == ["pending", "ok"]

    asyncio.run(run())


@pytest.mark.parametrize(
    ("options", "code"),
    [
        ({"consent": False}, "dispatch.consent.denied"),
        ({"fail_audit": True}, "dispatch.audit.unavailable"),
    ],
)
def test_consent_or_audit_failure_prevents_any_effect(options, code: str) -> None:
    async def run() -> None:
        actor, _, grant, adapter, executor, _ = await configured(**options)
        with pytest.raises(DispatchError, match=code):
            await executor.dispatch(actor, grant, hold_seconds=0)
        assert adapter.sent == []

    asyncio.run(run())


def test_stop_during_hold_cancels_and_revokes_approval() -> None:
    async def run() -> None:
        actor, _, grant, adapter, executor, _ = await configured()
        job = asyncio.create_task(executor.dispatch(actor, grant, hold_seconds=30))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        executor.stop(actor)
        with pytest.raises(asyncio.CancelledError):
            await job
        with pytest.raises(PolicyError):
            await executor.dispatch(actor, grant, hold_seconds=0)
        assert adapter.sent == []

    asyncio.run(run())


def test_revocation_while_dispatch_audit_is_in_flight_denies_the_effect() -> None:
    async def run() -> None:
        started, release = asyncio.Event(), asyncio.Event()

        class BlockingAudit:
            async def append(self, principal, draft):
                if draft.result == "pending":
                    started.set()
                    await release.wait()
                return uuid4()

        notice = ConsentNotice("task", "local", 1)
        consent = ConsentService(Store(), [notice])
        actor, _, grant, adapter, executor, _ = await configured(
            checker=consent, audit_override=BlockingAudit()
        )
        await consent.decide(actor, notice, "granted", "voice")
        dispatch = asyncio.create_task(executor.dispatch(actor, grant, hold_seconds=0))
        await asyncio.wait_for(started.wait(), timeout=1)
        await consent.decide(actor, notice, "revoked", "voice")
        release.set()
        with pytest.raises(DispatchError, match="dispatch.consent.denied"):
            await dispatch
        assert adapter.sent == []

    asyncio.run(run())
