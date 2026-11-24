"""Bitácora real: hash SQL/Python, privilegios, concurrencia y rechazo de alteraciones."""

import asyncio
import json
from uuid import UUID

import asyncpg
import pytest
from coalsense_common import new_id
from coalsense_orchestrator.audit.chain import build_record, verify_chain
from coalsense_orchestrator.audit.events import AuditDraft, AuditError, AuditRefs
from coalsense_orchestrator.audit.log import append_event, read_chain
from coalsense_orchestrator.persistence.service import PersistenceService

from .conftest import DatabaseFixture
from .test_rls import AllowWrites, principal

pytestmark = pytest.mark.integration


def test_task_writes_and_pauses_use_one_chain_per_person(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        person, other = principal(), principal()
        try:
            task = await service.create_task(person, "document")
            await service.pause_task(person, task.id, task.revision)
            await service.create_task(other, "social")
            records = await service.audit_events(person)
            assert [item.draft.kind for item in records] == ["task.created", "task.paused"]
            assert [item.seq for item in records] == [1, 2]
            assert all(item.draft.refs.task_id == task.id for item in records)
            assert verify_chain(UUID(person.account_id), records).seq == 2
            assert len(await service.audit_events(other)) == 1
        finally:
            await service.close()

    asyncio.run(scenario())


def test_concurrent_writes_to_the_same_person_do_not_fork_the_chain(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        person = principal()
        try:
            tasks = await asyncio.gather(*(service.create_task(person, "email") for _ in range(10)))
            records = await service.audit_events(person)
            assert [item.seq for item in records] == list(range(1, 11))
            assert {item.draft.refs.task_id for item in records} == {task.id for task in tasks}
            assert verify_chain(UUID(person.account_id), records).seq == 10
        finally:
            await service.close()

    asyncio.run(scenario())


def test_all_reference_fields_roundtrip_with_the_same_sql_and_python_hash(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        person = principal()
        task = await service.create_task(person, "email")
        await service.close()
        owner = UUID(person.account_id)
        refs = AuditRefs(
            task_id=task.id,
            plan_id=UUID(new_id()),
            step_id=UUID(new_id()),
            pending_action_id=UUID(new_id()),
            actor_id=owner,
            device_id=UUID(person.device_id),
            session_id=UUID(person.session_id),
            tool_name="email.send",
            effect_class="external_effect",
            actor_origin="person",
            policy_version=47,
            action_id=UUID(new_id()),
            rule_id="default.external_effect",
        )
        connection = await database.connection()
        try:
            async with connection.transaction():
                await connection.execute(
                    "select set_config('coalsense.person_id', $1, true)", str(owner)
                )
                record = await append_event(connection, owner, AuditDraft("tool", "pending", refs))
                verified = await read_chain(connection, owner)
                assert verified.records[-1] == record and record.draft.refs == refs
        finally:
            await connection.close()

    asyncio.run(scenario())


def test_no_transaction_or_another_person_scope_is_rejected(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        connection = await database.connection()
        person = UUID(new_id())
        try:
            with pytest.raises(AuditError, match="^audit.transaction.required$"):
                await append_event(connection, person, AuditDraft("control.stop", "ok"))
            async with connection.transaction():
                await connection.execute(
                    "select set_config('coalsense.person_id', $1, true)", str(person)
                )
                with pytest.raises(AuditError, match="^audit.scope.invalid$"):
                    await read_chain(connection, UUID(new_id()))
        finally:
            await connection.close()

    asyncio.run(scenario())


def test_server_append_is_committed_before_it_returns(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        writer = await PersistenceService.connect(database.settings())
        person = principal()
        try:
            event = await writer.append_audit(person, AuditDraft("control.stop", "ok"))
            reader = await PersistenceService.connect(database.settings())
            try:
                assert await reader.audit_events(person) == (event,)
                assert await reader.audit_events(principal()) == ()
            finally:
                await reader.close()
        finally:
            await writer.close()

    asyncio.run(scenario())


def test_database_hash_and_shape_constraints_reject_forged_direct_inserts(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        connection = await database.connection()
        person = UUID(new_id())
        try:
            for refs in ({"body": "Contenido privado"}, {"actor_origin": "operator"}):
                with pytest.raises(asyncpg.CheckViolationError):
                    async with connection.transaction():
                        await connection.execute(
                            "select set_config('coalsense.person_id', $1, true)", str(person)
                        )
                        await connection.execute(
                            """
                            insert into coalsense.audit_event
                                (id, person_id, seq, at, kind, result, refs, prev_hash, hash)
                            select $1, $2, 1, now(), 'tool', 'ok', $3::jsonb, repeat('0',64),
                                coalsense.audit_hash($1, $2, 1, now(), 'tool', 'ok',
                                                     $3::jsonb, repeat('0',64))
                        """,
                            UUID(new_id()),
                            person,
                            json.dumps(refs),
                        )
            record = build_record(person, 1, AuditDraft("control.stop", "ok"), "0" * 64)
            with pytest.raises(asyncpg.CheckViolationError):
                async with connection.transaction():
                    await connection.execute(
                        "select set_config('coalsense.person_id', $1, true)", str(person)
                    )
                    await connection.execute(
                        """
                        insert into coalsense.audit_event
                            (id, person_id, seq, at, kind, result, refs, prev_hash, hash)
                        values ($1, $2, 1, $3, 'control.stop', 'ok', '{}', $4, $5)
                    """,
                        record.id,
                        person,
                        record.at,
                        record.prev_hash,
                        "f" * 64,
                    )
            skipped = build_record(person, 2, record.draft, record.prev_hash)
            with pytest.raises(asyncpg.RaiseError):
                async with connection.transaction():
                    await connection.execute(
                        "select set_config('coalsense.person_id', $1, true)", str(person)
                    )
                    await connection.execute(
                        """
                        insert into coalsense.audit_event
                            (id, person_id, seq, at, kind, result, refs, prev_hash, hash)
                        values ($1, $2, 2, $3, 'control.stop', 'ok', '{}', $4, $5)
                    """,
                        skipped.id,
                        person,
                        skipped.at,
                        skipped.prev_hash,
                        skipped.hash,
                    )
        finally:
            await connection.close()

    asyncio.run(scenario())


def test_privileged_tampering_is_detected_before_any_new_append(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        person = principal()
        owner = UUID(person.account_id)
        await service.create_task(person, "email")
        await service.close()
        admin = await database.connection(admin=True)
        transaction = admin.transaction()
        await transaction.start()
        try:
            # Simula corrupción privilegiada que evita los permisos normales y el CHECK.
            await admin.execute(
                "alter table coalsense.audit_event drop constraint audit_hash_matches"
            )
            await admin.execute("select set_config('coalsense.person_id', $1, true)", str(owner))
            await admin.execute(
                "update coalsense.audit_event set result='failed' where person_id=$1", owner
            )
            for operation in (
                read_chain(admin, owner),
                append_event(admin, owner, AuditDraft("control.stop", "ok")),
            ):
                with pytest.raises(AuditError, match="^audit.integrity.invalid$"):
                    await operation
            assert (
                await admin.fetchval(
                    "select count(*) from coalsense.audit_event where person_id=$1", owner
                )
                == 1
            )
        finally:
            # Restaura tanto los datos como el CHECK mediante rollback de la prueba.
            await transaction.rollback()
            await admin.close()

    asyncio.run(scenario())
