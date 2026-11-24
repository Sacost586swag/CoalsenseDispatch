"""Conversión de eventos existentes y carrera entre dos migradores reales."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.audit.log import read_chain
from coalsense_orchestrator.persistence.migrations import apply_migrations

from .conftest import DatabaseFixture

pytestmark = pytest.mark.integration
MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"


def test_legacy_events_keep_ids_timestamps_and_owner_in_the_new_chain(
    database: DatabaseFixture,
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if path.name < "0003_audit.sql":
                (tmp_path / path.name).write_bytes(path.read_bytes())
        async with database.isolated_database() as isolated:
            admin = await isolated.connection(admin=True)
            person, task_id, event_id = UUID(new_id()), UUID(new_id()), UUID(new_id())
            at = datetime(2026, 11, 18, 12, 34, 56, 123456, tzinfo=UTC)
            try:
                await apply_migrations(admin, tmp_path)
                connection = await isolated.connection()
                try:
                    async with connection.transaction():
                        await connection.execute(
                            "select set_config('coalsense.person_id', $1, true)", str(person)
                        )
                        await connection.execute(
                            "insert into coalsense.task(id,person_id,kind) "
                            "values($1,$2,'document')",
                            task_id,
                            person,
                        )
                        await connection.execute(
                            """
                            insert into coalsense.persistence_event
                                (id, person_id, operation, resource_id, at)
                            values ($1,$2,'task.create',$3,$4)
                        """,
                            event_id,
                            person,
                            task_id,
                            at,
                        )
                finally:
                    await connection.close()
                assert await apply_migrations(admin, MIGRATIONS) == tuple(
                    path.name
                    for path in sorted(MIGRATIONS.glob("*.sql"))
                    if path.name >= "0003_audit.sql"
                )
                connection = await isolated.connection()
                try:
                    async with connection.transaction():
                        await connection.execute(
                            "select set_config('coalsense.person_id', $1, true)", str(person)
                        )
                        chain = await read_chain(connection, person)
                        assert len(chain.records) == 1
                        event = chain.records[0]
                        assert (event.id, event.person_id, event.at) == (event_id, person, at)
                        assert (
                            event.draft.kind == "task.created"
                            and event.draft.refs.task_id == task_id
                        )
                        assert (
                            await connection.fetchval(
                                "select count(*) from coalsense.persistence_event"
                            )
                            == 1
                        )
                    assert (
                        await connection.fetchval(
                            "select bool_and(relrowsecurity and relforcerowsecurity) from pg_class "
                            "where oid in ('coalsense.persistence_event'::regclass, "
                            "'coalsense.audit_event'::regclass)"
                        )
                        is True
                    )
                finally:
                    await connection.close()
            finally:
                await admin.close()

    asyncio.run(scenario())


def test_simultaneous_migrators_apply_a_new_file_once(
    database: DatabaseFixture, tmp_path: Path
) -> None:
    async def scenario() -> None:
        for path in MIGRATIONS.glob("*.sql"):
            (tmp_path / path.name).write_bytes(path.read_bytes())
        (tmp_path / "9999_probe.sql").write_text(
            "create table coalsense.concurrent_migration_probe(id integer);", encoding="utf-8"
        )
        async with database.isolated_database() as isolated:
            first, second = (
                await isolated.connection(admin=True),
                await isolated.connection(admin=True),
            )
            try:
                await apply_migrations(first, MIGRATIONS)
                results = await asyncio.gather(
                    apply_migrations(first, tmp_path),
                    apply_migrations(second, tmp_path),
                )
                assert sorted(results) == [(), ("9999_probe.sql",)]
                assert (
                    await first.fetchval(
                        "select count(*) from coalsense_migrations.applied "
                        "where name='9999_probe.sql'"
                    )
                    == 1
                )
            finally:
                await first.close()
                await second.close()

    asyncio.run(scenario())
