import assert from "node:assert/strict";
import { test } from "node:test";

// Evita el falso verde de un paquete sin pruebas: el módulo debe cargarse.
test("el paquete se importa", async () => {
  const mod = await import("./index.ts");
  assert.deepEqual(Object.keys(mod), []);
});
