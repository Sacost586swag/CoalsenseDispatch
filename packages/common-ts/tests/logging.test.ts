import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { test } from "node:test";
import { AppError, createLogger } from "../src/index.ts";

test("recursive content scrubbing and boundary", () => {
  const marker = randomUUID();
  const lines: string[] = [];
  const log = createLogger("scrub", { contentKeys: ["private"], sink: (s) => lines.push(s) });
  const data = Object.fromEntries(
    [
      "text",
      "body",
      "dictation",
      "profile",
      "filename",
      "recipient",
      "prompt",
      "completion",
      "email_body",
      "userText",
      "PRIVATE",
      "audio",
      "video",
      "landmarks",
    ].map((key) => [key, marker]),
  );
  log.info("auth.code_sent", {
    nested: [data],
    unknown: marker.repeat(3),
    short: "x".repeat(64),
    id: "request-1",
  });
  assert.ok(!lines.join("").includes(marker));
  const record = JSON.parse(lines[0] ?? "");
  assert.deepEqual(record.extra.nested, [{}]);
  assert.equal(record.extra.unknown, "[omitido]");
  assert.equal(record.extra.short.length, 64);
  assert.equal(record.extra.id, "request-1");
  assert.equal(data.text, marker);
});

test("exceptions, invalid messages, cycles and objects never stringify content", () => {
  const marker = randomUUID();
  const lines: string[] = [];
  const log = createLogger("errors", { sink: (s) => lines.push(s) });
  const cycle: unknown[] = [];
  cycle.push(cycle);
  log.error("event.failed", {
    error: new Error(marker),
    app: new AppError("E_TEST", marker, false, [marker]),
    cycle,
    object: {
      toJSON() {
        throw new Error(marker);
      },
    },
  });
  log.info(`invalid message ${marker}`);
  assert.ok(!lines.join("").includes(marker));
  const record = JSON.parse(lines[0] ?? "");
  assert.equal(record.extra.error.type, "Error");
  assert.ok(record.extra.error.id);
  assert.equal(record.extra.app.code, "E_TEST");
  assert.deepEqual(record.extra.cycle, ["[omitido]"]);
  assert.equal(JSON.parse(lines[1] ?? "").message, "[omitido]");
});

test("level filtering", () => {
  const lines: string[] = [];
  const log = createLogger("levels", { level: "WARNING", sink: (s) => lines.push(s) });
  log.debug("event.hidden");
  log.info("event.hidden");
  log.warn("event.visible");
  assert.equal(lines.length, 1);
  assert.equal(JSON.parse(lines[0] ?? "").level, "WARNING");
});
