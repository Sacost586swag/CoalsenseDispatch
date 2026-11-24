"""Puertos de versiones y bitácora; las credenciales permanecen en persistencia."""

from typing import Protocol
from uuid import UUID

from coalsense_orchestrator.audit.events import AuditDraft, AuditRecord
from coalsense_orchestrator.auth.sessions import Principal

from .loader import PolicySnapshot


class PolicyLookup(Protocol):
    async def active_policy(self, principal: Principal) -> PolicySnapshot | None: ...


class AuditSink(Protocol):
    async def append(self, principal: Principal, draft: AuditDraft) -> UUID: ...


class AuditStore(Protocol):
    async def append_audit(self, principal: Principal, draft: AuditDraft) -> AuditRecord: ...


class PersistenceAudit:
    def __init__(self, store: AuditStore) -> None:
        self._store = store

    async def append(self, principal: Principal, draft: AuditDraft) -> UUID:
        return (await self._store.append_audit(principal, draft)).id
