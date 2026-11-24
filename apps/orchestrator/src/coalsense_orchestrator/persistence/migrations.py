"""Migraciones administrativas en una transacción, con huellas e historial prefijo.

No se llama desde agentes ni desde el usuario de ejecución. Los nombres completos
identifican migraciones; los prefijos numéricos históricos pueden repetirse.
"""

import hashlib
import re
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import Protocol, cast

import asyncpg  # type: ignore[import-untyped]  # Adaptador limitado por MigrationConnection.

from .config import DatabaseSettings


class MigrationError(ValueError):
    """Código fijo, sin SQL, parámetros ni detalles del controlador."""


class MigrationConnection(Protocol):
    def transaction(self) -> AbstractAsyncContextManager[None]: ...
    def is_in_transaction(self) -> bool: ...
    async def execute(self, query: str, *args: object) -> str: ...
    async def fetchrow(self, query: str, *args: object) -> Mapping[str, object] | None: ...
    async def fetch(self, query: str, *args: object) -> list[Mapping[str, object]]: ...
    async def close(self) -> None: ...


def _load(directory: Path) -> tuple[tuple[str, str, str], ...]:
    result: list[tuple[str, str, str]] = []
    if not directory.is_dir():
        raise MigrationError("migration.source.invalid")
    for path in sorted(directory.glob("*.sql")):
        if path.is_symlink() or not re.fullmatch(r"[0-9]{4}_[a-z0-9_]+\.sql", path.name):
            raise MigrationError("migration.source.invalid")
        # read_text normaliza los finales de línea; Windows y Linux comparten huella.
        sql = path.read_text(encoding="utf-8")
        if not sql.strip():
            raise MigrationError("migration.source.invalid")
        result.append((path.name, hashlib.sha256(sql.encode("utf-8")).hexdigest(), sql))
    if not result:
        raise MigrationError("migration.source.invalid")
    return tuple(result)


async def _execute(
    connection: MigrationConnection, directory: Path, *, write: bool
) -> tuple[str, ...]:
    migrations = _load(directory)
    if connection.is_in_transaction() is not False:
        raise MigrationError("migration.transaction.invalid")
    async with connection.transaction():
        role = await connection.fetchrow("""
            select r.rolsuper, r.rolcreaterole,
                   exists (select 1 from pg_roles g where g.rolname = 'app_rw'
                           and pg_has_role(current_user, g.oid, 'MEMBER')) as runtime_member
            from pg_roles r where r.rolname = current_user
        """)
        if not role or not (
            role["rolsuper"] is True
            or (role["rolcreaterole"] is True and role["runtime_member"] is False)
        ):
            raise MigrationError("migration.role.invalid")
        await connection.execute("""
            select pg_catalog.pg_advisory_xact_lock(
                pg_catalog.hashtextextended('coalsense.migrations.v1', 0)
            )
        """)
        if not write:
            exists = await connection.fetchrow(
                "select to_regclass('coalsense_migrations.applied') as relation"
            )
            if exists and exists["relation"] is None:
                return tuple(name for name, _, _ in migrations)
        else:
            await connection.execute("""
            create schema if not exists coalsense_migrations;
            revoke all on schema coalsense_migrations from public;
            create table if not exists coalsense_migrations.applied (
                name text primary key,
                sha256 text not null check (length(sha256) = 64),
                applied_at timestamptz not null default clock_timestamp()
            );
            revoke all on coalsense_migrations.applied from public;
            """)
        history = await connection.fetch(
            "select name, sha256 from coalsense_migrations.applied order by name"
        )
        expected = [(name, digest) for name, digest, _ in migrations]
        observed = [(row["name"], row["sha256"]) for row in history]
        if observed != expected[: len(observed)]:
            raise MigrationError("migration.history.changed")
        if not write:
            return tuple(name for name, _, _ in migrations[len(observed) :])
        applied: list[str] = []
        for name, digest, sql in migrations[len(observed) :]:
            await connection.execute("set local search_path = public")
            await connection.execute(sql)
            await connection.execute(
                "insert into coalsense_migrations.applied(name, sha256) values($1, $2)",
                name,
                digest,
            )
            applied.append(name)
        return tuple(applied)


async def _guarded(
    connection: MigrationConnection, directory: Path, *, write: bool
) -> tuple[str, ...]:
    code = "migration.failed"
    try:
        return await _execute(connection, directory, write=write)
    except MigrationError as error:
        if str(error) in {
            "migration.role.invalid",
            "migration.source.invalid",
            "migration.history.changed",
            "migration.transaction.invalid",
        }:
            code = str(error)
    except Exception:
        pass
    raise MigrationError(code)


async def apply_migrations(connection: MigrationConnection, directory: Path) -> tuple[str, ...]:
    return await _guarded(connection, directory, write=True)


async def plan_migrations(connection: MigrationConnection, directory: Path) -> tuple[str, ...]:
    """Consulta el historial sin crear esquemas ni tablas; nunca aplica SQL nuevo."""
    return await _guarded(connection, directory, write=False)


async def run_migrations(
    settings: DatabaseSettings, directory: Path, *, apply: bool = False
) -> tuple[str, ...]:
    """Adaptador del comando administrativo. No reutiliza la conexión de la aplicación."""
    connection: MigrationConnection | None = None
    result: tuple[str, ...] | None = None
    code = "migration.failed"
    try:
        settings = DatabaseSettings.from_dsn(
            settings.dsn.get_secret_value(), testing_local=settings.testing_local
        )
        connection = cast(
            MigrationConnection,
            await asyncpg.connect(
                settings.dsn.get_secret_value(),
                ssl=settings.tls(),
                timeout=5,
                command_timeout=60,  # [SUPUESTO] Tiempo técnico; un fallo revierte la transacción.
                server_settings={"application_name": "coalsense-migrations"},
            ),
        )
        result = await _guarded(connection, directory, write=apply)
    except MigrationError as error:
        code = str(error)
    except Exception:
        pass
    finally:
        if connection is not None:
            try:
                await connection.close()
            except Exception:
                result = None
    if result is None:
        raise MigrationError(code)
    return result
