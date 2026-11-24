"""Solo movimiento adyacente y de un mismo adaptador se fusiona bajo saturación."""

import math
from copy import deepcopy

from coalsense_intents import Intent
from coalsense_intents.models import PointerMoveIntent


def coalesce(previous: Intent, current: Intent) -> PointerMoveIntent | None:
    if previous["type"] != "pointer.move" or current["type"] != "pointer.move":
        return None
    if previous["adapter"] != current["adapter"] or previous["modality"] != current["modality"]:
        return None
    if previous["actor_origin"] != current["actor_origin"]:
        return None
    if previous["payload"]["mode"] != current["payload"]["mode"]:
        return None
    merged = deepcopy(current)
    if current["payload"]["mode"] == "relative":
        x = previous["payload"]["x"] + current["payload"]["x"]
        y = previous["payload"]["y"] + current["payload"]["y"]
        try:
            if not math.isfinite(x) or not math.isfinite(y):
                return None
        except OverflowError:
            return None
        merged["payload"]["x"], merged["payload"]["y"] = x, y
    return merged
