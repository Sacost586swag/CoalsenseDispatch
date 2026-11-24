"""T-02-002: aislamiento real PostgreSQL, transacciones y rol de ejecución mínimo."""

import asyncio
import os
import subprocess
import sys
from contextlib import suppress
from dataclasses import replace
from uuid import UUID

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.auth.scopes import CONTENT_READ, CONTENT_WRITE
from coalsense_orchestrator.auth.sessions import Principal
from coalsense_orchestrator.persistence.roles import agent_environment
from coalsense_orchestrator.persistence.service import PersistenceError, PersistenceService

from .conftest import DatabaseFixture


def principal() -> Principal:
    return Principal(
        new_id(), new_id(), new_id(), "person", frozenset({CONTENT_READ, CONTENT_WRITE})
    )


class AllowWrites:
    async def permits(self, person_id: UUID, operation: str, resource_id: UUID) -> bool:
        return True


@pytest.mark.integration
def test_rows_of_another_person_are_invisible_even_without_an_owner_filter(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        try:
            first, second = principal(), principal()
            a = await service.create_task(first, "document")
            b = await service.create_task(second, "email")
            assert await service.list_tasks(first) == (a,)
            assert await service.list_tasks(second) == (b,)
            assert await service.get_task(first, b.id) is None
            assert await service.get_task(second, a.id) is None
            with pytest.raises(PersistenceError, match="^persistence.task.changed$"):
                await service.pause_task(first, b.id, b.revision)
        finally:
            await service.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_restart_preserves_metadata_and_optimistic_revision_prevents_lost_update(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        person = principal()
        first = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        task = await first.create_task(person, "social")
        await first.close()
        restarted = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        try:
            assert await restarted.get_task(person, task.id) == task
            paused = await restarted.pause_task(person, task.id, task.revision)
            assert (paused.state, paused.revision, paused.autonomy_level) == ("paused", 2, "N0")
            with pytest.raises(PersistenceError, match="^persistence.task.changed$"):
                await restarted.pause_task(person, task.id, task.revision)
            assert await restarted.get_task(person, task.id) == paused
        finally:
            await restarted.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_denied_or_failing_policy_does_not_write(database: DatabaseFixture) -> None:
    class BrokenPolicy:
        async def permits(self, person_id: UUID, operation: str, resource_id: UUID) -> bool:
            raise RuntimeError("Un secreto que no debe salir")

    async def scenario() -> None:
        for policy in [None, BrokenPolicy()]:
            service = await PersistenceService.connect(database.settings(), policy=policy)
            person = principal()
            try:
                with pytest.raises(PersistenceError, match="^persistence.policy.denied$") as caught:
                    await service.create_task(person, "document")
                assert caught.value.__context__ is None
                assert await service.list_tasks(person) == ()
            finally:
                await service.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_operator_and_undelegated_caregiver_are_denied_before_database_access(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        try:
            person = principal()
            task = await service.create_task(person, "document")
            for role in ("operator", "caregiver", "company", "unknown"):
                actor = replace(person, role=role)
                with pytest.raises(PersistenceError, match="^persistence.access.denied$"):
                    await service.get_task(actor, task.id)
                with pytest.raises(PersistenceError):
                    await service.create_task(actor, "email")
        finally:
            await service.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_audit_insert_failure_rolls_back_the_task_and_hides_database_details(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        person = principal()
        await database.admin_execute("revoke insert on coalsense.audit_event from app_rw")
        try:
            with pytest.raises(PersistenceError, match="^persistence.unavailable$") as caught:
                await service.create_task(person, "document")
            assert caught.value.__context__ is None
            assert await service.list_tasks(person) == ()
        finally:
            await database.admin_execute("grant insert on coalsense.audit_event to app_rw")
            await service.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_privileged_database_connection_is_rejected(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        with pytest.raises(PersistenceError, match="^persistence.role.invalid$"):
            await PersistenceService.connect(database.settings(admin=True), policy=AllowWrites())

    asyncio.run(scenario())


@pytest.mark.integration
def test_rls_cannot_read_or_write_another_owner_and_scope_is_transaction_local(
    database: DatabaseFixture,
) -> None:
    asyncio.run(database.assert_direct_rls())


@pytest.mark.integration
def test_unsafe_role_group_is_rejected_even_when_the_login_itself_is_unprivileged(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        await database.admin_execute("alter role app_rw bypassrls")
        try:
            with pytest.raises(PersistenceError, match="^persistence.role.invalid$"):
                await PersistenceService.connect(database.settings(), policy=AllowWrites())
        finally:
            await database.admin_execute("alter role app_rw nobypassrls")

    asyncio.run(scenario())


@pytest.mark.integration
def test_cancellation_rolls_back_the_write_and_the_pool_remains_usable(
    database: DatabaseFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        person = principal()
        entered = asyncio.Event()

        async def pending_record(*args: object) -> None:
            entered.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(service, "_record", pending_record)
        task = asyncio.create_task(service.create_task(person, "document"))
        try:
            await asyncio.wait_for(entered.wait(), timeout=5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert await service.list_tasks(person) == ()
        finally:
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            await service.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_concurrent_requests_never_share_a_person_scope(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        people = [principal() for _ in range(6)]
        try:
            tasks = await asyncio.gather(
                *(service.create_task(person, "document") for person in people)
            )
            lists = await asyncio.gather(*(service.list_tasks(person) for person in people))
            assert lists == [(task,) for task in tasks]
        finally:
            await service.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_an_agent_child_without_inherited_credentials_cannot_authenticate(
    database: DatabaseFixture,
) -> None:
    environment = agent_environment(dict(os.environ, PGPASSWORD=database.app_password))
    script = """
import asyncio, sys
import asyncpg
async def main():
    try:
        connection = await asyncpg.connect(host='127.0.0.1', port=int(sys.argv[1]),
            user='coalsense_test_app', database='coalsense_test', ssl=False, timeout=5)
    except asyncpg.InvalidPasswordError:
        return
    await connection.close()
    raise RuntimeError('Unexpected database access')
asyncio.run(main())
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(database.port)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
