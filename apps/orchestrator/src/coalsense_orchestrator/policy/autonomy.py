"""Tabla de la spec 03. Estas guardas no se configuran desde un agente."""

from coalsense_intents.models import ToolEffectClass

from .contexts import ExecutionContext
from .loader import PolicySnapshot
from .rules import Verdict


def choose_rule(
    snapshot: PolicySnapshot, context: ExecutionContext, effect: ToolEffectClass
) -> tuple[Verdict, str]:
    rule = snapshot.rule_for(effect)
    if rule.decision == "deny":
        return "deny", rule.id
    if effect == "external_effect":
        return "require_approval", rule.id
    if context.first_task is True:
        return "require_approval", "guard.first_task"
    if context.autonomy == "N0":
        return "require_approval", "guard.n0"
    if context.first_task is None:
        return "deny", "guard.context_incomplete"
    if context.stage == "final":
        return "require_approval", "guard.final"
    return rule.decision, rule.id
