"""Políticas reales por persona, versiones inmutables y activación auditada atómica."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest
from coalsense_common import new_id
from coalsense_orchestrator.auth.scopes import APPROVAL_DECIDE, CONTENT_READ
from coalsense_orchestrator.persistence.service import PersistenceError, PersistenceService
from coalsense_orchestrator.policy.approvals import ApprovalService
from coalsense_orchestrator.policy.contexts import TaskContextLookup
from coalsense_orchestrator.policy.engine import EvaluationRequest, PolicyEngine
from coalsense_orchestrator.policy.grant import GrantSigner
from coalsense_orchestrator.policy.loader import load_policy, parse_policy
from coalsense_orchestrator.policy.versions import PersistenceAudit

from ..policy.test_engine import Health, registry
from ..policy.test_grant import intent
from .conftest import DatabaseFixture
from .test_rls import AllowWrites, principal

pytestmark = pytest.mark.integration
CONFIG = Path(__file__).resolve().parents[2] / "config/policies/default.yaml"


def test_exact_approval_commits_only_metadata_in_postgres(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        owner = principal()
        owner = replace(owner, scopes=owner.scopes | {APPROVAL_DECIDE})
        store = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        try:
            task = await store.create_task(owner, "document")
            await store.activate_policy(owner, load_policy(CONFIG))
            catalog = registry()
            audit = PersistenceAudit(store)
            engine = PolicyEngine(
                catalog, store, TaskContextLookup(store, stage="final"), Health(), audit
            )
            approvals = ApprovalService(catalog, engine, audit, GrantSigner(b"t" * 32))
            action = await approvals.propose(
                owner,
                task.id,
                "sample.action",
                "Resumen sintético",
                ("Destino sintético",),
                {"body": "Contenido sintético"},
            )
            grant = await approvals.decide(owner, intent(action))
            assert grant is not None
            events = await store.audit_events(owner)
            event = events[-1].draft
            assert event.kind == "approval" and event.result == "ok"
            assert event.refs.pending_action_id == action.id
            assert event.refs.session_id == UUID(owner.session_id)
            assert "sintético" not in repr(events)
            assert grant.signature not in repr(events)
            assert (await approvals.claim(owner, grant)).tool_input() == {
                "body": "Contenido sintético"
            }
        finally:
            await store.close()

    asyncio.run(scenario())


def snapshot(version: int = 1):
    payload = json.loads(CONFIG.read_text("utf-8"))
    payload["version"] = version
    return parse_policy(payload)


def test_activation_is_idempotent_scoped_and_survives_service_restart(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        person, other = principal(), principal()
        service = await PersistenceService.connect(database.settings())
        try:
            assert await service.active_policy(person) is None
            assert await service.activate_policy(person, snapshot()) is True
            assert await service.activate_policy(person, snapshot()) is False
            assert await service.active_policy(other) is None
            events = await service.audit_events(person)
            assert len(events) == 1 and events[0].schema_version == 2
            assert events[0].draft.refs.rule_id == "policy.activation"
        finally:
            await service.close()
        restarted = await PersistenceService.connect(database.settings())
        try:
            assert await restarted.active_policy(person) == snapshot()
        finally:
            await restarted.close()

    asyncio.run(scenario())


def test_versions_cannot_be_replaced_or_implicitly_rolled_back(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        person = principal()
        service = await PersistenceService.connect(database.settings())
        try:
            await service.activate_policy(person, snapshot())
            changed = json.loads(snapshot().canonical)
            changed["rules"]["read"]["decision"] = "deny"
            with pytest.raises(PersistenceError, match="^persistence.policy.version.conflict$"):
                await service.activate_policy(person, parse_policy(changed))
            await service.activate_policy(person, snapshot(2))
            with pytest.raises(PersistenceError, match="^persistence.policy.version.conflict$"):
                await service.activate_policy(person, snapshot())
            assert (await service.active_policy(person)).version == 2
        finally:
            await service.close()

    asyncio.run(scenario())


def test_failed_activation_audit_keeps_the_previous_version(database: DatabaseFixture) -> None:
    async def scenario() -> None:
        person = principal()
        service = await PersistenceService.connect(database.settings())
        await service.activate_policy(person, snapshot())
        await database.admin_execute("revoke insert on coalsense.audit_event from app_rw")
        try:
            with pytest.raises(PersistenceError):
                await service.activate_policy(person, snapshot(2))
            assert await service.active_policy(person) == snapshot()
        finally:
            await database.admin_execute("grant insert on coalsense.audit_event to app_rw")
            await service.close()

    asyncio.run(scenario())


def test_database_rejects_permissive_external_policy_even_with_a_correct_digest(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        connection = await database.connection()
        person = principal()
        payload = json.loads(snapshot().canonical)
        payload["rules"]["external_effect"]["decision"] = "allow"
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        try:
            with pytest.raises(asyncpg.CheckViolationError):
                async with connection.transaction():
                    await connection.execute(
                        "select set_config('coalsense.person_id', $1, true)", person.account_id
                    )
                    await connection.execute(
                        """
                        insert into coalsense.policy_version(person_id, version, canonical, digest)
                        values ($1, 1, $2, encode(sha256(convert_to($2, 'UTF8')), 'hex'))
                    """,
                        UUID(person.account_id),
                        canonical,
                    )
        finally:
            await connection.close()

    asyncio.run(scenario())


def test_engine_uses_stored_n0_and_commits_action_rule_and_decision(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        person = principal()
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        try:
            task = await service.create_task(person, "document")
            await service.activate_policy(person, load_policy(CONFIG))
            engine = PolicyEngine(
                registry("read"),
                service,
                TaskContextLookup(service, stage="step"),
                Health(),
                PersistenceAudit(service),
            )
            request = EvaluationRequest(UUID(new_id()), task.id, "sample.action")
            decision = await engine.evaluate(person, request)
            assert decision.verdict == "require_approval" and decision.rule_id == "guard.n0"
            event = (await service.audit_events(person))[-1]
            assert event.id == decision.audit_event_id and event.draft.result == "pending"
            assert event.draft.refs.action_id == request.action_id
            assert (
                event.draft.refs.rule_id == decision.rule_id and event.draft.refs.task_id == task.id
            )
        finally:
            await service.close()

    asyncio.run(scenario())


def test_engine_observes_policy_and_pause_changes_on_each_evaluation(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        person = principal()
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        try:
            task = await service.create_task(person, "document")
            await service.activate_policy(person, snapshot())
            engine = PolicyEngine(
                registry("read"),
                service,
                TaskContextLookup(service, stage="step"),
                Health(),
                PersistenceAudit(service),
            )
            request = EvaluationRequest(UUID(new_id()), task.id, "sample.action")
            assert (await engine.evaluate(person, request)).verdict == "require_approval"
            updated = json.loads(snapshot(2).canonical)
            updated["rules"]["read"]["decision"] = "deny"
            await service.activate_policy(person, parse_policy(updated))
            denied = await engine.evaluate(person, request)
            assert denied.verdict == "deny" and denied.policy_version == 2
            assert denied.rule_id == "default.read"
            await service.pause_task(person, task.id, task.revision)
            paused = await engine.evaluate(person, request)
            assert paused.verdict == "deny" and paused.rule_id == "guard.paused"
        finally:
            await service.close()

    asyncio.run(scenario())


def test_real_audit_failure_turns_an_approval_decision_into_denial(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        person = principal()
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        task = await service.create_task(person, "document")
        await service.activate_policy(person, snapshot())
        engine = PolicyEngine(
            registry(),
            service,
            TaskContextLookup(service, stage="step"),
            Health(),
            PersistenceAudit(service),
        )
        await database.admin_execute("revoke insert on coalsense.audit_event from app_rw")
        try:
            result = await engine.evaluate(
                person, EvaluationRequest(UUID(new_id()), task.id, "sample.action")
            )
            assert result.verdict == "deny" and result.audit_event_id is None
        finally:
            await database.admin_execute("grant insert on coalsense.audit_event to app_rw")
            await service.close()

    asyncio.run(scenario())


def test_policy_versions_are_append_only_and_isolated_in_the_database(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        person, other = principal(), principal()
        service = await PersistenceService.connect(database.settings())
        await service.activate_policy(person, snapshot())
        await service.close()
        connection = await database.connection()
        try:
            async with connection.transaction():
                await connection.execute(
                    "select set_config('coalsense.person_id', $1, true)", other.account_id
                )
                assert await connection.fetch("select * from coalsense.policy_version") == []
                assert await connection.fetch("select * from coalsense.policy_active") == []
            for sql in (
                "update coalsense.policy_version set canonical='{}'",
                "delete from coalsense.policy_version",
                "truncate coalsense.policy_version",
            ):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.execute(sql)
        finally:
            await connection.close()

    asyncio.run(scenario())


def test_read_only_actor_can_record_policy_without_receiving_write_permission(
    database: DatabaseFixture,
) -> None:
    async def scenario() -> None:
        owner = principal()
        reader = replace(owner, scopes=frozenset({CONTENT_READ}))
        service = await PersistenceService.connect(database.settings(), policy=AllowWrites())
        try:
            task = await service.create_task(owner, "document")
            await service.activate_policy(owner, snapshot())
            engine = PolicyEngine(
                registry("read"),
                service,
                TaskContextLookup(service, stage="step"),
                Health(),
                PersistenceAudit(service),
            )
            result = await engine.evaluate(
                reader, EvaluationRequest(UUID(new_id()), task.id, "sample.action")
            )
            assert result.verdict == "require_approval" and result.audit_event_id is not None
            assert (await service.audit_events(reader))[-1].id == result.audit_event_id
            with pytest.raises(PersistenceError):
                await service.activate_policy(reader, snapshot(2))
            with pytest.raises(PersistenceError):
                await service.pause_task(reader, task.id, task.revision)
        finally:
            await service.close()

    asyncio.run(scenario())
