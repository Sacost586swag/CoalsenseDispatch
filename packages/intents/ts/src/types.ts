// Generado desde schema/*.schema.json. No editar a mano.

export type Modality = "voice" | "head_gesture" | "keyboard_mouse" | "gaze" | "switch_scan";

export type ActorOrigin = "person" | "caregiver" | "system";

export type Priority = "preemptive" | "normal";

export type Envelope = {
  "id": string;
  "modality": Modality;
  "adapter": string;
  "actor_origin": ActorOrigin;
  "monotonic_ts": number;
  "wall_ts": string;
};

export type EmptyPayload = Record<string, never>;

export type PointerMovePayload = {
  "mode": "relative" | "absolute";
  "x": number;
  "y": number;
};

export type PointerButtonPayload = {
  "button": "left" | "right" | "middle";
};

export type PointerScrollPayload = {
  "dx": number;
  "dy": number;
};

export type KeyPressPayload = {
  "keys": Array<string>;
};

export type TextInsertPayload = {
  "text": string;
};

export type TextDictationPayload = {
  "text": string;
  "final": boolean;
  "segment_id"?: string;
};

export type NavSelectPayload = {
  "target_id"?: string;
};

export type UiNumbersPayload = {
  "enabled"?: boolean;
};

export type UiGridPayload = {
  "level"?: number;
  "cell"?: number;
};

export type UiSelectPayload = {
  "by": "number" | "label" | "id" | "grid";
  "value": string;
};

export type ModeSetPayload = {
  "mode": "command" | "dictation" | "sleep";
};

export type InputPausePayload = {
  "modality"?: "voice" | "head_gesture" | "keyboard_mouse" | "gaze" | "switch_scan";
};

export type ProfileSwitchPayload = {
  "profile_id": string;
};

export type CalibrationRequestPayload = {
  "modality": "voice" | "head_gesture" | "keyboard_mouse" | "gaze" | "switch_scan";
};

export type CommandInvokePayload = {
  "name": string;
  "parameters": { [key: string]: string | number | boolean | null };
};

export type ControlStopIntent = Envelope & {
  "type": "control.stop";
  "priority": "preemptive";
  "payload": EmptyPayload;
  "confidence"?: number;
};

export type ControlUndoIntent = Envelope & {
  "type": "control.undo";
  "priority": "preemptive";
  "payload": EmptyPayload;
  "confidence"?: number;
};

export type HelpRequestHumanIntent = Envelope & {
  "type": "help.request_human";
  "priority": "preemptive";
  "payload": EmptyPayload;
  "confidence"?: number;
};

export type ApprovalApproveIntent = Envelope & {
  "type": "approval.approve";
  "priority": "normal";
  "payload": EmptyPayload;
  "pending_action_id": string;
  "content_digest": string;
  "confidence": number;
};

export type ApprovalRejectIntent = Envelope & {
  "type": "approval.reject";
  "priority": "normal";
  "payload": EmptyPayload;
  "pending_action_id": string;
  "content_digest": string;
  "confidence": number;
};

export type PointerMoveIntent = Envelope & {
  "type": "pointer.move";
  "priority": "normal";
  "payload": PointerMovePayload;
  "confidence"?: number;
};

export type PointerClickIntent = Envelope & {
  "type": "pointer.click";
  "priority": "normal";
  "payload": PointerButtonPayload;
  "confidence"?: number;
};

export type PointerDoubleClickIntent = Envelope & {
  "type": "pointer.double_click";
  "priority": "normal";
  "payload": PointerButtonPayload;
  "confidence"?: number;
};

export type PointerDragToggleIntent = Envelope & {
  "type": "pointer.drag_toggle";
  "priority": "normal";
  "payload": PointerButtonPayload;
  "confidence"?: number;
};

export type PointerScrollIntent = Envelope & {
  "type": "pointer.scroll";
  "priority": "normal";
  "payload": PointerScrollPayload;
  "confidence"?: number;
};

export type KeyPressIntent = Envelope & {
  "type": "key.press";
  "priority": "normal";
  "payload": KeyPressPayload;
  "confidence"?: number;
};

export type TextInsertIntent = Envelope & {
  "type": "text.insert";
  "priority": "normal";
  "payload": TextInsertPayload;
  "confidence"?: number;
};

export type TextDictationIntent = Envelope & {
  "type": "text.dictation";
  "priority": "normal";
  "payload": TextDictationPayload;
  "confidence"?: number;
};

export type NavNextIntent = Envelope & {
  "type": "nav.next";
  "priority": "normal";
  "payload": EmptyPayload;
  "confidence"?: number;
};

export type NavPreviousIntent = Envelope & {
  "type": "nav.previous";
  "priority": "normal";
  "payload": EmptyPayload;
  "confidence"?: number;
};

export type NavSelectIntent = Envelope & {
  "type": "nav.select";
  "priority": "normal";
  "payload": NavSelectPayload;
  "confidence"?: number;
};

export type NavBackIntent = Envelope & {
  "type": "nav.back";
  "priority": "normal";
  "payload": EmptyPayload;
  "confidence"?: number;
};

export type UiShowNumbersIntent = Envelope & {
  "type": "ui.show_numbers";
  "priority": "normal";
  "payload": UiNumbersPayload;
  "confidence"?: number;
};

export type UiShowGridIntent = Envelope & {
  "type": "ui.show_grid";
  "priority": "normal";
  "payload": UiGridPayload;
  "confidence"?: number;
};

export type UiSelectTargetIntent = Envelope & {
  "type": "ui.select_target";
  "priority": "normal";
  "payload": UiSelectPayload;
  "confidence"?: number;
};

export type ModeSetIntent = Envelope & {
  "type": "mode.set";
  "priority": "normal";
  "payload": ModeSetPayload;
  "confidence"?: number;
};

export type InputPauseIntent = Envelope & {
  "type": "input.pause";
  "priority": "normal";
  "payload": InputPausePayload;
  "confidence"?: number;
};

export type InputResumeIntent = Envelope & {
  "type": "input.resume";
  "priority": "normal";
  "payload": InputPausePayload;
  "confidence"?: number;
};

export type ProfileSwitchIntent = Envelope & {
  "type": "profile.switch";
  "priority": "normal";
  "payload": ProfileSwitchPayload;
  "confidence"?: number;
};

export type CalibrationRequestIntent = Envelope & {
  "type": "calibration.request";
  "priority": "normal";
  "payload": CalibrationRequestPayload;
  "confidence"?: number;
};

export type CommandInvokeIntent = Envelope & {
  "type": "command.invoke";
  "priority": "normal";
  "payload": CommandInvokePayload;
  "confidence"?: number;
};

export type VoiceTrigger = {
  "phrase": string;
};

export type GestureTrigger = {
  "gesture": string;
};

export type KeyboardTrigger = {
  "keys": Array<string>;
};

export type GazeTrigger = {
  "target_id": string;
  "dwell_ms": number;
};

export type SwitchTrigger = {
  "switch": string;
};

export type Binding = {
  "modality": "voice" | "head_gesture" | "keyboard_mouse" | "gaze" | "switch_scan";
  "trigger": VoiceTrigger | GestureTrigger | KeyboardTrigger | GazeTrigger | SwitchTrigger;
  "intent": "control.stop" | "control.undo" | "help.request_human" | "approval.approve" | "approval.reject" | "pointer.move" | "pointer.click" | "pointer.double_click" | "pointer.drag_toggle" | "pointer.scroll" | "key.press" | "text.insert" | "text.dictation" | "nav.next" | "nav.previous" | "nav.select" | "nav.back" | "ui.show_numbers" | "ui.show_grid" | "ui.select_target" | "mode.set" | "input.pause" | "input.resume" | "profile.switch" | "calibration.request" | "command.invoke";
};

export type GestureSettings = {
  "on": number;
  "off": number;
  "hold_ms": number;
  "cooldown_ms": number;
};

export type NeutralPose = {
  "yaw": number;
  "pitch": number;
};

export type VoiceSettings = {
  "enabled": boolean;
  "gain"?: number;
  "isolation_silence_ms"?: number;
  "ambiguity_margin"?: number;
};

export type HeadGestureSettings = {
  "enabled": boolean;
  "pointer_mode"?: "rate" | "absolute";
  "dead_zone"?: number;
  "max_speed"?: number;
  "tremor_filter"?: boolean;
  "camera_roll_deg"?: number;
  "neutral_pose"?: NeutralPose;
  "gestures"?: { [key: string]: GestureSettings };
};

export type KeyboardMouseSettings = {
  "enabled": boolean;
};

export type GazeSettings = {
  "enabled": boolean;
  "dwell_ms"?: number;
  "approval_dwell_ms"?: number;
};

export type SwitchScanSettings = {
  "enabled": boolean;
  "interval_ms"?: number;
};

export type FeedbackSettings = {
  "visual": boolean;
  "audio": boolean;
};

export type DeclaredCondition = {
  "text": string;
  "consent_ref": string;
  "category": "special";
};

export type ModalitySettings = {
  "voice"?: VoiceSettings;
  "head_gesture"?: HeadGestureSettings;
  "keyboard_mouse"?: KeyboardMouseSettings;
  "gaze"?: GazeSettings;
  "switch_scan"?: SwitchScanSettings;
};

export type CapabilityProfile = {
  "schema_version": 1;
  "profile_id": string;
  "label": string;
  "language": "es-EC";
  "modalities": ModalitySettings;
  "bindings": Array<Binding>;
  "approval_min_confidence": number;
  "min_target_px": number;
  "feedback": FeedbackSettings;
  "declared_condition"?: null | DeclaredCondition;
};

export type StopRouteReason = "starting" | "healthy" | "device_unavailable" | "model_loading" | "adapter_unresponsive" | "stop_unbound" | "stale" | "stopped";

export type StopRouteHealth = {
  "identifier": string;
  "modality": Modality;
  "healthy": boolean;
  "reason": StopRouteReason;
};

export type StopHealthSnapshot = {
  "stop_reachable": boolean;
  "revision": number;
  "updated_at": string;
  "routes": Array<StopRouteHealth>;
};

export type HeartbeatEvent = {
  "event": "heartbeat";
  "schema_version": 1;
  "instance_id": string;
  "sequence": number;
  "wall_ts": string;
  "state": StopHealthSnapshot;
};

export type JsonValue = string | number | boolean | null | Array<JsonValue> | { [key: string]: JsonValue };

export type ToolSchema = { [key: string]: JsonValue };

export type ToolName = string;

export type ToolEffectClass = "read" | "internal_write" | "external_effect";

export type ToolManifest = {
  "name": ToolName;
  "input_schema": ToolSchema;
  "output_schema": ToolSchema;
  "effect_class"?: ToolEffectClass;
  "reversible": boolean;
  "compensation"?: ToolName;
  "data_categories": Array<string>;
  "provider": string;
};

export type Intent = ControlStopIntent | ControlUndoIntent | HelpRequestHumanIntent | ApprovalApproveIntent | ApprovalRejectIntent | PointerMoveIntent | PointerClickIntent | PointerDoubleClickIntent | PointerDragToggleIntent | PointerScrollIntent | KeyPressIntent | TextInsertIntent | TextDictationIntent | NavNextIntent | NavPreviousIntent | NavSelectIntent | NavBackIntent | UiShowNumbersIntent | UiShowGridIntent | UiSelectTargetIntent | ModeSetIntent | InputPauseIntent | InputResumeIntent | ProfileSwitchIntent | CalibrationRequestIntent | CommandInvokeIntent;
