"""El comando consulta por defecto y no sustituye credenciales de aplicación por admin."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from coalsense_orchestrator.persistence.migrations import plan_migrations

from .conftest import DatabaseFixture

TOOL = Path(__file__).resolve().parents[2] / "tools/migrate.py"
MIGRATIONS = TOOL.parents[1] / "migrations"


def test_missing_admin_configuration_exits_without_network_or_credential_output() -> None:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() != "COALSENSE_MIGRATION_DATABASE_URL"
    }
    result = subprocess.run(
        [sys.executable, str(TOOL)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 2 and not result.stderr
    assert json.loads(result.stdout) == {"code": "migration.configuration.missing"}


@pytest.mark.integration
def test_plan_on_a_fresh_database_has_no_ddl_effect(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        async with database.isolated_database() as isolated:
            connection = await isolated.connection(admin=True)
            try:
                pending = await plan_migrations(connection, MIGRATIONS)
                assert pending == tuple(path.name for path in sorted(MIGRATIONS.glob("*.sql")))
                assert (
                    await connection.fetchval("select to_regnamespace('coalsense_migrations')")
                    is None
                )
                assert await connection.fetchval("select to_regnamespace('coalsense')") is None
            finally:
                await connection.close()

    asyncio.run(scenario())


@pytest.mark.integration
def test_command_uses_its_own_configuration_and_reports_json_only(
    database: DatabaseFixture,
) -> None:
    environment = dict(
        os.environ,
        COALSENSE_MIGRATION_DATABASE_URL=database.settings(admin=True).dsn.get_secret_value(),
    )
    for arguments, key in [(["--local-test"], "pending"), (["--local-test", "--apply"], "applied")]:
        result = subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert result.returncode == 0 and not result.stderr
        assert json.loads(result.stdout) == {key: []}
        assert database.password not in result.stdout
