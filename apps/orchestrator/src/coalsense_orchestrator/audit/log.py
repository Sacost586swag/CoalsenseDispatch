"""Acceso a bitácora mediante la transacción del servicio de persistencia.

No posee credenciales ni abre conexiones. El llamador debe propagar cualquier fallo
e impedir un efecto externo si el registro no pudo completarse.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol, cast
from uuid import UUID

from .chain import ChainHead, build_record, verify_chain
from .events import AuditDraft, AuditError, AuditRecord


class AuditConnection(Protocol):
    def is_in_transaction(self) -> bool: ...
    async def execute(self, query: str, *args: object) -> str: ...
    async def fetchrow(self, query: str, *args: object) -> Mapping[str, object] | None: ...
    async def fetch(self, query: str, *args: object) -> list[Mapping[str, object]]: ...


@dataclass(frozen=True)
class VerifiedChain:
    records: tuple[AuditRecord, ...]
    head: ChainHead


def _decode(row: Mapping[str, object]) -> AuditRecord:
    record: AuditRecord | None = None
    try:
        refs = json.loads(cast(str, row["refs"]))
        record = AuditRecord(
            UUID(str(row["id"])),
            UUID(str(row["person_id"])),
            cast(int, row["seq"]),
            cast(datetime, row["at"]),
            AuditDraft.from_payload(
                {
                    "kind": row["kind"],
                    "result": row["result"],
                    "refs": refs,
                }
            ),
            cast(str, row["prev_hash"]),
            cast(str, row["hash"]),
            cast(Literal[1, 2], row["schema_version"]),
        )
    except Exception:
        pass
    if record is None:
        raise AuditError("audit.integrity.invalid")
    return record


async def _scope(connection: AuditConnection, person_id: UUID) -> None:
    if type(person_id) is not UUID or connection.is_in_transaction() is not True:
        raise AuditError("audit.transaction.required")
    row = await connection.fetchrow(
        "select nullif(current_setting('coalsense.person_id', true), '') as owner"
    )
    if row is None or row["owner"] != str(person_id):
        raise AuditError("audit.scope.invalid")


async def read_chain(connection: AuditConnection, person_id: UUID) -> VerifiedChain:
    await _scope(connection, person_id)
    rows = await connection.fetch(
        "select * from coalsense.audit_event where person_id = $1 order by seq", person_id
    )
    records = tuple(_decode(row) for row in rows)
    return VerifiedChain(records, verify_chain(person_id, records))


async def append_event(
    connection: AuditConnection, person_id: UUID, draft: AuditDraft
) -> AuditRecord:
    if type(draft) is not AuditDraft:
        raise AuditError("audit.event.invalid")
    await _scope(connection, person_id)
    await connection.execute("select coalsense.audit_lock($1)", person_id)
    # Se comprueba el historial completo antes de extenderlo. El costo es lineal
    # por escritura; debe medirse con el volumen real antes de cambiar esta garantía.
    current = await read_chain(connection, person_id)
    record = build_record(person_id, current.head.seq + 1, draft, current.head.hash)
    await connection.execute(
        """
        insert into coalsense.audit_event
            (id, person_id, seq, at, kind, result, refs, prev_hash, hash, schema_version)
        values ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10)
    """,
        record.id,
        person_id,
        record.seq,
        record.at,
        draft.kind,
        draft.result,
        json.dumps(draft.refs.to_payload(), allow_nan=False),
        record.prev_hash,
        record.hash,
        record.schema_version,
    )
    return record
