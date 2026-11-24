"""Clasificación explícita de toda clase de actuación local (REQ-01-024)."""

from enum import StrEnum
from types import MappingProxyType


class ActionKind(StrEnum):
    POINTER_MOVE = "pointer.move"
    POINTER_CLICK = "pointer.click"
    POINTER_DOUBLE_CLICK = "pointer.double_click"
    POINTER_DRAG_TOGGLE = "pointer.drag_toggle"
    POINTER_SCROLL = "pointer.scroll"
    KEY_PRESS = "key.press"
    TEXT_INSERT = "text.insert"
    TEXT_DICTATION = "text.dictation"
    MODE_SET = "mode.set"
    PROFILE_SWITCH = "profile.switch"


class Reversibility(StrEnum):
    NEVER = "never"
    LOCAL = "local"
    VERIFIED = "verified"


ACTION_POLICIES = MappingProxyType(
    {
        ActionKind.POINTER_MOVE: Reversibility.NEVER,
        ActionKind.POINTER_CLICK: Reversibility.NEVER,
        ActionKind.POINTER_DOUBLE_CLICK: Reversibility.NEVER,
        ActionKind.POINTER_DRAG_TOGGLE: Reversibility.LOCAL,
        ActionKind.POINTER_SCROLL: Reversibility.NEVER,
        ActionKind.KEY_PRESS: Reversibility.NEVER,
        ActionKind.TEXT_INSERT: Reversibility.VERIFIED,
        ActionKind.TEXT_DICTATION: Reversibility.VERIFIED,
        ActionKind.MODE_SET: Reversibility.LOCAL,
        ActionKind.PROFILE_SWITCH: Reversibility.LOCAL,
    }
)
