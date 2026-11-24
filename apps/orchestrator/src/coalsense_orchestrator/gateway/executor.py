"""Despacho de efectos aprobados por adaptadores registrados en el servidor."""

import asyncio
import math
from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from coalsense_intents.models import JsonValue

from coalsense_orchestrator.audit.events import AuditDraft, AuditRefs, EventResult
from coalsense_orchestrator.auth.sessions import Principal
from coalsense_orchestrator.policy.approvals import ApprovalService
from coalsense_orchestrator.policy.grant import ApprovalGrant, GrantSigner
from coalsense_orchestrator.policy.versions import AuditSink

from .consent_client import ConsentChecker, ConsentError, DenyConsentChecker, require_consent
from .registry import ToolRegistry


class DispatchError(ValueError):
    """Estado de despacho sin datos del proveedor."""


class DispatchAdapter(Protocol):
    async def execute(self, value: JsonValue, *, idempotency_key: str) -> object: ...


class ExternalExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        approvals: ApprovalService,
        verifier: GrantSigner,
        audit: AuditSink,
        adapters: Mapping[str, DispatchAdapter],
        consent: ConsentChecker | None = None,
    ) -> None:
        self._registry, self._approvals, self._verifier = registry, approvals, verifier
        self._audit, self._adapters = audit, dict(adapters)
        self._consent = DenyConsentChecker() if consent is None else consent
        self._jobs: dict[tuple[str, UUID], asyncio.Task[JsonValue]] = {}

    async def dispatch(
        self, actor: Principal, grant: ApprovalGrant, *, hold_seconds: float
    ) -> JsonValue:
        """La retención proviene de preferencias consultadas por un llamador de confianza."""
        if (
            type(hold_seconds) not in (int, float)
            or not math.isfinite(hold_seconds)
            or hold_seconds < 0
        ):
            raise DispatchError("dispatch.hold.invalid")
        if (
            not self._verifier.verify(grant)
            or str(grant.person_id) != actor.account_id
            or str(grant.session_id) != actor.session_id
        ):
            raise DispatchError("dispatch.grant.denied")
        key = (actor.account_id, grant.pending_action_id)
        if key in self._jobs:
            raise DispatchError("dispatch.in_progress")
        job = asyncio.create_task(self._dispatch(actor, grant, hold_seconds))
        self._jobs[key] = job
        try:
            return await job
        finally:
            del self._jobs[key]

    def stop(self, actor: Principal) -> None:
        self._approvals.stop(actor)
        for (owner, _), job in self._jobs.items():
            if owner == actor.account_id:
                job.cancel()

    async def _dispatch(
        self, actor: Principal, grant: ApprovalGrant, hold_seconds: float
    ) -> JsonValue:
        preview = self._approvals.preview(actor, grant.pending_action_id)
        manifest = self._registry.get(preview.tool_name)
        adapter = self._adapters.get(manifest.name)
        if adapter is None or manifest.effect_class != "external_effect":
            raise DispatchError("dispatch.tool.unavailable")
        refs = AuditRefs(
            task_id=preview.task_id,
            pending_action_id=preview.id,
            actor_id=grant.person_id,
            session_id=grant.session_id,
            actor_origin="person",
            tool_name=manifest.name,
            effect_class=manifest.effect_class,
        )
        await asyncio.sleep(hold_seconds)
        await self._record(actor, "pending", refs)

        async def check_consent() -> None:
            # [SUPUESTO] Plazo técnico para dependencias; no limita la revisión humana.
            async with asyncio.timeout(2):
                if not manifest.data_categories:
                    raise ConsentError("consent.context.invalid")
                for category in manifest.data_categories:
                    await require_consent(
                        self._consent, actor.account_id, category, manifest.provider
                    )

        try:
            action = await self._approvals.claim(actor, grant, before_consume=check_consent)
        except (ConsentError, TimeoutError):
            await self._record(actor, "denied", refs)
            raise DispatchError("dispatch.consent.denied") from None
        outcome: JsonValue
        try:
            result = await adapter.execute(action.tool_input(), idempotency_key=str(action.id))
            outcome = manifest.validate_output(result)
        except asyncio.CancelledError:
            # Un proveedor puede haber aceptado la operación antes de la cancelación.
            try:
                await self._record(actor, "failed", refs)
            except DispatchError:
                pass
            raise
        except Exception:
            failed = True
        else:
            failed = False
        if failed:
            await self._record(actor, "failed", refs)
            raise DispatchError("dispatch.outcome_unconfirmed")
        await self._record(actor, "ok", refs)
        return outcome

    async def _record(self, actor: Principal, result: EventResult, refs: AuditRefs) -> None:
        recorded = False
        try:
            async with asyncio.timeout(2):
                recorded = (
                    type(await self._audit.append(actor, AuditDraft("tool", result, refs))) is UUID
                )
        except Exception:
            pass
        if not recorded:
            code = (
                "dispatch.audit.unavailable"
                if result in ("pending", "denied")
                else ("dispatch.outcome_unconfirmed")
            )
            raise DispatchError(code)
