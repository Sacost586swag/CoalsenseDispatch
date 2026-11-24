"""Decisión explícita y consulta vigente sin caché ni caducidad."""

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from coalsense_common import new_id
from coalsense_intents.models import Modality

from coalsense_orchestrator.auth.scopes import CONTENT_READ, CONTENT_WRITE
from coalsense_orchestrator.auth.sessions import Principal

from .models import ConsentNotice, ConsentRecord, ConsentRecordError, Decision


class ConsentStore(Protocol):
    async def append(self, person: UUID, record: ConsentRecord) -> None: ...
    async def history(self, person: UUID) -> tuple[ConsentRecord, ...]:
        """Devuelve decisiones de esa persona en orden de registro."""
        ...


def _person(actor: Principal, scope: str) -> UUID:
    if type(actor) is Principal and actor.role == "person" and scope in actor.scopes:
        try:
            return UUID(actor.account_id)
        except (ValueError, TypeError, AttributeError):
            pass
    raise ConsentRecordError("consent.actor.denied")


class ConsentService:
    def __init__(self, store: ConsentStore, notices: Iterable[ConsentNotice]) -> None:
        self._store = store
        self._notices: dict[tuple[str, str], ConsentNotice] = {}
        for notice in notices:
            if type(notice) is not ConsentNotice:
                raise ConsentRecordError("consent.notice.invalid")
            key = (notice.category, notice.provider)
            if key in self._notices:
                raise ConsentRecordError("consent.notice.duplicate")
            self._notices[key] = notice

    async def decide(
        self, actor: Principal, notice: ConsentNotice, decision: Decision, modality: Modality
    ) -> ConsentRecord:
        person = _person(actor, CONTENT_WRITE)
        if (
            type(notice) is not ConsentNotice
            or self._notices.get((notice.category, notice.provider)) != notice
        ):
            raise ConsentRecordError("consent.notice.changed")
        record = ConsentRecord(UUID(new_id()), notice, decision, modality, datetime.now(UTC))
        try:
            await self._store.append(person, record)
        except Exception:
            pass
        else:
            return record
        raise ConsentRecordError("consent.unavailable")

    async def history(self, actor: Principal) -> tuple[ConsentRecord, ...]:
        return await self._history(_person(actor, CONTENT_READ))

    async def _history(self, person: UUID) -> tuple[ConsentRecord, ...]:
        try:
            records = await self._store.history(person)
            if type(records) is tuple and all(type(record) is ConsentRecord for record in records):
                return records
        except Exception:
            pass
        raise ConsentRecordError("consent.unavailable")

    async def check(self, person_id: str, category: str, provider: str) -> bool:
        """Implementa ConsentChecker para los llamadores internos de confianza."""
        state = await self._latest(person_id, category, provider)
        return state is not None and state.decision == "granted"

    async def needs_decision(self, actor: Principal, category: str, provider: str) -> bool:
        person = _person(actor, CONTENT_READ)
        if (category, provider) not in self._notices:
            return False
        return await self._latest(str(person), category, provider) is None

    async def _latest(self, person_id: str, category: str, provider: str) -> ConsentRecord | None:
        notice = self._notices.get((category, provider))
        if notice is None:
            return None
        try:
            person = UUID(person_id)
        except (ValueError, TypeError, AttributeError):
            raise ConsentRecordError("consent.actor.denied") from None
        for record in reversed(await self._history(person)):
            if (record.notice.category, record.notice.provider) == (category, provider):
                return record if record.notice == notice else None
        return None
