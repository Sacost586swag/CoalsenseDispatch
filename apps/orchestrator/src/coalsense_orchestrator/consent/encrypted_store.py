"""Adaptador de ConsentStore. Solo entrega sobres cifrados a persistencia."""

import json
from datetime import datetime
from typing import Protocol
from uuid import UUID

from .models import ConsentNotice, ConsentRecord, ConsentRecordError

# [SUPUESTO] El sobre contiene solo una decisión y metadatos criptográficos.
MAX_ENVELOPE_BYTES = 8192


class ConsentCipher(Protocol):
    """Cifrado autenticado con DEK por persona y datos asociados obligatorios."""

    async def seal(self, person: UUID, plaintext: bytes, *, associated_data: bytes) -> bytes: ...
    async def open(self, person: UUID, envelope: bytes, *, associated_data: bytes) -> bytes: ...


class EnvelopeStore(Protocol):
    async def append_consent_envelope(
        self, person: UUID, record: UUID, envelope: bytes
    ) -> None: ...
    async def consent_envelopes(self, person: UUID) -> tuple[tuple[UUID, bytes], ...]: ...


def _context(person: UUID, record: UUID) -> bytes:
    return b"coalsense.consent.v1\x00" + person.bytes + record.bytes


def _valid_envelope(envelope: object) -> bool:
    return type(envelope) is bytes and 0 < len(envelope) <= MAX_ENVELOPE_BYTES


class EncryptedConsentStore:
    def __init__(self, storage: EnvelopeStore, cipher: ConsentCipher) -> None:
        self._storage, self._cipher = storage, cipher

    async def append(self, person: UUID, record: ConsentRecord) -> None:
        payload = json.dumps(
            {
                "category": record.notice.category,
                "provider": record.notice.provider,
                "text_version": record.notice.text_version,
                "decision": record.decision,
                "modality": record.modality,
                "at": record.at.isoformat(),
            },
            separators=(",", ":"),
        ).encode("ascii")
        envelope = await self._cipher.seal(
            person, payload, associated_data=_context(person, record.id)
        )
        if not _valid_envelope(envelope):
            raise ConsentRecordError("consent.envelope.invalid")
        await self._storage.append_consent_envelope(person, record.id, envelope)

    async def history(self, person: UUID) -> tuple[ConsentRecord, ...]:
        records: list[ConsentRecord] = []
        for identifier, envelope in await self._storage.consent_envelopes(person):
            if not _valid_envelope(envelope):
                raise ConsentRecordError("consent.envelope.invalid")
            payload = await self._cipher.open(
                person, envelope, associated_data=_context(person, identifier)
            )
            value = json.loads(payload)
            if type(value) is not dict or set(value) != {
                "category",
                "provider",
                "text_version",
                "decision",
                "modality",
                "at",
            }:
                raise ConsentRecordError("consent.record.invalid")
            records.append(
                ConsentRecord(
                    identifier,
                    ConsentNotice(value["category"], value["provider"], value["text_version"]),
                    value["decision"],
                    value["modality"],
                    datetime.fromisoformat(value["at"]),
                )
            )
        return tuple(records)
