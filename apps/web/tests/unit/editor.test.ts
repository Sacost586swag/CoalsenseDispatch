import assert from "node:assert/strict";
import { test } from "node:test";
import { splitBlocks, applyBlockEdit } from "../../src/features/workspace/blocks.ts";
import {
  appendVersion,
  validDraft,
  versionInput,
  type DraftInput,
} from "../../src/features/workspace/versions.ts";

test("numbered paragraphs, headings and list items keep exact original offsets", () => {
  const text = "\r\n# Título\r\nUna línea\r\notra línea.\r\n\r\n- Uno\r\n  continúa\r\n- Dos\r\n";
  const blocks = splitBlocks(text);
  assert.deepEqual(
    blocks.map(({ number, kind, text }) => ({ number, kind, text })),
    [
      { number: 1, kind: "heading", text: "# Título" },
      { number: 2, kind: "paragraph", text: "Una línea\r\notra línea." },
      { number: 3, kind: "list", text: "- Uno\r\n  continúa" },
      { number: 4, kind: "list", text: "- Dos" },
    ],
  );
  for (const block of blocks) assert.equal(text.slice(block.start, block.end), block.text);
  assert.deepEqual(splitBlocks(" \n\t\r\n"), []);
});

test("fenced text stays in one block and Unicode offsets do not corrupt neighbouring text", () => {
  const text =
    "👩🏽‍💻 Mi nota\n\n```md\n# no es un encabezado\n\n- no es otra selección\n```\n\nÚltimo.";
  assert.equal(splitBlocks(text).length, 3);
  const changed = applyBlockEdit(text, 2, "replace", "Árbol");
  assert.equal(changed, "👩🏽‍💻 Mi nota\n\nÁrbol\n\nÚltimo.");
  assert.equal(applyBlockEdit(text, 1, "delete", ""), text.slice("👩🏽‍💻 Mi nota".length));
});

test("insertion preserves following blocks and rejects non-existent selections", () => {
  assert.equal(
    applyBlockEdit("# Uno\nDos\n\nTres", 1, "insert", "Nuevo"),
    "# Uno\n\nNuevo\n\nDos\n\nTres",
  );
  assert.equal(
    applyBlockEdit("Uno\r\n\r\nDos", 1, "insert", "Nuevo"),
    "Uno\r\n\r\nNuevo\r\n\r\nDos",
  );
  for (const selection of [0, -1, 1.5, Infinity, 99])
    assert.equal(applyBlockEdit("Uno", selection, "replace", "Dos"), null);
});

const input: DraftInput = {
  kind: "document",
  title: "Mi documento",
  subject: "",
  recipient: "",
  body: "Versión original.",
};
test("versions are immutable, preserve all fields and remain monotonic when restoring older text", () => {
  const first = appendVersion([], input, "2026-11-18T10:00:00Z");
  const second = appendVersion(
    first,
    { ...input, body: "Segunda versión." },
    "2026-11-18T10:01:00Z",
  );
  const original = first[0];
  assert.ok(original);
  const restored = appendVersion(second, versionInput(original), "2026-11-18T10:02:00Z");
  assert.deepEqual(
    restored.map((item) => item.revision),
    [1, 2, 3],
  );
  assert.equal(restored[2]?.body, input.body);
  assert.equal(second[1]?.body, "Segunda versión.");
  assert.ok(Object.isFrozen(restored) && Object.isFrozen(restored[0]));
  assert.equal(first.length, 1);
});

test("draft limits reject empty proposals and overlong combined edits without adding a version", () => {
  assert.equal(validDraft({ ...input, body: "Á".repeat(50000) }), true);
  for (const invalid of [
    { ...input, body: " \n" },
    { ...input, title: " " },
    { ...input, body: "Á".repeat(50001) },
    { ...input, title: "x".repeat(181) },
  ]) {
    assert.equal(validDraft(invalid), false);
    assert.throws(() => appendVersion([], invalid, "2026-11-18T10:00:00Z"));
  }
});
