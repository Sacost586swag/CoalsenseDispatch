"""Pruebas de persistencia de sobres opacos y aislamiento en PostgreSQL."""

import asyncio
from uuid import UUID, uuid4

import asyncpg
import pytest
from coalsense_orchestrator.consent.encrypted_store import EncryptedConsentStore
from coalsense_orchestrator.consent.models import ConsentNotice
from coalsense_orchestrator.consent.service import ConsentService
from coalsense_orchestrator.persistence.service import PersistenceService

from ..policy.test_engine import principal
from .conftest import DatabaseFixture


class OpaqueCipherFixture:
    """Doble en memoria que exige el contexto. No implementa criptografía."""

    def __init__(self) -> None:
        self.values: dict[tuple[UUID, bytes, bytes], bytes] = {}

    async def seal(self, person: UUID, plaintext: bytes, *, associated_data: bytes) -> bytes:
        token = uuid4().bytes
        self.values[person, token, associated_data] = plaintext
        return token

    async def open(self, person: UUID, envelope: bytes, *, associated_data: bytes) -> bytes:
        return self.values[person, envelope, associated_data]


@pytest.mark.integration
def test_consent_envelopes_are_ordered_private_and_append_only(database: DatabaseFixture) -> None:
    async def run() -> None:
        person, other = principal(), principal()
        owner = UUID(person.account_id)
        notice = ConsentNotice("llm_content", "sample_model", 1)
        cipher = OpaqueCipherFixture()
        persistence = await PersistenceService.connect(database.settings())
        try:
            service = ConsentService(EncryptedConsentStore(persistence, cipher), [notice])
            granted = await service.decide(person, notice, "granted", "voice")
            assert await service.check(person.account_id, notice.category, notice.provider)
            revoked = await service.decide(person, notice, "revoked", "gaze")
            assert await service.history(person) == (granted, revoked)
            assert not await service.check(person.account_id, notice.category, notice.provider)
            assert await service.history(other) == ()
            rows = await persistence.consent_envelopes(owner)
            assert [row[0] for row in rows] == [granted.id, revoked.id]
            assert all(len(blob) == 16 for _, blob in rows)
            column_names = {"person_id", "id", "ordinal", "envelope"}
            connection = await database.connection()
            try:
                async with connection.transaction():
                    await connection.execute(
                        "select set_config('coalsense.person_id', $1, true)", person.account_id
                    )
                    raw = await connection.fetch("select * from coalsense.consent_record")
                    assert len(raw) == 2 and set(raw[0].keys()) == column_names
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.execute("delete from coalsense.consent_record")
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.execute(
                        """
                        insert into coalsense.consent_record(person_id, id, ordinal, envelope)
                        overriding system value values($1, $2, 1, $3)
                        """,
                        owner,
                        uuid4(),
                        rows[0][1],
                    )
            finally:
                await connection.close()
        finally:
            await persistence.close()

    asyncio.run(run())
