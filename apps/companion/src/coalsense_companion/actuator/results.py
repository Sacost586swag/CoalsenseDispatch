"""Resultados sin texto escrito, nombres de ventanas ni excepciones del sistema."""

from dataclasses import dataclass

from coalsense_common.i18n_es import es


@dataclass(frozen=True, slots=True)
class ActuationResult:
    intent_id: str
    intent_type: str
    code: str
    message_es: str
    partial: bool = False


def result(
    intent_id: str,
    intent_type: str,
    code: str,
    *,
    partial: bool = False,
) -> ActuationResult:
    return ActuationResult(
        intent_id,
        intent_type,
        f"input.actuation.{code}",
        es[f"input.actuation.{code}.message"],
        partial,
    )
