"""Tipos cerrados de bitácora. Ningún campo admite contenido libre."""

from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Literal, cast
from uuid import UUID

from coalsense_intents import ContractError, validate_tool_name

EventKind = Literal[
    "task.created",
    "task.paused",
    "plan",
    "step",
    "tool",
    "policy",
    "approval",
    "control.stop",
    "control.undo",
    "derivation",
    "auth",
]
EventResult = Literal["ok", "pending", "failed", "denied", "cancelled"]
ActorOrigin = Literal["person", "caregiver", "system"]
EffectClass = Literal["read", "internal_write", "external_effect"]
KINDS = (
    "task.created",
    "task.paused",
    "plan",
    "step",
    "tool",
    "policy",
    "approval",
    "control.stop",
    "control.undo",
    "derivation",
    "auth",
)
RESULTS = ("ok", "pending", "failed", "denied", "cancelled")
UUID_KEYS = (
    "task_id",
    "plan_id",
    "step_id",
    "pending_action_id",
    "actor_id",
    "device_id",
    "session_id",
)
REF_KEYS = (*UUID_KEYS, "tool_name", "effect_class", "actor_origin", "policy_version")
V2_KEYS = ("action_id", "rule_id")


class AuditError(ValueError):
    """Código estable, sin entrada ni excepción de conversión."""


@dataclass(frozen=True)
class AuditRefs:
    task_id: UUID | None = None
    plan_id: UUID | None = None
    step_id: UUID | None = None
    pending_action_id: UUID | None = None
    actor_id: UUID | None = None
    device_id: UUID | None = None
    session_id: UUID | None = None
    tool_name: str | None = None
    effect_class: EffectClass | None = None
    actor_origin: ActorOrigin | None = None
    policy_version: int | None = None
    action_id: UUID | None = None
    rule_id: str | None = None

    def __post_init__(self) -> None:
        if any(
            getattr(self, name) is not None and type(getattr(self, name)) is not UUID
            for name in (*UUID_KEYS, "action_id")
        ):
            raise AuditError("audit.event.invalid")
        for identifier in (self.tool_name, self.rule_id):
            if identifier is None:
                continue
            valid = False
            try:
                validate_tool_name(identifier)
                valid = True
            except ContractError:
                pass
            if not valid:
                raise AuditError("audit.event.invalid")
        if (
            (
                self.effect_class is not None
                and (
                    type(self.effect_class) is not str
                    or self.effect_class not in ("read", "internal_write", "external_effect")
                )
            )
            or (
                self.actor_origin is not None
                and (
                    type(self.actor_origin) is not str
                    or self.actor_origin not in ("person", "caregiver", "system")
                )
            )
            or (
                self.policy_version is not None
                and (type(self.policy_version) is not int or self.policy_version < 1)
            )
        ):
            raise AuditError("audit.event.invalid")

    @classmethod
    def from_payload(cls, value: object) -> "AuditRefs":
        result: AuditRefs | None = None
        try:
            if type(value) is not dict or set(value) - set((*REF_KEYS, *V2_KEYS)):
                raise ValueError
            kwargs: dict[str, object] = {}
            for name, item in value.items():
                if item is None:
                    raise ValueError
                if name in (*UUID_KEYS, "action_id"):
                    if type(item) is not str or str(UUID(item)) != item:
                        raise ValueError
                    kwargs[name] = UUID(item)
                else:
                    kwargs[name] = item
            result = cls(**kwargs)  # type: ignore[arg-type]  # Se valida cada campo en __post_init__.
        except Exception:
            pass
        if result is None:
            raise AuditError("audit.event.invalid")
        return result

    def to_payload(self) -> dict[str, str | int]:
        result: dict[str, str | int] = {}
        for item in fields(self):
            value = getattr(self, item.name)
            if value is not None:
                result[item.name] = str(value) if type(value) is UUID else cast(str | int, value)
        return result


@dataclass(frozen=True)
class AuditDraft:
    kind: EventKind
    result: EventResult
    refs: AuditRefs = field(default_factory=AuditRefs)

    def __post_init__(self) -> None:
        if (
            type(self.kind) is not str
            or self.kind not in KINDS
            or type(self.result) is not str
            or self.result not in RESULTS
            or type(self.refs) is not AuditRefs
        ):
            raise AuditError("audit.event.invalid")

    @classmethod
    def from_payload(cls, value: object) -> "AuditDraft":
        result: AuditDraft | None = None
        try:
            if (
                type(value) is not dict
                or set(value) - {"kind", "result", "refs"}
                or not {"kind", "result"} <= set(value)
            ):
                raise ValueError
            result = cls(
                value["kind"], value["result"], AuditRefs.from_payload(value.get("refs", {}))
            )
        except Exception:
            pass
        if result is None:
            raise AuditError("audit.event.invalid")
        return result


@dataclass(frozen=True)
class AuditRecord:
    id: UUID
    person_id: UUID
    seq: int
    at: datetime
    draft: AuditDraft
    prev_hash: str
    hash: str
    schema_version: Literal[1, 2] = 2

    def __post_init__(self) -> None:
        if (
            type(self.id) is not UUID
            or type(self.person_id) is not UUID
            or type(self.seq) is not int
            or self.seq < 1
            or type(self.at) is not datetime
            or self.at.utcoffset() is None
            or type(self.draft) is not AuditDraft
            or type(self.schema_version) is not int
            or self.schema_version not in (1, 2)
            or (
                self.schema_version == 1
                and (self.draft.refs.action_id is not None or self.draft.refs.rule_id is not None)
            )
            or any(
                type(value) is not str
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
                for value in (self.prev_hash, self.hash)
            )
        ):
            raise AuditError("audit.event.invalid")
