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

function capture(extra: Record<string, unknown>, opts: { contentKeys?: string[] } = {}) {
  const lines: string[] = [];
  createLogger("probe", { ...opts, sink: (s) => lines.push(s) }).info("event.probe", extra);
  return { output: lines.join(""), record: JSON.parse(lines[0] ?? "{}") };
}

test("Map, Set, Symbol keys and values never leak", () => {
  const marker = randomUUID();
  const { output, record } = capture({
    map: new Map([[marker, marker]]),
    set: new Set([marker]),
    weak: new WeakMap(),
    [Symbol(marker)]: marker,
    sym: Symbol(marker),
    list: [new Map([[1, marker]]), new Set([marker]), Symbol(marker)],
  });
  assert.ok(!output.includes(marker));
  assert.equal(record.extra.map, "[omitido]");
  assert.equal(record.extra.set, "[omitido]");
  assert.equal(record.extra.sym, "[omitido]");
  assert.deepEqual(record.extra.list, ["[omitido]", "[omitido]", "[omitido]"]);
});

test("prototype toJSON, getters and accessor array items never run or leak", () => {
  const marker = randomUUID();
  let calls = 0;
  class Dictation {
    toJSON() {
      calls++;
      return { text: marker, other: marker };
    }
  }
  const withGetter = {
    get secret() {
      calls++;
      return marker;
    },
    ok: "kept",
  };
  const items = [1, 2];
  Object.defineProperty(items, 1, {
    get() {
      calls++;
      return marker;
    },
    enumerable: true,
  });
  const { output, record } = capture({ cls: new Dictation(), withGetter, items });
  assert.ok(!output.includes(marker));
  assert.equal(calls, 0);
  assert.equal(record.extra.cls, "[omitido]");
  assert.deepEqual(record.extra.withGetter, { secret: "[omitido]", ok: "kept" });
  assert.deepEqual(record.extra.items, [1, "[omitido]"]);
});

test("nested Error with cause keeps only type and id", () => {
  const marker = randomUUID();
  const inner = new TypeError(marker);
  const outer = new Error(`wrapped ${marker}`, { cause: inner });
  const noProto = Object.setPrototypeOf(new Error(marker), null) as Error;
  const { output, record } = capture({
    list: [outer],
    deep: { error: outer, none: noProto },
    app: new AppError("E_TEST", marker, false, [marker]),
  });
  assert.ok(!output.includes(marker));
  assert.equal(record.extra.list[0].type, "Error");
  assert.ok(!("cause" in record.extra.list[0]) && !("message" in record.extra.list[0]));
  assert.equal(record.extra.deep.error.type, "Error");
  assert.equal(record.extra.deep.none.type, "[omitido]");
  assert.equal(record.extra.app.code, "E_TEST");
});

test("file names are content under any key spelling", () => {
  const marker = randomUUID();
  const keys = ["file_name", "fileName", "file-name", "FILE_PATH", "filePath", "path", "x_path"];
  const { output, record } = capture({
    ...Object.fromEntries(keys.map((k) => [k, marker])),
    file_id: "f-1",
  });
  assert.ok(!output.includes(marker));
  assert.deepEqual(record.extra, { file_id: "f-1" });
});

test("custom content keys are normalized and empty keys ignored", () => {
  const marker = randomUUID();
  const { output, record } = capture(
    { secretnote: marker, ok: "kept" },
    { contentKeys: ["Secret_Note", ""] },
  );
  assert.ok(!output.includes(marker));
  assert.deepEqual(record.extra, { ok: "kept" });
});
