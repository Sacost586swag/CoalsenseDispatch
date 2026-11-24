"""Generado desde schema/*.schema.json. No editar a mano."""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

type Modality = Literal["voice", "head_gesture", "keyboard_mouse", "gaze", "switch_scan"]


type ActorOrigin = Literal["person", "caregiver", "system"]


type Priority = Literal["preemptive", "normal"]


class Envelope(TypedDict):
    id: str
    modality: Modality
    adapter: str
    actor_origin: ActorOrigin
    monotonic_ts: int
    wall_ts: str


class EmptyPayload(TypedDict):
    pass


class PointerMovePayload(TypedDict):
    mode: Literal["relative", "absolute"]
    x: float
    y: float


class PointerButtonPayload(TypedDict):
    button: Literal["left", "right", "middle"]


class PointerScrollPayload(TypedDict):
    dx: float
    dy: float


class KeyPressPayload(TypedDict):
    keys: list[str]


class TextInsertPayload(TypedDict):
    text: str


class TextDictationPayload(TypedDict):
    text: str
    final: bool
    segment_id: NotRequired[str]


class NavSelectPayload(TypedDict):
    target_id: NotRequired[str]


class UiNumbersPayload(TypedDict):
    enabled: NotRequired[bool]


class UiGridPayload(TypedDict):
    level: NotRequired[int]
    cell: NotRequired[int]


class UiSelectPayload(TypedDict):
    by: Literal["number", "label", "id", "grid"]
    value: str


class ModeSetPayload(TypedDict):
    mode: Literal["command", "dictation", "sleep"]


class InputPausePayload(TypedDict):
    modality: NotRequired[Literal["voice", "head_gesture", "keyboard_mouse", "gaze", "switch_scan"]]


class ProfileSwitchPayload(TypedDict):
    profile_id: str


class CalibrationRequestPayload(TypedDict):
    modality: Literal["voice", "head_gesture", "keyboard_mouse", "gaze", "switch_scan"]


class CommandInvokePayload(TypedDict):
    name: str
    parameters: dict[str, str | float | bool | None]


class ControlStopIntent(Envelope):
    type: Literal["control.stop"]
    priority: Literal["preemptive"]
    payload: EmptyPayload
    confidence: NotRequired[float]


class ControlUndoIntent(Envelope):
    type: Literal["control.undo"]
    priority: Literal["preemptive"]
    payload: EmptyPayload
    confidence: NotRequired[float]


class HelpRequestHumanIntent(Envelope):
    type: Literal["help.request_human"]
    priority: Literal["preemptive"]
    payload: EmptyPayload
    confidence: NotRequired[float]


class ApprovalApproveIntent(Envelope):
    type: Literal["approval.approve"]
    priority: Literal["normal"]
    payload: EmptyPayload
    pending_action_id: str
    content_digest: str
    confidence: float


class ApprovalRejectIntent(Envelope):
    type: Literal["approval.reject"]
    priority: Literal["normal"]
    payload: EmptyPayload
    pending_action_id: str
    content_digest: str
    confidence: float


class PointerMoveIntent(Envelope):
    type: Literal["pointer.move"]
    priority: Literal["normal"]
    payload: PointerMovePayload
    confidence: NotRequired[float]


class PointerClickIntent(Envelope):
    type: Literal["pointer.click"]
    priority: Literal["normal"]
    payload: PointerButtonPayload
    confidence: NotRequired[float]


class PointerDoubleClickIntent(Envelope):
    type: Literal["pointer.double_click"]
    priority: Literal["normal"]
    payload: PointerButtonPayload
    confidence: NotRequired[float]


class PointerDragToggleIntent(Envelope):
    type: Literal["pointer.drag_toggle"]
    priority: Literal["normal"]
    payload: PointerButtonPayload
    confidence: NotRequired[float]


class PointerScrollIntent(Envelope):
    type: Literal["pointer.scroll"]
    priority: Literal["normal"]
    payload: PointerScrollPayload
    confidence: NotRequired[float]


class KeyPressIntent(Envelope):
    type: Literal["key.press"]
    priority: Literal["normal"]
    payload: KeyPressPayload
    confidence: NotRequired[float]


class TextInsertIntent(Envelope):
    type: Literal["text.insert"]
    priority: Literal["normal"]
    payload: TextInsertPayload
    confidence: NotRequired[float]


class TextDictationIntent(Envelope):
    type: Literal["text.dictation"]
    priority: Literal["normal"]
    payload: TextDictationPayload
    confidence: NotRequired[float]


class NavNextIntent(Envelope):
    type: Literal["nav.next"]
    priority: Literal["normal"]
    payload: EmptyPayload
    confidence: NotRequired[float]


class NavPreviousIntent(Envelope):
    type: Literal["nav.previous"]
    priority: Literal["normal"]
    payload: EmptyPayload
    confidence: NotRequired[float]


class NavSelectIntent(Envelope):
    type: Literal["nav.select"]
    priority: Literal["normal"]
    payload: NavSelectPayload
    confidence: NotRequired[float]


class NavBackIntent(Envelope):
    type: Literal["nav.back"]
    priority: Literal["normal"]
    payload: EmptyPayload
    confidence: NotRequired[float]


class UiShowNumbersIntent(Envelope):
    type: Literal["ui.show_numbers"]
    priority: Literal["normal"]
    payload: UiNumbersPayload
    confidence: NotRequired[float]


class UiShowGridIntent(Envelope):
    type: Literal["ui.show_grid"]
    priority: Literal["normal"]
    payload: UiGridPayload
    confidence: NotRequired[float]


class UiSelectTargetIntent(Envelope):
    type: Literal["ui.select_target"]
    priority: Literal["normal"]
    payload: UiSelectPayload
    confidence: NotRequired[float]


class ModeSetIntent(Envelope):
    type: Literal["mode.set"]
    priority: Literal["normal"]
    payload: ModeSetPayload
    confidence: NotRequired[float]


class InputPauseIntent(Envelope):
    type: Literal["input.pause"]
    priority: Literal["normal"]
    payload: InputPausePayload
    confidence: NotRequired[float]


class InputResumeIntent(Envelope):
    type: Literal["input.resume"]
    priority: Literal["normal"]
    payload: InputPausePayload
    confidence: NotRequired[float]


class ProfileSwitchIntent(Envelope):
    type: Literal["profile.switch"]
    priority: Literal["normal"]
    payload: ProfileSwitchPayload
    confidence: NotRequired[float]


class CalibrationRequestIntent(Envelope):
    type: Literal["calibration.request"]
    priority: Literal["normal"]
    payload: CalibrationRequestPayload
    confidence: NotRequired[float]


class CommandInvokeIntent(Envelope):
    type: Literal["command.invoke"]
    priority: Literal["normal"]
    payload: CommandInvokePayload
    confidence: NotRequired[float]


class VoiceTrigger(TypedDict):
    phrase: str


class GestureTrigger(TypedDict):
    gesture: str


class KeyboardTrigger(TypedDict):
    keys: list[str]


class GazeTrigger(TypedDict):
    target_id: str
    dwell_ms: float


class SwitchTrigger(TypedDict):
    switch: str


class Binding(TypedDict):
    modality: Literal["voice", "head_gesture", "keyboard_mouse", "gaze", "switch_scan"]
    trigger: VoiceTrigger | GestureTrigger | KeyboardTrigger | GazeTrigger | SwitchTrigger
    intent: Literal[
        "control.stop",
        "control.undo",
        "help.request_human",
        "approval.approve",
        "approval.reject",
        "pointer.move",
        "pointer.click",
        "pointer.double_click",
        "pointer.drag_toggle",
        "pointer.scroll",
        "key.press",
        "text.insert",
        "text.dictation",
        "nav.next",
        "nav.previous",
        "nav.select",
        "nav.back",
        "ui.show_numbers",
        "ui.show_grid",
        "ui.select_target",
        "mode.set",
        "input.pause",
        "input.resume",
        "profile.switch",
        "calibration.request",
        "command.invoke",
    ]


class GestureSettings(TypedDict):
    on: float
    off: float
    hold_ms: float
    cooldown_ms: float


class NeutralPose(TypedDict):
    yaw: float
    pitch: float


class VoiceSettings(TypedDict):
    enabled: bool
    gain: NotRequired[float]
    isolation_silence_ms: NotRequired[float]
    ambiguity_margin: NotRequired[float]


class HeadGestureSettings(TypedDict):
    enabled: bool
    pointer_mode: NotRequired[Literal["rate", "absolute"]]
    dead_zone: NotRequired[float]
    max_speed: NotRequired[float]
    tremor_filter: NotRequired[bool]
    camera_roll_deg: NotRequired[float]
    neutral_pose: NotRequired[NeutralPose]
    gestures: NotRequired[dict[str, GestureSettings]]


class KeyboardMouseSettings(TypedDict):
    enabled: bool


class GazeSettings(TypedDict):
    enabled: bool
    dwell_ms: NotRequired[float]
    approval_dwell_ms: NotRequired[float]


class SwitchScanSettings(TypedDict):
    enabled: bool
    interval_ms: NotRequired[float]


class FeedbackSettings(TypedDict):
    visual: bool
    audio: bool


class DeclaredCondition(TypedDict):
    text: str
    consent_ref: str
    category: Literal["special"]


class ModalitySettings(TypedDict):
    voice: NotRequired[VoiceSettings]
    head_gesture: NotRequired[HeadGestureSettings]
    keyboard_mouse: NotRequired[KeyboardMouseSettings]
    gaze: NotRequired[GazeSettings]
    switch_scan: NotRequired[SwitchScanSettings]


class CapabilityProfile(TypedDict):
    schema_version: Literal[1]
    profile_id: str
    label: str
    language: Literal["es-EC"]
    modalities: ModalitySettings
    bindings: list[Binding]
    approval_min_confidence: float
    min_target_px: int
    feedback: FeedbackSettings
    declared_condition: NotRequired[None | DeclaredCondition]


type StopRouteReason = Literal[
    "starting",
    "healthy",
    "device_unavailable",
    "model_loading",
    "adapter_unresponsive",
    "stop_unbound",
    "stale",
    "stopped",
]


class StopRouteHealth(TypedDict):
    identifier: str
    modality: Modality
    healthy: bool
    reason: StopRouteReason


class StopHealthSnapshot(TypedDict):
    stop_reachable: bool
    revision: int
    updated_at: str
    routes: list[StopRouteHealth]


class HeartbeatEvent(TypedDict):
    event: Literal["heartbeat"]
    schema_version: Literal[1]
    instance_id: str
    sequence: int
    wall_ts: str
    state: StopHealthSnapshot


type JsonValue = str | float | bool | None | list[JsonValue] | dict[str, JsonValue]


type ToolSchema = dict[str, JsonValue]


type ToolName = str


type ToolEffectClass = Literal["read", "internal_write", "external_effect"]


class ToolManifest(TypedDict):
    name: ToolName
    input_schema: ToolSchema
    output_schema: ToolSchema
    effect_class: NotRequired[ToolEffectClass]
    reversible: bool
    compensation: NotRequired[ToolName]
    data_categories: list[str]
    provider: str


type Intent = (
    ControlStopIntent
    | ControlUndoIntent
    | HelpRequestHumanIntent
    | ApprovalApproveIntent
    | ApprovalRejectIntent
    | PointerMoveIntent
    | PointerClickIntent
    | PointerDoubleClickIntent
    | PointerDragToggleIntent
    | PointerScrollIntent
    | KeyPressIntent
    | TextInsertIntent
    | TextDictationIntent
    | NavNextIntent
    | NavPreviousIntent
    | NavSelectIntent
    | NavBackIntent
    | UiShowNumbersIntent
    | UiShowGridIntent
    | UiSelectTargetIntent
    | ModeSetIntent
    | InputPauseIntent
    | InputResumeIntent
    | ProfileSwitchIntent
    | CalibrationRequestIntent
    | CommandInvokeIntent
)


MODALITIES: tuple[Modality, ...] = (
    "voice",
    "head_gesture",
    "keyboard_mouse",
    "gaze",
    "switch_scan",
)


ACTOR_ORIGINS: tuple[ActorOrigin, ...] = ("person", "caregiver", "system")
