export type BlockKind = "paragraph" | "heading" | "list";
export type TextBlock = Readonly<{
  number: number;
  kind: BlockKind;
  start: number;
  end: number;
  text: string;
}>;
export type BlockOperation = "replace" | "insert" | "delete";
export type BlockDraft = Readonly<{
  selected: number;
  operation: BlockOperation;
  text: string;
  comparing: boolean;
}>;

export function hasBlockChange(text: string, draft: BlockDraft | undefined): boolean {
  if (!draft) return false;
  const block = splitBlocks(text)[draft.selected - 1];
  return Boolean(
    block &&
    (draft.operation === "delete" ||
      (draft.operation === "insert" ? draft.text.length > 0 : draft.text !== block.text)),
  );
}

/** Offsets refer to the original string; blank lines and line endings are never normalized. */
export function splitBlocks(text: string): TextBlock[] {
  const result: TextBlock[] = [];
  let current: { start: number; end: number; kind: BlockKind } | undefined;
  let fence: string | undefined;
  const finish = () => {
    if (current)
      result.push(
        Object.freeze({
          ...current,
          number: result.length + 1,
          text: text.slice(current.start, current.end),
        }),
      );
    current = undefined;
  };
  for (const match of text.matchAll(/[^\r\n]*(?:\r\n|\n|\r|$)/g)) {
    if (!match[0]) continue;
    const line = match[0].replace(/[\r\n]+$/, "");
    const start = match.index;
    const marker = /^\s{0,3}(`{3,}|~{3,})(.*)$/.exec(line);
    if (fence && current) {
      current.end = start + line.length;
      const closing = marker?.[1];
      if (
        closing &&
        closing[0] === fence[0] &&
        closing.length >= fence.length &&
        !marker?.[2]?.trim()
      ) {
        fence = undefined;
        finish();
      }
      continue;
    }
    if (!line.trim()) {
      finish();
      continue;
    }
    if (marker?.[1]) {
      finish();
      fence = marker[1];
      current = { start, end: start + line.length, kind: "paragraph" };
      continue;
    }
    const kind: BlockKind = /^\s{0,3}#{1,6}(?:[ \t]+|$)/.test(line)
      ? "heading"
      : /^\s*(?:[-*+]|\d+[.)])[ \t]+/.test(line)
        ? "list"
        : "paragraph";
    if (
      current &&
      kind === "paragraph" &&
      (current.kind === "paragraph" || (current.kind === "list" && /^\s{2,}\S/.test(line)))
    )
      current.end = start + line.length;
    else {
      finish();
      current = { start, end: start + line.length, kind };
    }
  }
  finish();
  return result;
}

/** Changes one numbered range, retaining all other characters exactly. */
export function applyBlockEdit(
  text: string,
  number: number,
  operation: BlockOperation,
  replacement: string,
): string | null {
  if (!Number.isInteger(number) || number < 1) return null;
  const block = splitBlocks(text)[number - 1];
  if (!block) return null;
  const before = text.slice(0, block.start);
  const after = text.slice(block.end);
  if (operation === "replace") return before + replacement + after;
  if (operation === "delete") return before + after;
  if (operation === "insert") {
    const newline = /\r\n|\r|\n/.exec(text)?.[0] ?? "\n";
    const extraBreak = after && !/^(?:\r\n|\r|\n)[ \t]*(?:\r\n|\r|\n)/.test(after) ? newline : "";
    return text.slice(0, block.end) + newline + newline + replacement + extraBreak + after;
  }
  return null;
}
