"""Tareas sin contenido: SQL fijo, RLS transaccional, política y registro atómico.

El título y el borrador no se guardan aquí. Requieren el cifrado de T-07-003 y las
versiones de T-04-003. Ninguna consulta ni conexión se entrega a los agentes.
"""

import json
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Literal, Protocol, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]  # Puerto tipado abajo; el paquete no trae py.typed.
from coalsense_common import new_id

from coalsense_orchestrator.audit.events import AuditDraft, AuditRecord, AuditRefs
from coalsense_orchestrator.audit.log import append_event, read_chain
from coalsense_orchestrator.auth.scopes import CONTENT_READ, CONTENT_WRITE
from coalsense_orchestrator.auth.sessions import Principal
from coalsense_orchestrator.consent.encrypted_store import MAX_ENVELOPE_BYTES
from coalsense_orchestrator.policy.loader import PolicySnapshot, parse_policy

from .config import DatabaseSettings
from .roles import PersistenceError, person_scope

TaskKind = Literal["email", "document", "social"]
TaskState = Literal["draft", "paused"]
Row = Mapping[str, object]
_ERRORS = frozenset(
    {
        "persistence.configuration.invalid",
        "persistence.unavailable",
        "persistence.role.invalid",
        "persistence.access.denied",
        "persistence.policy.denied",
        "persistence.input.invalid",
        "persistence.task.changed",
        "persistence.policy.invalid",
        "persistence.policy.version.conflict",
    }
)


def _protected[**P, T](function: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """No deja cruzar contextos de excepción adjuntados por contextlib/asyncpg."""

    @wraps(function)
    async def run(*args: P.args, **kwargs: P.kwargs) -> T:
        code = "persistence.unavailable"
        try:
            return await function(*args, **kwargs)
        except PersistenceError as error:
            if str(error) in _ERRORS:
                code = str(error)
        except Exception:
            pass
        # Excepción nueva, después de salir también del contexto de los await.
        raise PersistenceError(code)

    return run


class _Connection(Protocol):
    def transaction(self) -> AbstractAsyncContextManager[None]: ...
    def is_in_transaction(self) -> bool: ...
    async def execute(self, query: str, *args: object) -> str: ...
    async def fetchrow(self, query: str, *args: object) -> Row | None: ...
    async def fetch(self, query: str, *args: object) -> list[Row]: ...


class _Pool(Protocol):
    def acquire(self) -> AbstractAsyncContextManager[_Connection]: ...
    async def close(self) -> None: ...


class WritePolicy(Protocol):
    async def permits(self, person_id: UUID, operation: str, resource_id: UUID) -> bool: ...


@dataclass(frozen=True)
class StoredTask:
    id: UUID
    person_id: UUID
    kind: TaskKind
    state: TaskState
    autonomy_level: Literal["N0"]
    revision: int
    created_at: datetime
    updated_at: datetime


def _task(row: Row) -> StoredTask:
    return StoredTask(
        UUID(str(row["id"])),
        UUID(str(row["person_id"])),
        cast(TaskKind, row["kind"]),
        cast(TaskState, row["state"]),
        cast(Literal["N0"], row["autonomy_level"]),
        cast(int, row["revision"]),
        cast(datetime, row["created_at"]),
        cast(datetime, row["updated_at"]),
    )


def _policy_snapshot(row: Row) -> PolicySnapshot:
    canonical = row["canonical"]
    if type(canonical) is not str:
        raise PersistenceError("persistence.policy.invalid")
    snapshot = parse_policy(json.loads(canonical))
    if (
        snapshot.version != row["version"]
        or snapshot.canonical != canonical
        or snapshot.digest != row["digest"]
    ):
        raise PersistenceError("persistence.policy.invalid")
    return snapshot


class PersistenceService:
    def __init__(self, pool: _Pool, policy: WritePolicy | None) -> None:
        self._pool, self._policy = pool, policy

    @classmethod
    @_protected
    async def connect(
        cls, settings: DatabaseSettings, *, policy: WritePolicy | None = None
    ) -> "PersistenceService":
        # Revalidar también configuraciones construidas sin la fábrica.
        settings = DatabaseSettings.from_dsn(
            settings.dsn.get_secret_value(), testing_local=settings.testing_local
        )
        pool: _Pool | None = None
        ready = False
        error = "persistence.unavailable"
        try:
            pool = cast(
                _Pool,
                await asyncpg.create_pool(
                    settings.dsn.get_secret_value(),
                    ssl=settings.tls(),
                    min_size=1,
                    max_size=2,
                    timeout=5,
                    command_timeout=5,  # [SUPUESTO] Presupuestos técnicos, no decisiones humanas.
                    server_settings={
                        "search_path": "pg_catalog",
                        "application_name": "coalsense-persistence",
                    },
                ),
            )
            async with pool.acquire() as connection:
                role = await connection.fetchrow("""
                    select r.rolsuper, r.rolbypassrls, r.rolcreaterole,
                           r.rolcreatedb, r.rolreplication,
                           pg_has_role(current_user, 'admin', 'MEMBER') as is_admin,
                           pg_has_role(current_user, 'app_rw', 'USAGE') as can_write,
                           exists (
                               select 1 from pg_roles g where g.rolname = 'app_rw'
                               and (g.rolcanlogin or g.rolsuper or g.rolbypassrls
                                    or g.rolcreaterole or g.rolcreatedb or g.rolreplication)
                           ) as unsafe_group
                    from pg_roles r where r.rolname = current_user
                """)
            if (
                role
                and role["can_write"] is True
                and not any(
                    role[name]
                    for name in (
                        "rolsuper",
                        "rolbypassrls",
                        "rolcreaterole",
                        "rolcreatedb",
                        "rolreplication",
                        "is_admin",
                        "unsafe_group",
                    )
                )
            ):
                ready = True
                return cls(pool, policy)
            error = "persistence.role.invalid"
        except Exception:
            pass
        finally:
            if pool is not None and not ready:
                try:
                    await pool.close()
                except Exception:
                    pass
        raise PersistenceError(error)

    @_protected
    async def close(self) -> None:
        failed = False
        try:
            await self._pool.close()
        except Exception:
            failed = True
        if failed:
            raise PersistenceError("persistence.unavailable")

    @asynccontextmanager
    async def _transaction(self, person_id: UUID) -> AsyncIterator[_Connection]:
        failed = False
        try:
            async with self._pool.acquire() as connection, connection.transaction():
                await connection.execute(
                    "select pg_catalog.set_config('coalsense.person_id', $1, true)", str(person_id)
                )
                yield connection
        except PersistenceError:
            raise
        except Exception:
            failed = True
        if failed:
            raise PersistenceError("persistence.unavailable")

    async def _permit(self, person_id: UUID, operation: str, resource_id: UUID) -> None:
        decision: object = None
        try:
            if self._policy is not None:
                decision = await self._policy.permits(person_id, operation, resource_id)
        except Exception:
            pass
        if decision is not True:
            raise PersistenceError("persistence.policy.denied")

    async def _record(
        self, connection: _Connection, person_id: UUID, operation: str, resource_id: UUID
    ) -> None:
        await append_event(
            connection,
            person_id,
            AuditDraft(
                "task.created" if operation == "task.create" else "task.paused",
                "ok",
                AuditRefs(task_id=resource_id, actor_id=person_id, actor_origin="person"),
            ),
        )

    @_protected
    async def audit_events(self, principal: Principal) -> tuple[AuditRecord, ...]:
        owner = person_scope(principal, CONTENT_READ)
        async with self._transaction(owner) as connection:
            return (await read_chain(connection, owner)).records

    @_protected
    async def append_audit(self, principal: Principal, draft: AuditDraft) -> AuditRecord:
        """Puerto interno del servidor; retorna después del commit. No es una ruta de cliente."""
        # Registrar una lectura es instrumentación del servidor, no una modificación
        # del contenido. El registro no depende del permiso de editar un borrador.
        owner = person_scope(principal, CONTENT_READ)
        async with self._transaction(owner) as connection:
            return await append_event(connection, owner, draft)

    @_protected
    async def append_consent_envelope(self, person: UUID, record: UUID, envelope: bytes) -> None:
        """Puerto privado para el adaptador cifrado, sin ruta de cliente."""
        if (
            type(person) is not UUID
            or type(record) is not UUID
            or type(envelope) is not bytes
            or not 0 < len(envelope) <= MAX_ENVELOPE_BYTES
        ):
            raise PersistenceError("persistence.input.invalid")
        async with self._transaction(person) as connection:
            # Serializa el orden de inserción y confirmación de una persona.
            await connection.execute(
                """
                select pg_catalog.pg_advisory_xact_lock(
                    pg_catalog.hashtextextended('coalsense.consent:' || $1::text, 0)
                )
                """,
                str(person),
            )
            await connection.execute(
                """
                insert into coalsense.consent_record(person_id, id, envelope) values($1, $2, $3)
                """,
                person,
                record,
                envelope,
            )

    @_protected
    async def consent_envelopes(self, person: UUID) -> tuple[tuple[UUID, bytes], ...]:
        if type(person) is not UUID:
            raise PersistenceError("persistence.input.invalid")
        async with self._transaction(person) as connection:
            rows = await connection.fetch(
                "select id, envelope from coalsense.consent_record order by ordinal"
            )
            return tuple((UUID(str(row["id"])), cast(bytes, row["envelope"])) for row in rows)

    @_protected
    async def active_policy(self, principal: Principal) -> PolicySnapshot | None:
        owner = person_scope(principal, CONTENT_READ)
        async with self._transaction(owner) as connection:
            row = await connection.fetchrow(
                """
                select v.version, v.canonical, v.digest
                from coalsense.policy_active a join coalsense.policy_version v
                  on (v.person_id, v.version) = (a.person_id, a.version)
                where a.person_id = $1
            """,
                owner,
            )
            return _policy_snapshot(row) if row is not None else None

    @_protected
    async def activate_policy(self, principal: Principal, snapshot: PolicySnapshot) -> bool:
        """Instalación interna de configuración validada; no modifica la autonomía de tareas."""
        owner = person_scope(principal, CONTENT_WRITE)
        if type(snapshot) is not PolicySnapshot:
            raise PersistenceError("persistence.input.invalid")
        async with self._transaction(owner) as connection:
            await connection.execute(
                """
                select pg_catalog.pg_advisory_xact_lock(
                    pg_catalog.hashtextextended('coalsense.policy:' || $1::text, 0)
                )
            """,
                str(owner),
            )
            active = await connection.fetchrow(
                """
                select v.version, v.canonical, v.digest
                from coalsense.policy_active a join coalsense.policy_version v
                  on (v.person_id, v.version) = (a.person_id, a.version)
                where a.person_id = $1
            """,
                owner,
            )
            if active is not None:
                current = _policy_snapshot(active)
                if snapshot.version < current.version:
                    raise PersistenceError("persistence.policy.version.conflict")
                if snapshot.version == current.version:
                    if snapshot.digest != current.digest:
                        raise PersistenceError("persistence.policy.version.conflict")
                    return False
            existing = await connection.fetchrow(
                """
                select version, canonical, digest from coalsense.policy_version
                where person_id = $1 and version = $2
            """,
                owner,
                snapshot.version,
            )
            if existing is not None:
                if _policy_snapshot(existing).digest != snapshot.digest:
                    raise PersistenceError("persistence.policy.version.conflict")
            else:
                await connection.execute(
                    """
                    insert into coalsense.policy_version(person_id, version, canonical, digest)
                    values ($1, $2, $3, $4)
                """,
                    owner,
                    snapshot.version,
                    snapshot.canonical,
                    snapshot.digest,
                )
            await connection.execute(
                """
                insert into coalsense.policy_active(person_id, version) values ($1, $2)
                on conflict(person_id) do update set version = excluded.version
            """,
                owner,
                snapshot.version,
            )
            await append_event(
                connection,
                owner,
                AuditDraft(
                    "policy",
                    "ok",
                    AuditRefs(
                        policy_version=snapshot.version,
                        rule_id="policy.activation",
                        actor_origin="system",
                    ),
                ),
            )
            return True

    @_protected
    async def create_task(self, principal: Principal, kind: TaskKind) -> StoredTask:
        owner = person_scope(principal, CONTENT_WRITE)
        if type(kind) is not str or kind not in ("email", "document", "social"):
            raise PersistenceError("persistence.input.invalid")
        identifier = UUID(new_id())
        await self._permit(owner, "task.create", identifier)
        async with self._transaction(owner) as connection:
            row = await connection.fetchrow(
                """
                insert into coalsense.task (id, person_id, kind) values ($1, $2, $3) returning *
            """,
                identifier,
                owner,
                kind,
            )
            if row is None:
                raise PersistenceError("persistence.unavailable")
            await self._record(connection, owner, "task.create", identifier)
            return _task(row)

    @_protected
    async def list_tasks(self, principal: Principal) -> tuple[StoredTask, ...]:
        owner = person_scope(principal, CONTENT_READ)
        async with self._transaction(owner) as connection:
            rows = await connection.fetch("select * from coalsense.task order by id")
            return tuple(_task(row) for row in rows)

    @_protected
    async def get_task(self, principal: Principal, identifier: UUID) -> StoredTask | None:
        owner = person_scope(principal, CONTENT_READ)
        if type(identifier) is not UUID:
            raise PersistenceError("persistence.input.invalid")
        async with self._transaction(owner) as connection:
            row = await connection.fetchrow(
                "select * from coalsense.task where id = $1", identifier
            )
            return _task(row) if row is not None else None

    @_protected
    async def pause_task(self, principal: Principal, identifier: UUID, revision: int) -> StoredTask:
        owner = person_scope(principal, CONTENT_WRITE)
        if type(identifier) is not UUID or type(revision) is not int or revision < 1:
            raise PersistenceError("persistence.input.invalid")
        await self._permit(owner, "task.pause", identifier)
        async with self._transaction(owner) as connection:
            row = await connection.fetchrow(
                """
                update coalsense.task
                set state = 'paused', revision = revision + 1, updated_at = now()
                where id = $1 and revision = $2 and state <> 'paused' returning *
            """,
                identifier,
                revision,
            )
            if row is None:
                raise PersistenceError("persistence.task.changed")
            await self._record(connection, owner, "task.pause", identifier)
            return _task(row)
