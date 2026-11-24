"""La prioridad procede exclusivamente del catálogo compartido."""

from coalsense_intents import priority_for


def preemptive(kind: str) -> bool:
    return priority_for(kind) == "preemptive"
