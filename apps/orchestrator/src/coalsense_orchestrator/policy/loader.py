"""Políticas YAML en el subconjunto JSON, sin constructores ni dependencias de ejecución."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from coalsense_intents.models import ToolEffectClass

from .rules import EFFECTS, MAX_VERSION, PolicyError, Rule


@dataclass(frozen=True)
class PolicySnapshot:
    version: int
    rules: tuple[Rule, ...]

    def __post_init__(self) -> None:
        if (
            type(self.version) is not int
            or not 1 <= self.version <= MAX_VERSION
            or type(self.rules) is not tuple
            or len(self.rules) != 3
            or any(type(rule) is not Rule for rule in self.rules)
            or {rule.effect_class for rule in self.rules} != set(EFFECTS)
            or len({rule.id for rule in self.rules}) != 3
        ):
            raise PolicyError("policy.configuration.invalid")

    def to_payload(self) -> dict[str, object]:
        return {
            "version": self.version,
            "rules": {
                rule.effect_class: {"id": rule.id, "decision": rule.decision} for rule in self.rules
            },
        }

    @property
    def canonical(self) -> str:
        return json.dumps(self.to_payload(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical.encode("ascii")).hexdigest()

    def rule_for(self, effect: ToolEffectClass) -> Rule:
        return next(rule for rule in self.rules if rule.effect_class == effect)


def parse_policy(value: object) -> PolicySnapshot:
    result: PolicySnapshot | None = None
    try:
        if type(value) is not dict or set(value) != {"version", "rules"}:
            raise ValueError
        rules = value["rules"]
        if type(rules) is not dict or set(rules) != set(EFFECTS):
            raise ValueError
        parsed: list[Rule] = []
        for effect in EFFECTS:
            rule = rules[effect]
            if type(rule) is not dict or set(rule) != {"id", "decision"}:
                raise ValueError
            parsed.append(Rule(rule["id"], effect, rule["decision"]))
        result = PolicySnapshot(value["version"], tuple(parsed))
    except Exception:
        pass
    if result is None:
        raise PolicyError("policy.configuration.invalid")
    return result


def load_policy(path: Path) -> PolicySnapshot:
    result: PolicySnapshot | None = None
    try:
        result = parse_policy(json.loads(path.read_text("utf-8")))
    except Exception:
        pass
    if result is None:
        raise PolicyError("policy.configuration.invalid")
    return result
