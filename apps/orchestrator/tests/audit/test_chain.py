"""REQ-02-080: metadatos cerrados, cadena determinista y detección de alteraciones."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.audit.chain import ChainHead, build_record, verify_chain
from coalsense_orchestrator.audit.events import AuditDraft, AuditError, AuditRefs
from hypothesis import given
from hypothesis import strategies as st


def sample():
    person = UUID(new_id())
    draft = AuditDraft("control.stop", "ok", AuditRefs(actor_origin="person", actor_id=person))
    first = build_record(person, 1, draft, "0" * 64, at=datetime(2026, 11, 18, tzinfo=UTC))
    second = build_record(person, 2, draft, first.hash, at=first.at)
    return person, (first, second)


def test_chain_roundtrip_and_an_external_head_detects_tail_truncation() -> None:
    person, records = sample()
    head = verify_chain(person, records)
    assert head == ChainHead(person, 2, records[-1].hash)
    assert verify_chain(person, records, expected_head=head) == head
    with pytest.raises(AuditError, match="^audit.integrity.invalid$"):
        verify_chain(person, records[:1], expected_head=head)
    assert verify_chain(person, ()) == ChainHead(person, 0, "0" * 64)


def test_tampering_reordering_deletion_and_another_person_are_detected() -> None:
    person, records = sample()
    for changed in (
        (replace(records[0], draft=AuditDraft("control.undo", "ok")), records[1]),
        (records[1], records[0]),
        (records[1],),
        (replace(records[0], person_id=UUID(new_id())), records[1]),
        (records[0], replace(records[1], prev_hash="f" * 64)),
    ):
        with pytest.raises(AuditError, match="^audit.integrity.invalid$"):
            verify_chain(person, changed)


@pytest.mark.parametrize("field", ["text", "body", "profile", "recipient", "filename", "crisis"])
def test_neither_events_nor_references_accept_content_fields(field: str) -> None:
    for payload in (
        {"kind": "control.stop", "result": "ok", field: "Contenido privado"},
        {"kind": "control.stop", "result": "ok", "refs": {field: "Contenido privado"}},
    ):
        with pytest.raises(AuditError, match="^audit.event.invalid$") as caught:
            AuditDraft.from_payload(payload)
        assert "privado" not in str(caught.value)
        assert caught.value.__context__ is None


@given(st.text().filter(lambda key: key not in {"kind", "result", "refs"}))
def test_every_unknown_event_field_is_rejected(key: str) -> None:
    with pytest.raises(AuditError):
        AuditDraft.from_payload({"kind": "policy", "result": "denied", key: "private"})


@pytest.mark.parametrize(
    "refs",
    [
        {"task_id": "private"},
        {"actor_origin": "operator"},
        {"tool_name": "Una nota privada"},
        {"effect_class": "unknown"},
        {"policy_version": True},
        {"policy_version": 0},
        {"policy_version": 1.0},
        {"task_id": None},
        {"tool_name": "email.send\n"},
    ],
)
def test_reference_types_are_strict(refs: object) -> None:
    with pytest.raises(AuditError):
        AuditDraft.from_payload({"kind": "tool", "result": "ok", "refs": refs})


def test_hash_binds_every_metadata_field_and_uses_utc_microseconds() -> None:
    person, records = sample()
    original = records[0]
    again = build_record(
        person, 1, original.draft, original.prev_hash, event_id=original.id, at=original.at
    )
    assert again.hash == original.hash
    changed = build_record(
        person,
        1,
        original.draft,
        original.prev_hash,
        event_id=original.id,
        at=original.at.replace(microsecond=1),
    )
    assert changed.hash != original.hash


def test_version_one_and_two_can_share_a_chain_without_rehashing_history() -> None:
    person = UUID(new_id())
    first = build_record(person, 1, AuditDraft("control.stop", "ok"), "0" * 64, schema_version=1)
    second = build_record(
        person,
        2,
        AuditDraft(
            "policy",
            "pending",
            AuditRefs(
                action_id=UUID(new_id()),
                rule_id="guard.n0",
                policy_version=1,
            ),
        ),
        first.hash,
    )
    assert (first.schema_version, second.schema_version) == (1, 2)
    assert verify_chain(person, (first, second)).hash == second.hash
    changed = replace(
        second, draft=replace(second.draft, refs=replace(second.draft.refs, rule_id="guard.final"))
    )
    with pytest.raises(AuditError, match="^audit.integrity.invalid$"):
        verify_chain(person, (first, changed))
    with pytest.raises(AuditError):
        build_record(person, 1, second.draft, "0" * 64, schema_version=1)
