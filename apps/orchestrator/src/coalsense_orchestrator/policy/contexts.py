"""Contexto del servidor. Ningún campo de salud o autonomía proviene de la solicitud."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol
from uuid import UUID

from coalsense_orchestrator.auth.sessions import Principal

from .rules import EvaluationRequest, PolicyError

if TYPE_CHECKING:
    from coalsense_orchestrator.persistence.service import StoredTask

Autonomy = Literal["N0", "N1", "N2"]
Stage = Literal["step", "final"]


@dataclass(frozen=True)
class ExecutionContext:
    person_id: UUID
    task_id: UUID
    task_kind: Literal["email", "document", "social"]
    autonomy: Autonomy
    stage: Stage
    first_task: bool | None
    paused: bool
    revision: int

    def __post_init__(self) -> None:
        if (
            type(self.person_id) is not UUID
            or type(self.task_id) is not UUID
            or self.task_kind not in ("email", "document", "social")
            or self.autonomy not in ("N0", "N1", "N2")
            or self.stage not in ("step", "final")
            or (self.first_task is not None and type(self.first_task) is not bool)
            or type(self.paused) is not bool
            or type(self.revision) is not int
            or self.revision < 1
        ):
            raise PolicyError("policy.context.invalid")


class ContextLookup(Protocol):
    async def lookup(
        self, actor: Principal, request: EvaluationRequest
    ) -> ExecutionContext | None: ...


class TaskReader(Protocol):
    async def get_task(self, principal: Principal, identifier: UUID) -> StoredTask | None: ...


class TaskContextLookup:
    def __init__(self, reader: TaskReader, *, stage: Stage) -> None:
        if stage not in ("step", "final"):
            raise PolicyError("policy.context.invalid")
        self._reader, self._stage = reader, stage

    async def lookup(self, actor: Principal, request: EvaluationRequest) -> ExecutionContext | None:
        task = await self._reader.get_task(actor, request.task_id)
        if task is None:
            return None
        # El servidor elige la etapa. La clasificación de primera tarea sigue
        # desconocida hasta conectar el flujo; todas las filas actuales permanecen N0.
        return ExecutionContext(
            task.person_id,
            task.id,
            task.kind,
            task.autonomy_level,
            self._stage,
            None,
            task.state == "paused",
            task.revision,
        )
