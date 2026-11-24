"""Escritores v1 y v2 conservan una cadena común tras la migración de políticas."""

import asyncio
import json
from pathlib import Path
from uuid import UUID

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.audit.chain import build_record
from coalsense_orchestrator.audit.events import AuditDraft, AuditRefs
from coalsense_orchestrator.audit.log import append_event, read_chain
from coalsense_orchestrator.persistence.migrations import apply_migrations

from .conftest import DatabaseFixture


@pytest.mark.integration
def test_v1_events_remain_valid_and_historical_writers_can_still_append(
    database: DatabaseFixture,
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        root = Path(__file__).resolve().parents[2] / "migrations"
        for path in root.glob("*.sql"):
            if path.name < "0004_policy.sql":
                (tmp_path / path.name).write_bytes(path.read_bytes())
        async with database.isolated_database() as isolated:
            admin = await isolated.connection(admin=True)
            person = UUID(new_id())
            first = build_record(
                person, 1, AuditDraft("control.stop", "ok"), "0" * 64, schema_version=1
            )
            try:
                await apply_migrations(admin, tmp_path)
                connection = await isolated.connection()
                try:
                    async with connection.transaction():
                        await connection.execute(
                            "select set_config('coalsense.person_id', $1, true)", str(person)
                        )
                        await connection.execute(
                            """
                            insert into coalsense.audit_event
                                (id,person_id,seq,at,kind,result,refs,prev_hash,hash)
                            values($1,$2,1,$3,'control.stop','ok','{}',$4,$5)
                        """,
                            first.id,
                            person,
                            first.at,
                            first.prev_hash,
                            first.hash,
                        )
                finally:
                    await connection.close()
                assert await apply_migrations(admin, root) == tuple(
                    sorted(
                        path.name for path in root.glob("*.sql") if path.name >= "0004_policy.sql"
                    )
                )
                connection = await isolated.connection()
                try:
                    async with connection.transaction():
                        await connection.execute(
                            "select set_config('coalsense.person_id', $1, true)", str(person)
                        )
                        second = await append_event(
                            connection,
                            person,
                            AuditDraft(
                                "policy",
                                "pending",
                                AuditRefs(
                                    action_id=UUID(new_id()),
                                    rule_id="guard.n0",
                                    policy_version=1,
                                ),
                            ),
                        )
                        third = build_record(
                            person,
                            3,
                            AuditDraft("control.undo", "ok"),
                            second.hash,
                            schema_version=1,
                        )
                        await connection.execute(
                            """
                            insert into coalsense.audit_event
                                (id,person_id,seq,at,kind,result,refs,prev_hash,hash)
                            values($1,$2,3,$3,'control.undo','ok',$4::jsonb,$5,$6)
                        """,
                            third.id,
                            person,
                            third.at,
                            json.dumps(third.draft.refs.to_payload()),
                            third.prev_hash,
                            third.hash,
                        )
                        chain = await read_chain(connection, person)
                        assert chain.records == (first, second, third)
                        assert [event.schema_version for event in chain.records] == [1, 2, 1]
                finally:
                    await connection.close()
            finally:
                await admin.close()

    asyncio.run(scenario())
