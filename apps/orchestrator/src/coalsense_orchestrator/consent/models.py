"""Datos cerrados de una decisión y versión del texto confirmado."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from coalsense_intents.models import Modality

Decision = Literal["granted", "denied", "revoked"]
_IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,63}")
_MODALITIES = ("voice", "head_gesture", "keyboard_mouse", "gaze", "switch_scan")


class ConsentRecordError(ValueError):
    """Código fijo sin información privada."""


@dataclass(frozen=True)
class ConsentNotice:
    category: str
    provider: str
    text_version: int

    def __post_init__(self) -> None:
        if (
            any(
                type(v) is not str or _IDENTIFIER.fullmatch(v) is None
                for v in (self.category, self.provider)
            )
            or type(self.text_version) is not int
            or not 1 <= self.text_version <= 9_007_199_254_740_991
        ):
            raise ConsentRecordError("consent.notice.invalid")


@dataclass(frozen=True, repr=False)
class ConsentRecord:
    id: UUID
    notice: ConsentNotice
    decision: Decision
    modality: Modality
    at: datetime

    def __post_init__(self) -> None:
        if (
            type(self.id) is not UUID
            or type(self.notice) is not ConsentNotice
            or type(self.decision) is not str
            or self.decision not in ("granted", "denied", "revoked")
            or type(self.modality) is not str
            or self.modality not in _MODALITIES
            or type(self.at) is not datetime
            or self.at.utcoffset() is None
        ):
            raise ConsentRecordError("consent.record.invalid")
