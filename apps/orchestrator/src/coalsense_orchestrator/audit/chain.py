"""Framing v1 sin campos libres: una línea por campo ASCII, orden fijo y UTC."""

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hmac import compare_digest
from typing import Literal
from uuid import UUID

from coalsense_common import new_id

from .events import REF_KEYS, V2_KEYS, AuditDraft, AuditError, AuditRecord

GENESIS = "0" * 64


@dataclass(frozen=True)
class ChainHead:
    person_id: UUID
    seq: int
    hash: str

    def __post_init__(self) -> None:
        if (
            type(self.person_id) is not UUID
            or type(self.seq) is not int
            or self.seq < 0
            or type(self.hash) is not str
            or len(self.hash) != 64
            or any(character not in "0123456789abcdef" for character in self.hash)
            or (self.seq == 0 and self.hash != GENESIS)
        ):
            raise AuditError("audit.integrity.invalid")


def calculate_hash(record: AuditRecord) -> str:
    refs = record.draft.refs.to_payload()
    at = record.at.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    parts = [
        "coalsense.audit.v" + str(record.schema_version),
        str(record.id),
        str(record.person_id),
        str(record.seq),
        at,
        record.draft.kind,
        record.draft.result,
        *(str(refs.get(name, "-")) for name in REF_KEYS),
        *(str(refs.get(name, "-")) for name in V2_KEYS if record.schema_version == 2),
        record.prev_hash,
    ]
    return hashlib.sha256(("\n".join(parts) + "\n").encode("ascii")).hexdigest()


def build_record(
    person_id: UUID,
    seq: int,
    draft: AuditDraft,
    prev_hash: str,
    *,
    event_id: UUID | None = None,
    at: datetime | None = None,
    schema_version: Literal[1, 2] = 2,
) -> AuditRecord:
    record = AuditRecord(
        event_id if event_id is not None else UUID(new_id()),
        person_id,
        seq,
        at if at is not None else datetime.now(UTC),
        draft,
        prev_hash,
        GENESIS,
        schema_version,
    )
    return replace(record, hash=calculate_hash(record))


def verify_chain(
    person_id: UUID, records: Iterable[AuditRecord], *, expected_head: ChainHead | None = None
) -> ChainHead:
    head = ChainHead(person_id, 0, GENESIS)
    seen: set[UUID] = set()
    for record in records:
        if (
            type(record) is not AuditRecord
            or record.person_id != person_id
            or record.seq != head.seq + 1
            or record.id in seen
            or not compare_digest(record.prev_hash, head.hash)
            or not compare_digest(record.hash, calculate_hash(record))
        ):
            raise AuditError("audit.integrity.invalid")
        head = ChainHead(person_id, record.seq, record.hash)
        seen.add(record.id)
    if expected_head is not None and head != expected_head:
        raise AuditError("audit.integrity.invalid")
    return head
