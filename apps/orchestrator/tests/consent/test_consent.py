"""REQ-05-031 y REQ-05-034 a 039: vigencia y atribución del consentimiento."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.consent.models import ConsentNotice, ConsentRecord, ConsentRecordError
from coalsense_orchestrator.consent.service import ConsentService
from coalsense_orchestrator.gateway.consent_client import ConsentError, require_consent

from ..policy.test_engine import principal


class Store:
    def __init__(self) -> None:
        self.rows: dict[UUID, list[ConsentRecord]] = {}
        self.unavailable = False

    async def append(self, person: UUID, record: ConsentRecord) -> None:
        self.rows.setdefault(person, []).append(record)

    async def history(self, person: UUID) -> tuple[ConsentRecord, ...]:
        if self.unavailable:
            raise RuntimeError("contenido privado")
        return tuple(self.rows.get(person, ()))


def test_isolated_scope_default_denial_grant_revocation_and_failure() -> None:
    async def run() -> None:
        owner, other = principal(), principal()
        notice = ConsentNotice("llm_content", "sample_model", 1)
        store = Store()
        service = ConsentService(store, [notice])
        scope = (notice.category, notice.provider)
        with pytest.raises(ConsentError, match="consent.denied"):
            await require_consent(service, owner.account_id, *scope)
        await service.decide(owner, notice, "granted", "voice")
        await require_consent(service, owner.account_id, *scope)
        assert not await service.check(other.account_id, *scope)
        assert not await service.check(owner.account_id, notice.category, "other_model")
        assert not await service.check(owner.account_id, "other_category", notice.provider)
        await service.decide(owner, notice, "revoked", "switch_scan")
        with pytest.raises(ConsentError, match="consent.denied"):
            await require_consent(service, owner.account_id, *scope)
        assert not await service.needs_decision(owner, *scope)
        assert [record.modality for record in await service.history(owner)] == [
            "voice",
            "switch_scan",
        ]
        store.unavailable = True
        with pytest.raises(ConsentError, match="consent.unavailable") as error:
            await require_consent(service, owner.account_id, *scope)
        assert error.value.__context__ is None

    asyncio.run(run())


def test_denial_is_not_prompted_again_and_new_text_requires_a_fresh_decision() -> None:
    async def run() -> None:
        owner = principal()
        notice = ConsentNotice("llm_content", "sample_model", 1)
        modified = replace(notice, text_version=2)
        scope = (notice.category, notice.provider)
        store = Store()
        before = ConsentService(store, [notice])
        assert await before.needs_decision(owner, *scope)
        await before.decide(owner, notice, "denied", "keyboard_mouse")
        assert not await before.needs_decision(owner, *scope)
        await before.decide(owner, notice, "granted", "keyboard_mouse")
        after = ConsentService(store, [modified])
        assert not await after.check(owner.account_id, *scope)
        assert await after.needs_decision(owner, *scope)
        with pytest.raises(ConsentRecordError, match="consent.notice.changed"):
            await after.decide(owner, notice, "granted", "keyboard_mouse")
        await after.decide(owner, modified, "granted", "keyboard_mouse")
        assert await after.check(owner.account_id, *scope)

    asyncio.run(run())


def test_old_decision_has_no_time_expiry_and_caregiver_cannot_change_it() -> None:
    async def run() -> None:
        owner = principal()
        notice = ConsentNotice("llm_content", "sample_model", 1)
        store = Store()
        await store.append(
            UUID(owner.account_id),
            ConsentRecord(
                UUID(new_id()), notice, "granted", "gaze", datetime(2000, 1, 1, tzinfo=UTC)
            ),
        )
        service = ConsentService(store, [notice])
        caregiver = replace(owner, role="caregiver")
        with pytest.raises(ConsentRecordError, match="consent.actor.denied"):
            await service.decide(caregiver, notice, "revoked", "voice")
        with pytest.raises(ConsentRecordError, match="consent.actor.denied"):
            await service.history(caregiver)
        assert await service.check(owner.account_id, notice.category, notice.provider)

    asyncio.run(run())
