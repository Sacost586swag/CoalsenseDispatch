"""Una aprobación de baja confianza nunca se convierte en permiso (REQ-01-011)."""

import math
from dataclasses import dataclass

from coalsense_intents import Intent


@dataclass(frozen=True, slots=True)
class ApprovalFeedback:
    code: str
    pending_action_id: str
    # Solo metadatos; no la frase reconocida ni el contenido de la acción.


class ApprovalGuard:
    def __init__(self, minimum_confidence: float) -> None:
        if (
            isinstance(minimum_confidence, bool)
            or not math.isfinite(minimum_confidence)
            or not 0 <= minimum_confidence <= 1
        ):
            raise ValueError("Invalid approval confidence threshold")
        self.minimum_confidence = minimum_confidence

    def check(self, intention: Intent) -> ApprovalFeedback | None:
        if (
            intention["type"] == "approval.approve"
            and intention["confidence"] < self.minimum_confidence
        ):
            return ApprovalFeedback("approval.uncertain", intention["pending_action_id"])
        return None
