import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { inspect } from "node:util";
import { z } from "zod";
import {
  AppError,
  ConfigError,
  loadConfig,
  Secret,
  newId,
  monotonicNs,
  wallClockIso,
} from "../src/index.ts";

const schema = z.object({
  PORT: z.coerce.number().int().positive(),
  TOKEN: z
    .string()
    .min(8)
    .transform((value) => new Secret(value)),
});

test("configuración validada y secretos ocultos", () => {
  const env = { PORT: "8000", TOKEN: "fake-test-token" };
  const config = loadConfig(schema, env);
  assert.equal(config.PORT, 8000);
  assert.equal(config.TOKEN.getSecretValue(), env.TOKEN);
  for (const output of [
    String(config.TOKEN),
    JSON.stringify(config),
    inspect(config),
    inspect(config, { showHidden: true }),
  ])
    assert.ok(!output.includes(env.TOKEN));
  assert.equal(String(config.TOKEN), "***");
  assert.equal(JSON.stringify(config.TOKEN), '"***"');
  assert.equal(inspect(config.TOKEN), "***");
  const key = "COALSENSE_TEST_PORT";
  const old = process.env[key];
  try {
    process.env[key] = "8000";
    assert.equal(loadConfig(z.object({ [key]: z.coerce.number() }))[key], 8000);
  } finally {
    if (old === undefined) delete process.env.COALSENSE_TEST_PORT;
    else process.env[key] = old;
  }
});

test("errores de configuración no revelan valores", () => {
  for (const env of [
    { TOKEN: "fake-test-token" },
    { PORT: "8000", TOKEN: "bad" },
    { PORT: "invalid", TOKEN: "fake-test-token" },
  ]) {
    assert.throws(
      () => loadConfig(schema, env),
      (error) => {
        assert.ok(error instanceof ConfigError);
        assert.match(error.message, /configuración/);
        assert.ok(!inspect(error).includes(env.TOKEN));
        return true;
      },
    );
  }
  assert.throws(
    () =>
      loadConfig(
        z.object({
          TOKEN: z
            .string()
            .superRefine((value, ctx) => ctx.addIssue({ code: "custom", message: value })),
        }),
        { TOKEN: "fake-test-token" },
      ),
    (error) => {
      assert.ok(error instanceof ConfigError);
      assert.ok(!inspect(error).includes("fake-test-token"));
      return true;
    },
  );
});

test("error común coincide con el fixture compartido", () => {
  const golden = JSON.parse(
    readFileSync(
      new URL("../../common-py/tests/fixtures/error_golden.json", import.meta.url),
      "utf8",
    ),
  );
  const error = new AppError(
    golden.code,
    golden.message_es,
    golden.recoverable,
    golden.next_actions,
  );
  assert.deepEqual(error.toJSON(), golden);
  assert.deepEqual(JSON.parse(JSON.stringify(error)), golden);
});

test("10 000 UUIDv7 únicos y ordenados", () => {
  const start = Date.now();
  const ids = Array.from({ length: 10_000 }, () => newId());
  assert.equal(new Set(ids).size, 10_000);
  assert.deepEqual(ids, [...ids].sort());
  for (const id of ids)
    assert.match(id, /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  assert.ok(parseInt(ids.at(0)?.replaceAll("-", "").slice(0, 12) ?? "", 16) >= start);
});

test("UUIDv7 con reloj detenido y en retroceso", (t) => {
  let now = 2_000_000_000_000;
  t.mock.method(Date, "now", () => now);
  const ids = Array.from({ length: 10_000 }, () => newId());
  now -= 1000;
  ids.push(newId());
  assert.deepEqual(ids, [...new Set(ids)].sort());
});

test("tiempos monotónicos y UTC", () => {
  const first = monotonicNs();
  assert.equal(typeof first, "bigint");
  assert.ok(monotonicNs() >= first);
  const value = wallClockIso();
  assert.match(value, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/);
  assert.ok(Number.isFinite(Date.parse(value)));
});
