"""Contratos cerrados: el agente solicita una herramienta, no declara permisos."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from coalsense_intents import ContractError, validate_tool_name
from coalsense_intents.models import ToolEffectClass

Verdict = Literal["allow", "require_approval", "deny"]
EFFECTS: tuple[ToolEffectClass, ...] = ("read", "internal_write", "external_effect")
VERDICTS = ("allow", "require_approval", "deny")
MAX_VERSION = 9_007_199_254_740_991  # Entero seguro compartible con TypeScript.


class PolicyError(ValueError):
    """Código fijo: no refleja entrada, configuración ni excepción de otro servicio."""


@dataclass(frozen=True)
class Rule:
    id: str
    effect_class: ToolEffectClass
    decision: Verdict

    def __post_init__(self) -> None:
        valid = False
        try:
            validate_tool_name(self.id)
            valid = True
        except ContractError:
            pass
        if (
            not valid
            or self.id.startswith(("guard.", "policy."))
            or type(self.effect_class) is not str
            or self.effect_class not in EFFECTS
            or type(self.decision) is not str
            or self.decision not in VERDICTS
            or (self.effect_class == "external_effect" and self.decision == "allow")
        ):
            raise PolicyError("policy.configuration.invalid")


@dataclass(frozen=True)
class EvaluationRequest:
    action_id: UUID
    task_id: UUID
    tool_name: str

    def __post_init__(self) -> None:
        valid = False
        try:
            validate_tool_name(self.tool_name)
            valid = True
        except ContractError:
            pass
        if not valid or type(self.action_id) is not UUID or type(self.task_id) is not UUID:
            raise PolicyError("policy.request.invalid")

    @classmethod
    def from_payload(cls, value: object) -> "EvaluationRequest":
        result: EvaluationRequest | None = None
        try:
            if type(value) is not dict or set(value) != {"action_id", "task_id", "tool_name"}:
                raise ValueError
            for key in ("action_id", "task_id"):
                if type(value[key]) is not str or str(UUID(value[key])) != value[key]:
                    raise ValueError
            result = cls(UUID(value["action_id"]), UUID(value["task_id"]), value["tool_name"])
        except Exception:
            pass
        if result is None:
            raise PolicyError("policy.request.invalid")
        return result


@dataclass(frozen=True)
class PolicyDecision:
    verdict: Verdict
    rule_id: str
    policy_version: int | None
    audit_event_id: UUID | None
    action_id: UUID | None
    task_id: UUID | None
    tool_name: str | None
    effect_class: ToolEffectClass
    context_revision: int | None
    policy_digest: str | None

    def __post_init__(self) -> None:
        if self.verdict != "deny" and (
            self.audit_event_id is None
            or self.policy_version is None
            or self.context_revision is None
        ):
            raise PolicyError("policy.decision.invalid")
