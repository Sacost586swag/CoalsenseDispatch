"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { es } from "@coalsense/ui";
import { Button, TextField } from "@coalsense/ui/components";
import { useWorkspace, type Task } from "./state.tsx";
import {
  applyBlockEdit,
  hasBlockChange,
  splitBlocks,
  type BlockDraft,
  type BlockOperation,
} from "./blocks.ts";
import { draftLimits, sameDraft, type DraftInput } from "./versions.ts";
import { Area } from "./ui.tsx";
import { ReadAloud } from "./speech.tsx";

const PAUSED = "workspace.paused.reason";
const NO_CHANGE = "workspace.editor.no.change";
const LAST_BLOCK = "workspace.editor.delete.reason";
const PAGE_SIZE = 8; // [SUPUESTO] keep numbered choices manageable without hiding direct number access.
const operations = ["replace", "insert", "delete"] as const;
const operationCopy = {
  replace: "workspace.editor.replace",
  insert: "workspace.editor.insert",
  delete: "workspace.editor.delete",
} as const;
const blockCopy = {
  paragraph: "workspace.editor.kind.paragraph",
  heading: "workspace.editor.kind.heading",
  list: "workspace.editor.kind.list",
} as const;

function EditorHeading({ title }: { title: string }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (!document.activeElement?.closest("[data-cs-stop-bar]")) heading.current?.focus();
  }, []);
  return (
    <h3 ref={heading} tabIndex={-1}>
      {title}
    </h3>
  );
}

function Comparison({ before, after }: { before: ReactNode; after: ReactNode }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (!document.activeElement?.closest("[data-cs-stop-bar]")) heading.current?.focus();
  }, []);
  return (
    <div className="editor-comparison">
      <section>
        <h4 ref={heading} tabIndex={-1}>
          {es["workspace.editor.before"]}
        </h4>
        {before}
      </section>
      <section>
        <h4>{es["workspace.editor.after"]}</h4>
        {after}
      </section>
    </div>
  );
}

export function BlockEditor({ task, onDone }: { task: Task; onDone: () => void }) {
  const workspace = useWorkspace();
  const key = `${task.id}:${task.revision}`;
  const blocks = splitBlocks(task.body);
  const [draft, setDraft] = useState<BlockDraft>(
    () =>
      workspace.readBlockEditor(key) ?? {
        selected: 1,
        operation: "replace",
        text: blocks[0]?.text ?? "",
        comparing: false,
      },
  );
  const [jump, setJump] = useState(String(draft.selected));
  const [page, setPage] = useState(Math.floor((draft.selected - 1) / PAGE_SIZE));
  const [error, setError] = useState("");
  const selected = blocks[draft.selected - 1];
  const dirty = hasBlockChange(task.body, draft);
  const proposal = applyBlockEdit(task.body, draft.selected, draft.operation, draft.text);
  const afterText =
    draft.operation === "delete"
      ? es["workspace.editor.removed"]
      : draft.operation === "insert"
        ? `${selected?.text ?? ""}\n\n${draft.text}`
        : draft.text;
  function change(next: BlockDraft) {
    setDraft(next);
    workspace.writeBlockEditor(key, next);
    setError("");
  }
  function choose(number: number) {
    if (dirty) return;
    const block = blocks[number - 1];
    if (!Number.isInteger(number) || !block) {
      setError(es["workspace.editor.invalid"]);
      document.getElementById("block-number")?.focus();
      return;
    }
    change({ selected: number, operation: "replace", text: block.text, comparing: false });
    setJump(String(number));
    setPage(Math.floor((number - 1) / PAGE_SIZE));
  }
  function operation(next: BlockOperation) {
    change({
      ...draft,
      operation: next,
      text: next === "replace" ? (selected?.text ?? "") : "",
      comparing: false,
    });
  }
  function compare() {
    if (draft.operation !== "delete" && !draft.text.trim()) {
      setError(es["workspace.editor.required"]);
      return;
    }
    if (!proposal?.trim()) {
      setError(es["workspace.editor.delete.reason"]);
      return;
    }
    if (proposal.length > draftLimits.body) {
      setError(es["workspace.editor.limit"]);
      return;
    }
    change({ ...draft, comparing: true });
  }
  return (
    <div className="numbered-editor">
      <EditorHeading title={es["workspace.editor.blocks"]} />
      <p className="muted-copy">{es["workspace.editor.body"]}</p>
      {dirty && (
        <p id="block-selection-lock" className="local-note">
          {es["workspace.editor.pending"]}
        </p>
      )}
      <form
        className="editor-number-form"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          choose(Number(jump));
        }}
      >
        <TextField
          id="block-number"
          label={es["workspace.editor.jump"]}
          type="number"
          min={1}
          max={blocks.length}
          step={1}
          value={jump}
          onChange={(event) => setJump(event.target.value)}
          error={error === es["workspace.editor.invalid"] ? error : undefined}
        />
        <Button
          type="submit"
          disabled={dirty}
          aria-describedby={dirty ? "block-selection-lock" : undefined}
        >
          {es["workspace.editor.show"]}
        </Button>
      </form>
      <p className="muted-copy">
        {es["workspace.editor.range"]} {page * PAGE_SIZE + 1}–
        {Math.min((page + 1) * PAGE_SIZE, blocks.length)} / {blocks.length}
      </p>
      <ol className="numbered-blocks" start={page * PAGE_SIZE + 1}>
        {blocks.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE).map((block) => (
          <li key={block.number} className={block.number === draft.selected ? "is-selected" : ""}>
            <div className="block-toolbar">
              <span>{es[blockCopy[block.kind]]}</span>
              <Button
                aria-pressed={block.number === draft.selected}
                disabled={dirty && block.number !== draft.selected}
                aria-describedby={dirty ? "block-selection-lock" : undefined}
                onClick={() => {
                  if (block.number !== draft.selected) choose(block.number);
                }}
              >
                {es["workspace.editor.select"]} {block.number}
              </Button>
            </div>
            <div className="block-content" dir="auto">
              {block.text}
            </div>
          </li>
        ))}
      </ol>
      {blocks.length > PAGE_SIZE && (
        <div className="screen-actions">
          <Button disabled={page === 0} onClick={() => setPage(page - 1)}>
            {es["workspace.editor.previous"]}
          </Button>
          <Button
            disabled={(page + 1) * PAGE_SIZE >= blocks.length}
            onClick={() => setPage(page + 1)}
          >
            {es["workspace.editor.next"]}
          </Button>
        </div>
      )}
      {selected ? (
        <section className="block-workbench">
          <h4>
            {es["workspace.editor.block"]} {selected.number}
          </h4>
          {draft.comparing && <p className="muted-copy">{es["workspace.editor.read.after"]}</p>}
          <ReadAloud text={draft.comparing ? afterText : selected.text} />
          {draft.comparing ? (
            <>
              <Comparison
                before={
                  <div className="block-content" dir="auto">
                    {selected.text}
                  </div>
                }
                after={
                  <div className="block-content" dir="auto">
                    {afterText}
                  </div>
                }
              />
              <div className="screen-actions">
                <Button
                  variant="primary"
                  disabled={workspace.paused || workspace.copying}
                  disabledReason={workspace.paused ? PAUSED : undefined}
                  onClick={() => {
                    if (
                      !proposal ||
                      !workspace.updateTask(task.id, { ...task, body: proposal }, task.revision)
                    )
                      return;
                    workspace.writeBlockEditor(key, undefined);
                    onDone();
                  }}
                >
                  {es["workspace.editor.apply"]}
                </Button>
                <Button onClick={() => change({ ...draft, comparing: false })}>
                  {es["workspace.editor.revise"]}
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="screen-actions">
                {operations.map((item) => (
                  <Button
                    key={item}
                    aria-pressed={draft.operation === item}
                    disabled={
                      (item === "delete" && blocks.length <= 1) ||
                      (dirty && item !== draft.operation)
                    }
                    disabledReason={
                      item === "delete" && blocks.length <= 1 ? LAST_BLOCK : undefined
                    }
                    aria-describedby={dirty ? "block-selection-lock" : undefined}
                    onClick={() => {
                      if (item !== draft.operation) operation(item);
                    }}
                  >
                    {es[operationCopy[item]]}
                  </Button>
                ))}
              </div>
              {draft.operation !== "delete" && (
                <Area
                  id="block-text"
                  label={es["workspace.editor.text"]}
                  value={draft.text}
                  maxLength={draftLimits.body}
                  rows={7}
                  onChange={(event) =>
                    change({ ...draft, text: event.target.value, comparing: false })
                  }
                />
              )}
              <div className="screen-actions">
                <Button
                  variant="primary"
                  disabled={!dirty}
                  disabledReason={NO_CHANGE}
                  onClick={compare}
                >
                  {es["workspace.editor.compare"]}
                </Button>
              </div>
            </>
          )}
          {dirty && (
            <Button
              onClick={() =>
                change({
                  selected: draft.selected,
                  operation: "replace",
                  text: selected.text,
                  comparing: false,
                })
              }
            >
              {es["workspace.editor.discard"]}
            </Button>
          )}
        </section>
      ) : (
        <p>{es["workspace.editor.empty"]}</p>
      )}
      <p
        role="alert"
        className={
          error && error !== es["workspace.editor.invalid"]
            ? "workspace-notice"
            : "cs-visually-hidden"
        }
      >
        {error !== es["workspace.editor.invalid"] ? error : ""}
      </p>
      <div className="screen-actions">
        <Button onClick={onDone}>{es["workspace.editor.back"]}</Button>
      </div>
    </div>
  );
}

function VersionContent({ input }: { input: DraftInput }) {
  const kindCopy = {
    email: "workspace.task.email",
    document: "workspace.task.document",
    social: "workspace.task.social",
  } as const;
  return (
    <>
      <dl className="version-fields">
        <dt>{es["workspace.versions.type"]}</dt>
        <dd>{es[kindCopy[input.kind]]}</dd>
        <dt>{es["workspace.task.title.label"]}</dt>
        <dd>{input.title}</dd>
        <dt>{es["workspace.task.recipient"]}</dt>
        <dd>{input.recipient || es["workspace.review.unspecified"]}</dd>
        <dt>{es["workspace.task.subject"]}</dt>
        <dd>
          {input.subject ||
            (input.kind === "email" ? input.title : es["workspace.review.unspecified"])}
        </dd>
      </dl>
      <div className="block-content" dir="auto">
        {input.body}
      </div>
    </>
  );
}

export function VersionHistory({ task, onDone }: { task: Task; onDone: () => void }) {
  const workspace = useWorkspace();
  const versions = workspace.versionsFor(task.id);
  const [selected, setSelected] = useState<number | null>(null);
  const [number, setNumber] = useState(String(task.revision));
  const [page, setPage] = useState(0);
  const [error, setError] = useState(false);
  const snapshot = versions.find((item) => item.revision === selected);
  function choose(value: number) {
    if (!versions.some((item) => item.revision === value)) {
      setError(true);
      document.getElementById("version-number")?.focus();
      return;
    }
    setSelected(value);
    setNumber(String(value));
    setError(false);
  }
  return (
    <div className="version-history">
      <EditorHeading title={es["workspace.versions.title"]} />
      <p>{es["workspace.versions.body"]}</p>
      <p className="status-tag">
        {es["workspace.versions.current"]} {task.revision}
      </p>
      <form
        className="editor-number-form"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          choose(Number(number));
        }}
      >
        <TextField
          id="version-number"
          label={es["workspace.versions.number"]}
          type="number"
          min={1}
          max={versions.at(-1)?.revision ?? 1}
          step={1}
          value={number}
          onChange={(event) => setNumber(event.target.value)}
          error={error ? es["workspace.versions.not.found"] : undefined}
        />
        <Button type="submit">{es["workspace.versions.open"]}</Button>
      </form>
      <ol className="version-list">
        {[...versions]
          .reverse()
          .slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
          .map((item) => (
            <li key={item.revision}>
              <time dateTime={item.at}>
                {new Intl.DateTimeFormat("es-EC", {
                  dateStyle: "medium",
                  timeStyle: "short",
                }).format(new Date(item.at))}
              </time>
              <Button
                aria-pressed={selected === item.revision}
                onClick={() => choose(item.revision)}
              >
                {es["workspace.versions.show"]} {item.revision}
              </Button>
            </li>
          ))}
      </ol>
      {versions.length > PAGE_SIZE && (
        <div className="screen-actions">
          <Button disabled={page === 0} onClick={() => setPage(page - 1)}>
            {es["workspace.versions.next"]}
          </Button>
          <Button
            disabled={(page + 1) * PAGE_SIZE >= versions.length}
            onClick={() => setPage(page + 1)}
          >
            {es["workspace.versions.previous"]}
          </Button>
        </div>
      )}
      {snapshot && (
        <>
          <Comparison
            key={snapshot.revision}
            before={<VersionContent input={task} />}
            after={<VersionContent input={snapshot} />}
          />
          <div className="screen-actions">
            <Button
              variant="primary"
              disabled={workspace.paused || workspace.copying || sameDraft(task, snapshot)}
              disabledReason={workspace.paused ? PAUSED : NO_CHANGE}
              onClick={() => {
                if (workspace.restoreVersion(task.id, snapshot.revision, task.revision)) onDone();
              }}
            >
              {es["workspace.versions.use"]}
            </Button>
          </div>
        </>
      )}
      <div className="screen-actions">
        <Button onClick={onDone}>{es["workspace.editor.back"]}</Button>
      </div>
    </div>
  );
}
