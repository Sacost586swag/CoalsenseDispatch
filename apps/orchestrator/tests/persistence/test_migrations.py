"""Migraciones en PostgreSQL real: idempotencia, deriva, fallo atómico y permisos."""

import asyncio
from pathlib import Path

import pytest
from coalsense_orchestrator.persistence.migrations import MigrationError, apply_migrations

from .conftest import DatabaseFixture


@pytest.mark.integration
def test_migrations_are_recorded_once_and_not_reexecuted(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        connection = await database.connection(admin=True)
        try:
            root = Path(__file__).resolve().parents[2] / "migrations"
            assert await apply_migrations(connection, root) == ()
            applied = await connection.fetch(
                "select name from coalsense_migrations.applied order by name"
            )
            assert [row["name"] for row in applied] == sorted(
                path.name for path in root.glob("*.sql")
            )
        finally:
            await connection.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_modified_or_missing_applied_migration_is_rejected(
    database: DatabaseFixture,
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        original = Path(__file__).resolve().parents[2] / "migrations"
        for path in original.glob("*.sql"):
            (tmp_path / path.name).write_bytes(path.read_bytes())
        connection = await database.connection(admin=True)
        try:
            changed = sorted(tmp_path.glob("*.sql"))[0]
            changed.write_text(changed.read_text("utf-8") + "\n-- changed\n", encoding="utf-8")
            with pytest.raises(MigrationError, match="^migration.history.changed$") as caught:
                await apply_migrations(connection, tmp_path)
            assert caught.value.__context__ is None
            changed.unlink()
            with pytest.raises(MigrationError, match="^migration.history.changed$"):
                await apply_migrations(connection, tmp_path)
        finally:
            await connection.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_failed_migration_rolls_back_ddl_and_history(
    database: DatabaseFixture, tmp_path: Path
) -> None:
    async def scenario() -> None:
        original = Path(__file__).resolve().parents[2] / "migrations"
        for path in original.glob("*.sql"):
            (tmp_path / path.name).write_bytes(path.read_bytes())
        (tmp_path / "9999_failure.sql").write_text(
            "create table coalsense.migration_probe(id integer); select 1/0;", encoding="utf-8"
        )
        connection = await database.connection(admin=True)
        try:
            with pytest.raises(MigrationError, match="^migration.failed$") as caught:
                await apply_migrations(connection, tmp_path)
            assert caught.value.__context__ is None
            assert (
                await connection.fetchval("select to_regclass('coalsense.migration_probe')") is None
            )
            assert (
                await connection.fetchval(
                    "select count(*) from coalsense_migrations.applied "
                    "where name='9999_failure.sql'"
                )
                == 0
            )
        finally:
            await connection.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_application_user_cannot_run_administrative_migrations(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        connection = await database.connection()
        try:
            root = Path(__file__).resolve().parents[2] / "migrations"
            with pytest.raises(MigrationError, match="^migration.role.invalid$"):
                await apply_migrations(connection, root)
        finally:
            await connection.close()

    asyncio.run(scenario())
