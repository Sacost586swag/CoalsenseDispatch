import type {
  Intent,
  PointerClickIntent,
  CapabilityProfile,
  HeartbeatEvent,
  ToolManifest,
} from "../ts/src/types.ts";

declare const tool: ToolManifest;
const effect: "read" | "internal_write" | "external_effect" | undefined = tool.effect_class;
const inputSchema: Record<string, unknown> = tool.input_schema;
void effect;
void inputSchema;
// @ts-expect-error an undeclared effect is optional, never an automatic read
const automaticRead: "read" = tool.effect_class;
void automaticRead;

declare const intention: Intent;
if (intention.type === "pointer.click") {
  const click: PointerClickIntent = intention;
  const button: "left" | "right" | "middle" = click.payload.button;
  void button;
  // @ts-expect-error click payload never exposes dictation
  const text: unknown = intention.payload.text;
  void text;
}
if (intention.type === "approval.approve") {
  const pending: string = intention.pending_action_id;
  const confidence: number = intention.confidence;
  void pending;
  void confidence;
  // @ts-expect-error approval cannot promote itself above Alto
  const priority: "preemptive" = intention.priority;
  void priority;
}
if (intention.type === "control.stop") {
  // @ts-expect-error Alto has an empty payload
  intention.payload.button = "left";
}
declare const profile: CapabilityProfile;
// @ts-expect-error no clinical fields
const diagnosis: unknown = profile.diagnosis;
void diagnosis;
if (profile.declared_condition) {
  const category: "special" = profile.declared_condition.category;
  void category;
}

declare const heartbeat: HeartbeatEvent;
const event: "heartbeat" = heartbeat.event;
const reachable: boolean = heartbeat.state.stop_reachable;
void event;
void reachable;
// @ts-expect-error heartbeat must not expose sensor data
heartbeat.audio = "private audio";
// @ts-expect-error clinical fields are absent from the health snapshot
heartbeat.state.declared_condition = "private condition";
// @ts-expect-error the event is not a remote actuation command
heartbeat.command = "key.press";
