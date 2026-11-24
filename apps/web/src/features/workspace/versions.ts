export type DraftInput = {
  kind: "email" | "document" | "social";
  title: string;
  subject: string;
  recipient: string;
  body: string;
};
export type TaskVersion = Readonly<DraftInput & { revision: number; at: string }>;
export const draftLimits = Object.freeze({ title: 180, subject: 240, recipient: 254, body: 50000 });

export function validDraft(input: DraftInput): boolean {
  return (
    ["email", "document", "social"].includes(input.kind) &&
    Boolean(input.title.trim() && input.body.trim()) &&
    input.title.length <= draftLimits.title &&
    input.subject.length <= draftLimits.subject &&
    input.recipient.length <= draftLimits.recipient &&
    input.body.length <= draftLimits.body
  );
}

export function versionInput(version: DraftInput): DraftInput {
  return {
    kind: version.kind,
    title: version.title,
    subject: version.subject,
    recipient: version.recipient,
    body: version.body,
  };
}

export function sameDraft(a: DraftInput, b: DraftInput): boolean {
  return (
    a.kind === b.kind &&
    a.title === b.title &&
    a.subject === b.subject &&
    a.recipient === b.recipient &&
    a.body === b.body
  );
}

/** Kept independently of Undo snapshots, so a revision id is never reused after Undo. */
export function appendVersion(
  versions: readonly TaskVersion[],
  input: DraftInput,
  at: string,
): readonly TaskVersion[] {
  if (!validDraft(input)) throw new Error("Invalid draft version");
  const revision = versions.reduce((highest, item) => Math.max(highest, item.revision), 0) + 1;
  return Object.freeze([...versions, Object.freeze({ ...versionInput(input), revision, at })]);
}
