"""PostgreSQL aislado y efímero, activado explícitamente; sin secretos en el repositorio."""

import asyncio
import os
import re
import secrets
import subprocess
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID, uuid4

import asyncpg
import pytest
from coalsense_common import new_id
from coalsense_orchestrator.audit.events import AuditDraft, AuditRefs
from coalsense_orchestrator.audit.log import append_event
from coalsense_orchestrator.persistence.config import DatabaseSettings
from coalsense_orchestrator.persistence.migrations import apply_migrations
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[4]


@dataclass(repr=False)
class DatabaseFixture:
    port: int
    password: str = field(repr=False)
    app_password: str = field(repr=False)
    database_name: str = "coalsense_test"

    def settings(self, *, admin: bool = False) -> DatabaseSettings:
        user = "postgres" if admin else "coalsense_test_app"
        password = self.password if admin else self.app_password
        return DatabaseSettings.from_connection(
            username=user,
            password=SecretStr(password),
            host="127.0.0.1",
            port=self.port,
            database=self.database_name,
            testing_local=True,
        )

    async def connection(self, *, admin: bool = False):
        return await asyncpg.connect(self.settings(admin=admin).dsn.get_secret_value(), ssl=False)

    async def admin_execute(self, sql: str) -> None:
        connection = await self.connection(admin=True)
        try:
            await connection.execute(sql)
        finally:
            await connection.close()

    async def bootstrap(self) -> None:
        deadline = time.monotonic() + 40  # [SUPUESTO] Arranque técnico del contenedor de prueba.
        connection = None
        while time.monotonic() < deadline:
            try:
                connection = await self.connection(admin=True)
                break
            except (OSError, asyncpg.PostgresError):
                await asyncio.sleep(0.25)
        if connection is None:
            raise RuntimeError("No inició la base de prueba")
        try:
            await apply_migrations(connection, ROOT / "apps/orchestrator/migrations")
            async with connection.transaction():
                # Valor generado por token_hex, no un dato de entrada ni un secreto versionado.
                await connection.execute(
                    "create role coalsense_test_app login password '"
                    + self.app_password
                    + "' in role app_rw"
                )
        finally:
            await connection.close()

    @asynccontextmanager
    async def isolated_database(self) -> AsyncIterator["DatabaseFixture"]:
        name = "coalsense_test_" + uuid4().hex
        assert re.fullmatch(r"coalsense_test_[a-f0-9]{32}", name)
        # Identificador generado aquí; nunca proviene de una entrada de la aplicación.
        await self.admin_execute("create database " + name)
        try:
            yield DatabaseFixture(self.port, self.password, self.app_password, name)
        finally:
            await self.admin_execute("drop database " + name + " with (force)")

    async def assert_direct_rls(self) -> None:
        first, second = UUID(new_id()), UUID(new_id())
        foreign_task = UUID(new_id())
        connection = await self.connection()
        try:
            async with connection.transaction():
                await connection.execute(
                    "select set_config('coalsense.person_id', $1, true)", str(second)
                )
                await connection.execute(
                    "insert into coalsense.task(id, person_id, kind) values($1, $2, 'document')",
                    foreign_task,
                    second,
                )
            assert (
                await connection.fetchval(
                    "select nullif(current_setting('coalsense.person_id', true), '')"
                )
                is None
            )
            assert await connection.fetch("select * from coalsense.task") == []
            async with connection.transaction():
                await connection.execute(
                    "select set_config('coalsense.person_id', $1, true)", str(first)
                )
                assert await connection.fetch("select * from coalsense.task") == []
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                async with connection.transaction():
                    await connection.execute(
                        "select set_config('coalsense.person_id', $1, true)", str(first)
                    )
                    await connection.execute(
                        "insert into coalsense.task(id, person_id, kind) "
                        "values($1, $2, 'document')",
                        UUID(new_id()),
                        second,
                    )
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                async with connection.transaction():
                    await connection.execute(
                        "select set_config('coalsense.person_id', $1, true)", str(first)
                    )
                    await append_event(
                        connection,
                        first,
                        AuditDraft("task.created", "ok", AuditRefs(task_id=foreign_task)),
                    )
            for sql in (
                "delete from coalsense.persistence_event",
                "truncate coalsense.persistence_event",
                "update coalsense.persistence_event set operation = 'task.pause'",
                "delete from coalsense.audit_event",
                "truncate coalsense.audit_event",
                "update coalsense.audit_event set result = 'denied'",
            ):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.execute(sql)
            # Tampoco puede cambiar el dueño de una tarea ni convertirse en admin.
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await connection.execute("update coalsense.task set person_id = $1", first)
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await connection.execute("set role admin")
        finally:
            await connection.close()
        admin = await self.connection(admin=True)
        try:
            await admin.execute("set role admin")
            # FORCE RLS también cubre al propietario, sin un contexto de persona.
            assert await admin.fetch("select * from coalsense.task") == []
            assert await admin.fetch("select * from coalsense.audit_event") == []
            await admin.execute("reset role")
            await admin.execute("set role app_ro_audit")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await admin.fetch("select * from coalsense.task")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await admin.fetch("select * from coalsense.persistence_event")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await admin.fetch("select * from coalsense.audit_event")
        finally:
            await admin.close()


@pytest.fixture(scope="session")
def database() -> Iterator[DatabaseFixture]:
    if os.environ.get("COALSENSE_TEST_POSTGRES") != "1":
        pytest.skip("PostgreSQL real: activar COALSENSE_TEST_POSTGRES=1 y disponer de Docker")
    project = "coalsense-rls-test-" + uuid4().hex
    secret = secrets.token_hex(32)
    environment = dict(os.environ, COALSENSE_POSTGRES_TEST_PASSWORD=secret)
    command = ["docker", "compose", "-f", str(ROOT / "infra/compose.test.yaml"), "-p", project]

    def run(*args: str) -> str:
        result = subprocess.run(
            [*command, *args],
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode:
            raise RuntimeError("Falló Docker en la instancia aislada de prueba")
        return result.stdout.strip()

    try:
        run("up", "--detach")
        address = run("port", "postgres", "5432")
        instance = DatabaseFixture(int(address.rsplit(":", 1)[1]), secret, secrets.token_hex(32))
        asyncio.run(instance.bootstrap())
        yield instance
    finally:
        # Solo se eliminan los recursos del proyecto aleatorio creado por esta fixture.
        assert re.fullmatch(r"coalsense-rls-test-[a-f0-9]{32}", project)
        run("down", "--volumes", "--remove-orphans")
