"""Vista privada e inmutable del contenido propuesto para aprobación."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import cast
from uuid import UUID

from coalsense_intents.models import JsonValue

from coalsense_orchestrator.gateway.manifest import ToolManifest

from .rules import PolicyError


@dataclass(frozen=True)
class PendingAction:
    id: UUID
    task_id: UUID
    tool_name: str
    summary: str = field(repr=False)
    destinations: tuple[str, ...] = field(repr=False)
    _input: bytes = field(repr=False)
    content_digest: str

    def tool_input(self) -> JsonValue:
        """Cada lector recibe una copia independiente del valor mostrado."""
        return cast(JsonValue, json.loads(self._input))


def prepare_action(
    identifier: UUID,
    task_id: UUID,
    manifest: ToolManifest,
    summary: str,
    destinations: tuple[str, ...],
    value: object,
) -> PendingAction:
    if (
        type(summary) is not str
        or not summary.strip()
        or type(destinations) is not tuple
        or any(type(item) is not str or not item.strip() for item in destinations)
    ):
        raise PolicyError("approval.preview.invalid")
    prepared = manifest.validate_input(value)
    # ASCII JSON conserva cada punto de código y evita normalización de texto.
    frozen = json.dumps(prepared, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "ascii"
    )
    frame = json.dumps(
        ["coalsense.content.v1", manifest.name, summary, destinations, prepared],
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    return PendingAction(
        identifier,
        task_id,
        manifest.name,
        summary,
        destinations,
        frozen,
        hashlib.sha256(frame).hexdigest(),
    )
