"use client";

import { useEffect, useRef, useState } from "react";
import { es } from "@coalsense/ui";
import { Button, Dialog, TextField } from "@coalsense/ui/components";
import { useWorkspace, type InputMode, type Task } from "./state.tsx";
import { ReadAloud, useLocalSpeech } from "./speech.tsx";
import { BlockEditor, VersionHistory } from "./Editor.tsx";
import { draftLimits } from "./versions.ts";
import { Area, Icon, PageHeading, RouteButton, VoiceCue, type IconName } from "./ui.tsx";

const kinds = ["email", "document", "social"] as const;
const SEND_REASON = "workspace.review.send.reason";
const AUDIO_REASON = "workspace.audio.unavailable";
const EXPORT_REASON = "workspace.achievements.export.empty";
const NEW_EDITOR_KEY = "new";
const PAUSED_REASON = "workspace.paused.reason";
const PENDING_REASON = "workspace.editor.pending";
const taskCopy = {
  email: {
    title: "workspace.task.email",
    body: "workspace.task.email.body",
    category: "workspace.task.email.category",
    start: "workspace.task.email.start",
    icon: "mail",
  },
  document: {
    title: "workspace.task.document",
    body: "workspace.task.document.body",
    category: "workspace.task.document.category",
    start: "workspace.task.document.start",
    icon: "document",
  },
  social: {
    title: "workspace.task.social",
    body: "workspace.task.social.body",
    category: "workspace.task.social.category",
    start: "workspace.task.social.start",
    icon: "social",
  },
} as const;
const modes: Array<{
  mode: InputMode;
  title: keyof typeof es;
  body: keyof typeof es;
  icon: IconName;
}> = [
  { mode: "voice", title: "workspace.voice", body: "workspace.welcome.voice.body", icon: "voice" },
  { mode: "head", title: "workspace.head", body: "workspace.welcome.head.body", icon: "head" },
  { mode: "gaze", title: "workspace.gaze", body: "workspace.welcome.gaze.body", icon: "eye" },
];

export function WelcomeScreen() {
  const workspace = useWorkspace();
  return (
    <div className="welcome-surface">
      <div className="onboarding-progress" aria-label={es["workspace.steps.label"]}>
        <strong>{es["workspace.step.control"]}</strong>
        <span>{es["workspace.step.setup"]}</span>
        <span>{es["workspace.step.practice"]}</span>
      </div>
      <PageHeading title={es["workspace.welcome.title"]} body={es["workspace.welcome.body"]} />
      <section className="mode-grid" aria-label={es["workspace.welcome.selection"]}>
        {modes.map((item) => (
          <Button
            key={item.mode}
            className={`mode-card ${workspace.data.mode === item.mode ? "is-selected" : ""}`}
            aria-pressed={workspace.data.mode === item.mode}
            onClick={() => workspace.changeMode(item.mode)}
          >
            <span className="mode-card-top">
              <span className="icon-tile">
                <Icon variant={item.icon} />
              </span>
              <span className="status-tag">
                {
                  es[
                    workspace.data.mode === item.mode
                      ? "workspace.welcome.selected"
                      : "workspace.not.connected"
                  ]
                }
              </span>
            </span>
            <span className="mode-title">{es[item.title]}</span>
            <span className="mode-description">{es[item.body]}</span>
            <span className="mode-card-bottom">
              <span>
                {es["workspace.welcome.choose"]} {es[item.title]}
              </span>
              <Icon variant={workspace.data.mode === item.mode ? "check" : "arrow"} />
            </span>
          </Button>
        ))}
      </section>
      <div className="keyboard-choice">
        <Button
          aria-pressed={workspace.data.mode === "keyboard"}
          onClick={() => workspace.changeMode("keyboard")}
        >
          <Icon variant="keyboard" />
          {es["workspace.keyboard"]}
        </Button>
        <p>{es["workspace.welcome.keyboard.body"]}</p>
      </div>
      <section className="privacy-strip">
        <Icon variant="shield" />
        <div>
          <h2>{es["workspace.welcome.safe"]}</h2>
          <p>{es["workspace.welcome.safe.body"]}</p>
        </div>
      </section>
      <p className="muted-copy">{es["workspace.welcome.note"]}</p>
      <div className="screen-actions">
        <RouteButton href="/calibracion" primary>
          {es["workspace.welcome.start"]}
          <Icon variant="arrow" />
        </RouteButton>
        <RouteButton href="/inicio">{es["workspace.recovery.home"]}</RouteButton>
      </div>
    </div>
  );
}

export function CalibrationScreen() {
  const workspace = useWorkspace();
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const request = useRef(0);
  const [active, setActive] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  function stopCamera() {
    request.current += 1;
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
    if (video.current) video.current.srcObject = null;
    setActive(false);
    setBusy(false);
  }
  useEffect(() => workspace.registerStop(stopCamera), [workspace.registerStop]);
  useEffect(
    () => () => {
      request.current += 1;
      stream.current?.getTracks().forEach((track) => track.stop());
    },
    [],
  );
  useEffect(() => {
    if (workspace.paused) {
      request.current += 1;
      stream.current?.getTracks().forEach((track) => track.stop());
      stream.current = null;
      setActive(false);
      setBusy(false);
    }
  }, [workspace.paused]);
  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMessage(es["workspace.calibration.camera.unsupported"]);
      return;
    }
    const id = ++request.current;
    setBusy(true);
    setMessage("");
    try {
      const result = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (id !== request.current) {
        result.getTracks().forEach((track) => track.stop());
        return;
      }
      stream.current = result;
      result.getVideoTracks().forEach((track) => {
        track.onended = () => {
          if (stream.current === result) {
            stopCamera();
            setMessage(es["workspace.calibration.camera.denied"]);
          }
        };
      });
      if (video.current) video.current.srcObject = result;
      setActive(true);
    } catch {
      if (id === request.current) setMessage(es["workspace.calibration.camera.denied"]);
    } finally {
      if (id === request.current) setBusy(false);
    }
  }
  const steps = [
    ["workspace.calibration.brow", "workspace.calibration.step3.body"],
    ["workspace.calibration.mouth", "workspace.calibration.step3.body"],
    ["workspace.calibration.head", "workspace.calibration.step3.body"],
  ] as const;
  return (
    <>
      <PageHeading
        title={es["workspace.calibration.title"]}
        body={es["workspace.calibration.body"]}
      />
      <div className="calibration-layout">
        <section className="camera-panel" aria-label={es["workspace.calibration.preview"]}>
          <div className="camera-toolbar">
            <strong>{es["workspace.calibration.preview"]}</strong>
            <span className="status-tag">
              {es[active ? "workspace.calibration.local" : "workspace.home.off"]}
            </span>
          </div>
          <div className="camera-view">
            <video
              ref={video}
              autoPlay
              playsInline
              muted
              aria-label={es["workspace.calibration.preview"]}
            />
            {!active && (
              <div className="camera-placeholder">
                <Icon variant="head" />
                <p>{es["workspace.calibration.no.camera"]}</p>
              </div>
            )}
            {active && <div className="camera-frame" aria-hidden="true" />}
          </div>
          <p className="camera-caption" role="status">
            {
              es[
                active ? "workspace.calibration.camera.active" : "workspace.calibration.local.body"
              ]
            }
          </p>
          <div className="camera-actions">
            {active ? (
              <Button
                onClick={() => {
                  stopCamera();
                  setMessage(es["workspace.calibration.camera.stopped"]);
                }}
              >
                {es["workspace.calibration.camera.stop"]}
              </Button>
            ) : (
              <Button
                variant="primary"
                loading={busy}
                disabled={workspace.paused}
                onClick={() => void startCamera()}
              >
                {es["workspace.calibration.camera.start"]}
              </Button>
            )}
          </div>
        </section>
        <aside className="calibration-steps">
          <ol>
            {steps.map(([title, body], index) => (
              <li key={title}>
                <span className="step-number">{index + 1}</span>
                <div>
                  <h2>{es[title]}</h2>
                  <p>{es[body]}</p>
                  <div className="gesture-sensitivity">
                    <span>{es["workspace.calibration.sensitivity"]}</span>
                    <strong>{es["workspace.calibration.not.configured"]}</strong>
                  </div>
                  <div className="gesture-action">
                    <Button disabled>
                      {es["workspace.calibration.try"]} {es[title]}
                    </Button>
                    <span className="status-tag">{es["workspace.calibration.pending"]}</span>
                  </div>
                </div>
              </li>
            ))}
          </ol>
          <div className="local-note">
            <Icon variant="shield" />
            <p>{es["workspace.calibration.local.body"]}</p>
          </div>
        </aside>
      </div>
      {message && (
        <p className="workspace-notice" role="status">
          {message}
        </p>
      )}
      {workspace.data.mode === "voice" && (
        <p className="workspace-notice">{es["workspace.calibration.voice.note"]}</p>
      )}
      <div className="screen-actions">
        <RouteButton href="/primera-tarea" primary>
          {es["workspace.calibration.practice"]}
          <Icon variant="arrow" />
        </RouteButton>
        <RouteButton href="/bienvenida">{es["workspace.back"]}</RouteButton>
      </div>
    </>
  );
}

export function PracticeScreen() {
  const workspace = useWorkspace();
  const [note, setNote] = useState(workspace.data.practice);
  const [saved, setSaved] = useState(Boolean(workspace.data.practice));
  const [error, setError] = useState(false);
  return (
    <div className="practice-layout">
      <div>
        <PageHeading title={es["workspace.practice.title"]} body={es["workspace.practice.body"]} />
        <ol className="practice-steps">
          <li>
            <Icon variant="check" />
            {es["workspace.step.control"]}
          </li>
          <li>
            <Icon variant="check" />
            {es["workspace.step.setup"]}
          </li>
          <li className="is-current">
            <Icon variant="document" />
            {es["workspace.step.practice"]}
          </li>
        </ol>
        <p className="local-note">{es["workspace.memory.note"]}</p>
      </div>
      <section className="practice-card">
        <span className="status-tag">{es["workspace.practice.step"]}</span>
        {saved && Boolean(workspace.data.practice) ? (
          <div className="practice-success">
            <Icon variant="check" />
            <h2>{es["workspace.practice.success"]}</h2>
            <blockquote>{workspace.data.practice}</blockquote>
            <RouteButton href="/inicio" primary>
              {es["workspace.practice.to.home"]}
              <Icon variant="arrow" />
            </RouteButton>
          </div>
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (workspace.paused || workspace.copying) return;
              if (!note.trim()) {
                setError(true);
                return;
              }
              setSaved(workspace.savePractice(note.trim()));
            }}
          >
            <Area
              id="practice-note"
              label={es["workspace.practice.prompt"]}
              placeholder={es["workspace.practice.placeholder"]}
              value={note}
              onChange={(event) => {
                setNote(event.target.value);
                setError(false);
              }}
              rows={7}
              maxLength={10000}
            />
            {error && <p role="alert">{es["workspace.task.required"]}</p>}
            <Button
              type="submit"
              variant="primary"
              disabled={workspace.paused || workspace.copying}
              disabledReason={workspace.paused ? PAUSED_REASON : undefined}
            >
              {es["workspace.practice.action"]}
            </Button>
          </form>
        )}
      </section>
    </div>
  );
}

export function HomeScreen() {
  const workspace = useWorkspace();
  return (
    <>
      <section className="home-welcome">
        <PageHeading title={es["workspace.home.title"]} body={es["workspace.home.body"]} />
        <div className="system-panel">
          <div className="system-panel-title">
            <strong>{es["workspace.home.system"]}</strong>
            <span className="status-tag">{es["workspace.local"]}</span>
          </div>
          <div className="sensor-grid">
            {["workspace.home.microphone", "workspace.home.camera", "workspace.home.external"].map(
              (label) => (
                <div key={label}>
                  <span>{es[label as keyof typeof es]}</span>
                  <strong>
                    {
                      es[
                        label === "workspace.home.external"
                          ? "workspace.not.connected"
                          : "workspace.home.off"
                      ]
                    }
                  </strong>
                </div>
              ),
            )}
          </div>
          <p>{es["workspace.home.manual"]}</p>
        </div>
      </section>
      <div className="home-columns">
        <section>
          <div className="section-title">
            <h2>{es["workspace.home.tasks"]}</h2>
            <span className="status-tag">{es["workspace.home.available"]}</span>
          </div>
          <p className="section-intro">{es["workspace.home.tasks.body"]}</p>
          <div className="task-options">
            {kinds.map((kind) => {
              const copy = taskCopy[kind];
              return (
                <article className="task-option" key={kind}>
                  <div className="task-option-content">
                    <span className={`category-tag category-${kind}`}>
                      <Icon variant={copy.icon} />
                      {es[copy.category]}
                    </span>
                    <h3>{es[copy.title]}</h3>
                    <p>{es[copy.body]}</p>
                    <span className="task-local-note">
                      <Icon variant="shield" />
                      {es["workspace.task.no.external"]}
                    </span>
                  </div>
                  <RouteButton
                    href="/tareas/nueva"
                    primary
                    onNavigate={() => workspace.setNewKind(kind)}
                  >
                    <span>{es[copy.start]}</span>
                    <VoiceCue>{es[copy.start]}</VoiceCue>
                  </RouteButton>
                </article>
              );
            })}
          </div>
          <div className="custom-task">
            <Icon variant="document" />
            <div>
              <h3>{es["workspace.home.custom"]}</h3>
              <p>{es["workspace.home.custom.body"]}</p>
            </div>
            <RouteButton href="/tareas/nueva" onNavigate={() => workspace.setNewKind("document")}>
              {es["workspace.home.custom.action"]}
            </RouteButton>
          </div>
        </section>
        <aside className="home-summary">
          <h2>{es["workspace.home.week"]}</h2>
          <section className="summary-card">
            <Icon variant="check" />
            <h3>{es["workspace.home.completed"]}</h3>
            <strong className="summary-number">{workspace.data.achievements.length}</strong>
            <p>{es["workspace.achievements.local"]}</p>
          </section>
          <section className="summary-card">
            <Icon variant="clock" />
            <h3>{es["workspace.home.approvals"]}</h3>
            <strong className="summary-number">
              {workspace.data.tasks.filter((task) => task.status === "review").length}
            </strong>
            <p>{es["workspace.review.safeguard"]}</p>
          </section>
          <section className="summary-card">
            <h3>{es["workspace.home.income"]}</h3>
            <p>{es["workspace.home.no.income"]}</p>
          </section>
          <section className="pace-note">
            <h3>{es["workspace.home.goal"]}</h3>
            <p>{es["workspace.home.goal.body"]}</p>
          </section>
          <RouteButton href="/tareas">{es["workspace.home.history"]}</RouteButton>
        </aside>
      </div>
    </>
  );
}

function TaskFields({
  initial,
  draftKey,
  activeKind,
  onSave,
  submitLabel,
}: {
  initial: Pick<Task, "title" | "body" | "recipient" | "subject" | "kind">;
  draftKey: string;
  activeKind?: Task["kind"];
  onSave: (input: typeof initial) => boolean;
  submitLabel: string;
}) {
  const workspace = useWorkspace();
  const [values, setValues] = useState(() => workspace.readEditor(draftKey) ?? initial);
  const [error, setError] = useState(false);
  function change(key: keyof typeof initial, value: string) {
    const next = { ...values, [key]: value };
    setValues(next);
    workspace.writeEditor(draftKey, next);
    setError(false);
  }
  return (
    <form
      className="task-form"
      onSubmit={(event) => {
        event.preventDefault();
        if (workspace.paused || workspace.copying) return;
        if (!values.title.trim() || !values.body.trim()) {
          setError(true);
          event.currentTarget
            .querySelector<HTMLElement>(!values.title.trim() ? "#task-title" : "#task-notes")
            ?.focus();
          return;
        }
        if (onSave({ ...values, kind: activeKind ?? values.kind })) workspace.clearEditor(draftKey);
      }}
    >
      <TextField
        id="task-title"
        label={es["workspace.task.title.label"]}
        value={values.title}
        maxLength={draftLimits.title}
        onChange={(event) => change("title", event.target.value)}
        error={error && !values.title.trim() ? es["workspace.task.required"] : undefined}
      />
      {(activeKind ?? values.kind) === "email" && (
        <div className="form-row">
          <TextField
            id="task-recipient"
            label={es["workspace.task.recipient"]}
            type="email"
            value={values.recipient}
            maxLength={draftLimits.recipient}
            onChange={(event) => change("recipient", event.target.value)}
          />
          <TextField
            id="task-subject"
            label={es["workspace.task.subject"]}
            value={values.subject}
            maxLength={draftLimits.subject}
            onChange={(event) => change("subject", event.target.value)}
          />
        </div>
      )}
      <Area
        id="task-notes"
        label={es["workspace.task.notes"]}
        hint={es["workspace.task.notes.hint"]}
        error={error && !values.body.trim() ? es["workspace.task.required"] : undefined}
        value={values.body}
        onChange={(event) => change("body", event.target.value)}
        rows={10}
        maxLength={draftLimits.body}
      />
      <div className="screen-actions">
        <Button
          type="submit"
          variant="primary"
          disabled={workspace.paused || workspace.copying}
          disabledReason={workspace.paused ? PAUSED_REASON : undefined}
        >
          {submitLabel}
          <Icon variant="arrow" />
        </Button>
      </div>
    </form>
  );
}

export function NewTaskScreen() {
  const workspace = useWorkspace();
  const kind = workspace.newKind;
  return (
    <>
      <PageHeading title={es["workspace.task.new.title"]} body={es["workspace.task.new.body"]} />
      <div className="task-kind-row">
        {kinds.map((item) => (
          <Button
            key={item}
            aria-pressed={kind === item}
            onClick={() => workspace.setNewKind(item)}
          >
            <Icon variant={taskCopy[item].icon} />
            {es[taskCopy[item].title]}
          </Button>
        ))}
      </div>
      <section className="editor-panel">
        <TaskFields
          draftKey={NEW_EDITOR_KEY}
          activeKind={kind}
          initial={{
            kind,
            title: "",
            subject: "",
            recipient: "",
            body: workspace.data.practice,
          }}
          submitLabel={es["workspace.task.prepare"]}
          onSave={(input) => {
            const id = workspace.createTask(input);
            if (!id) return false;
            workspace.navigate(`/tareas/${id}`);
            return true;
          }}
        />
      </section>
      <p className="muted-copy">{es["workspace.memory.note"]}</p>
    </>
  );
}

export function TaskListScreen() {
  const workspace = useWorkspace();
  return (
    <>
      <PageHeading title={es["workspace.task.list.title"]} body={es["workspace.task.list.body"]} />
      {workspace.data.tasks.length ? (
        <div className="task-list">
          {workspace.data.tasks.map((task, index) => (
            <article key={task.id} className="task-row">
              <span className="icon-tile">
                <Icon variant={taskCopy[task.kind].icon} />
              </span>
              <div>
                <span className="status-tag">
                  {
                    es[
                      task.status === "copied"
                        ? "workspace.task.completed.status"
                        : task.status === "review"
                          ? "workspace.task.review.status"
                          : "workspace.task.local.status"
                    ]
                  }
                </span>
                <h2>{task.title}</h2>
                <p>{es[taskCopy[task.kind].title]}</p>
              </div>
              <RouteButton href={`/tareas/${task.id}`}>
                {es["workspace.task.open"]} {index + 1}
                <Icon variant="arrow" />
              </RouteButton>
            </article>
          ))}
        </div>
      ) : (
        <EmptyTasks />
      )}
      <div className="screen-actions">
        <RouteButton href="/tareas/nueva" primary>
          {es["workspace.achievements.start"]}
        </RouteButton>
      </div>
    </>
  );
}

function EmptyTasks({ missing = false }: { missing?: boolean }) {
  return (
    <section className="empty-panel">
      <Icon variant="document" />
      <h2>{es[missing ? "workspace.task.not.found" : "workspace.task.empty.title"]}</h2>
      <p>{es[missing ? "workspace.task.not.found.body" : "workspace.task.empty.body"]}</p>
      <RouteButton href="/inicio">{es["workspace.task.empty.action"]}</RouteButton>
    </section>
  );
}

export function TaskScreen({
  id,
  initialEditing = false,
}: {
  id: string;
  initialEditing?: boolean;
}) {
  const workspace = useWorkspace();
  const task = workspace.data.tasks.find((item) => item.id === id);
  const [mode, setMode] = useState<"preview" | "edit" | "blocks" | "versions">(
    initialEditing ? (workspace.pendingEdit(id) === "blocks" ? "blocks" : "edit") : "preview",
  );
  const panelTitle = useRef<HTMLHeadingElement>(null);
  const leftPreview = useRef(false);
  useEffect(() => {
    if (mode !== "preview") leftPreview.current = true;
    else if (leftPreview.current) {
      if (!document.activeElement?.closest("[data-cs-stop-bar]")) panelTitle.current?.focus();
      leftPreview.current = false;
    }
  }, [mode]);
  if (!task)
    return (
      <>
        <PageHeading title={es["workspace.nav.tasks"]} />
        <EmptyTasks missing />
      </>
    );
  const steps = [
    "workspace.task.step.choose",
    "workspace.task.step.draft",
    "workspace.task.step.review",
    "workspace.task.step.external",
  ] as const;
  const pending = workspace.pendingEdit(id);
  const hasWholeEdit = pending === "whole";
  const hasBlockEdit = pending === "blocks";
  return (
    <>
      <PageHeading
        title={es["workspace.task.progress.title"]}
        body={es["workspace.task.progress.body"]}
      />
      <div className="work-layout">
        <aside className="microsteps">
          <h2>{es["workspace.task.steps"]}</h2>
          <ol>
            {steps.map((step, index) => (
              <li
                className={index === 2 && task.status !== "copied" ? "is-current" : ""}
                key={step}
              >
                <span className="step-number">
                  {index < 2 || (index === 2 && task.status === "copied") ? (
                    <Icon variant="check" />
                  ) : (
                    index + 1
                  )}
                </span>
                <div>
                  <h3>{es[step]}</h3>
                  <span>
                    {
                      es[
                        index < 2 || (index === 2 && task.status === "copied")
                          ? "workspace.task.done"
                          : index === 2
                            ? "workspace.task.current"
                            : "workspace.task.pending"
                      ]
                    }
                  </span>
                </div>
              </li>
            ))}
          </ol>
          <p className="local-note">
            <Icon variant="shield" />
            {es["workspace.review.safeguard"]}
          </p>
        </aside>
        <section className="draft-panel">
          <div className="draft-toolbar">
            <h2 ref={panelTitle} tabIndex={-1}>
              {task.title}
            </h2>
            <span className="status-tag">
              {es["workspace.versions.current"]} {task.revision}
            </span>
            <span className="status-tag">
              {
                es[
                  task.status === "copied"
                    ? "workspace.task.completed.status"
                    : "workspace.task.local.status"
                ]
              }
            </span>
          </div>
          {mode === "blocks" ? (
            <BlockEditor key={task.revision} task={task} onDone={() => setMode("preview")} />
          ) : mode === "versions" ? (
            <VersionHistory key={task.revision} task={task} onDone={() => setMode("preview")} />
          ) : mode === "edit" ? (
            <>
              <TaskFields
                key={task.revision}
                draftKey={`${task.id}:${task.revision}`}
                initial={task}
                submitLabel={es["workspace.task.save"]}
                onSave={(input) => {
                  if (!workspace.updateTask(id, input, task.revision)) return false;
                  setMode("preview");
                  return true;
                }}
              />
              <div className="screen-actions">
                <Button onClick={() => setMode("preview")}>{es["workspace.editor.back"]}</Button>
              </div>
            </>
          ) : (
            <>
              <TaskPreview task={task} />
              <ReadAloud text={task.body} />
              <div className="screen-actions">
                <RouteButton
                  href={`/tareas/${id}/revision`}
                  primary
                  disabled={hasWholeEdit || hasBlockEdit}
                  disabledReason={PENDING_REASON}
                >
                  {es["workspace.task.review"]}
                  <Icon variant="arrow" />
                </RouteButton>
                <Button
                  disabled={hasBlockEdit || workspace.copying}
                  disabledReason={PENDING_REASON}
                  onClick={() => setMode("edit")}
                >
                  {es["workspace.task.edit"]}
                </Button>
                <Button
                  disabled={hasWholeEdit || workspace.copying}
                  disabledReason={PENDING_REASON}
                  onClick={() => setMode("blocks")}
                >
                  {es["workspace.editor.blocks"]}
                </Button>
                <Button
                  disabled={hasBlockEdit || hasWholeEdit || workspace.copying}
                  disabledReason={PENDING_REASON}
                  onClick={() => setMode("versions")}
                >
                  {es["workspace.versions.button"]}
                </Button>
              </div>
              {(hasBlockEdit || hasWholeEdit) && (
                <div className="pending-editor">
                  <p>{es["workspace.editor.pending"]}</p>
                  <Button onClick={() => workspace.discardEdits(id)}>
                    {es["workspace.editor.discard"]}
                  </Button>
                </div>
              )}
            </>
          )}
        </section>
        <aside className="task-activity">
          <section>
            <h2>{es["workspace.task.activity"]}</h2>
            <p>{es["workspace.task.activity.body"]}</p>
            <div className="activity-item">
              <time dateTime={task.createdAt}>
                {new Intl.DateTimeFormat("es-EC", { hour: "2-digit", minute: "2-digit" }).format(
                  new Date(task.createdAt),
                )}
              </time>
              <h3>{es["workspace.task.activity.created"]}</h3>
            </div>
            {task.updatedAt && (
              <div className="activity-item">
                <time dateTime={task.updatedAt}>
                  {new Intl.DateTimeFormat("es-EC", { hour: "2-digit", minute: "2-digit" }).format(
                    new Date(task.updatedAt),
                  )}
                </time>
                <h3>{es["workspace.task.activity.updated"]}</h3>
              </div>
            )}
            <div className="activity-item is-waiting">
              <h3>
                {
                  es[
                    task.status === "copied"
                      ? "workspace.task.completed.status"
                      : "workspace.task.activity.waiting"
                  ]
                }
              </h3>
              <p>
                {
                  es[
                    task.status === "copied"
                      ? "workspace.achievements.local"
                      : "workspace.task.activity.waiting.body"
                  ]
                }
              </p>
            </div>
          </section>
          <section className="pace-note">
            <h2>{es["workspace.home.goal"]}</h2>
            <p>{es["workspace.home.goal.body"]}</p>
            <Button onClick={workspace.stop}>{es["workspace.pause"]}</Button>
          </section>
        </aside>
      </div>
    </>
  );
}

function TaskPreview({ task }: { task: Task }) {
  return (
    <>
      {task.kind === "email" && (
        <dl className="message-metadata">
          <div>
            <dt>{es["workspace.task.recipient"]}</dt>
            <dd>{task.recipient || es["workspace.review.unspecified"]}</dd>
          </div>
          <div>
            <dt>{es["workspace.task.subject"]}</dt>
            <dd>{task.subject || task.title}</dd>
          </div>
        </dl>
      )}
      <div className="document-preview">{task.body}</div>
    </>
  );
}

export function ReviewScreen({ id }: { id: string }) {
  const workspace = useWorkspace();
  const reviewGeneration = useRef(0);
  useEffect(
    () => () => {
      reviewGeneration.current += 1;
    },
    [id],
  );
  const task = workspace.data.tasks.find((item) => item.id === id);
  if (!task)
    return (
      <>
        <PageHeading title={es["workspace.review.title"]} />
        <EmptyTasks missing />
      </>
    );
  const pending = Boolean(workspace.pendingEdit(id));
  return (
    <>
      <PageHeading title={es["workspace.review.title"]} body={es["workspace.review.body"]} />
      {pending && (
        <div className="workspace-notice">
          <p>{es["workspace.editor.pending"]}</p>
          <RouteButton href={`/tareas/${id}`}>{es["workspace.editor.back"]}</RouteButton>
        </div>
      )}
      <section className="approval-warning">
        <span className="warning-icon">
          <Icon variant="shield" />
        </span>
        <div>
          <h2>{es["workspace.review.warning"]}</h2>
          <p>{es["workspace.review.warning.body"]}</p>
          <p>
            <strong>{es["workspace.review.local.warning"]}</strong>
          </p>
        </div>
      </section>
      <div className="approval-layout">
        <section className="approval-preview">
          <div className="draft-toolbar">
            <h2>
              <Icon variant={taskCopy[task.kind].icon} />
              {es["workspace.review.preview"]}
            </h2>
            <Button
              disabled={workspace.copying}
              onClick={() => workspace.navigate(`/tareas/${id}?editar=1`)}
            >
              {es["workspace.review.open.editor"]}
            </Button>
          </div>
          <TaskPreview task={task} />
          <p className="muted-copy">
            {es["workspace.versions.current"]} {task.revision}
          </p>
          <ReadAloud text={task.body} />
        </section>
        <aside className="approval-aside">
          <section className="safeguard-card">
            <Icon variant="shield" />
            <h2>{es["workspace.review.safeguard"]}</h2>
            <p>{es["workspace.review.safeguard.body"]}</p>
          </section>
          <section className="effect-card">
            <h2>{es["workspace.review.effect"]}</h2>
            <p>{es["workspace.review.effect.body"]}</p>
            <dl>
              <dt>{es["workspace.review.channel"]}</dt>
              <dd>{es["workspace.review.channel.local"]}</dd>
            </dl>
            <Button id="approve-send" disabled disabledReason={SEND_REASON}>
              {es["workspace.review.send"]}
            </Button>
          </section>
        </aside>
      </div>
      <div className="decision-actions">
        <Button
          id="approve-copy"
          className="button-amber"
          loading={workspace.copying}
          disabled={workspace.paused || pending}
          disabledReason={workspace.paused ? PAUSED_REASON : pending ? PENDING_REASON : undefined}
          onClick={() => {
            const generation = reviewGeneration.current;
            void workspace.copyTask(id, task.revision).then((copied) => {
              if (copied && generation === reviewGeneration.current) workspace.navigate("/logros");
            });
          }}
        >
          <Icon variant="check" />
          {es["workspace.review.copy"]}
        </Button>
        <Button
          disabled={workspace.copying}
          onClick={() => workspace.navigate(`/tareas/${id}?editar=1`)}
        >
          <Icon variant="document" />
          {es["workspace.task.edit"]}
        </Button>
        <Button
          id="review-cancel"
          disabled={workspace.copying}
          onClick={() => {
            workspace.cancelTask(id);
            workspace.navigate(`/tareas/${id}`);
          }}
        >
          {es["workspace.review.cancel"]}
        </Button>
        <RouteButton href="/tareas">{es["workspace.review.defer"]}</RouteButton>
      </div>
    </>
  );
}

export function AchievementsScreen() {
  const workspace = useWorkspace();
  const [selected, setSelected] = useState("");
  const detail = workspace.data.achievements.find((item) => item.id === selected);
  return (
    <>
      <div className="achievement-header">
        <PageHeading
          title={es["workspace.achievements.title"]}
          body={es["workspace.achievements.body"]}
        />
        <div className="achievement-export">
          <Button
            variant="primary"
            disabled={workspace.paused || !workspace.data.achievements.length}
            disabledReason={workspace.paused ? PAUSED_REASON : EXPORT_REASON}
            onClick={workspace.exportAchievements}
          >
            <Icon variant="document" />
            {es["workspace.achievements.export"]}
          </Button>
        </div>
      </div>
      <section className="achievement-summary achievement-metrics">
        <div>
          <span>{es["workspace.home.completed"]}</span>
          <strong>{workspace.data.achievements.length}</strong>
        </div>
        <div>
          <span>{es["workspace.achievements.review"]}</span>
          <strong>{workspace.data.tasks.filter((task) => task.status === "review").length}</strong>
        </div>
        <div>
          <span>{es["workspace.home.income"]}</span>
          <strong className="text-metric">{es["workspace.income.empty"]}</strong>
        </div>
        <div>
          <span>{es["workspace.achievements.approval"]}</span>
          <strong className="text-metric">{es["workspace.achievements.approval.value"]}</strong>
        </div>
      </section>
      <p className="muted-copy">{es["workspace.achievements.no.income"]}</p>
      {workspace.data.achievements.length ? (
        <div className="achievement-list">
          {[...workspace.data.achievements].reverse().map((item, index) => (
            <article key={item.id} className="achievement-row">
              <span className="achievement-check">
                <Icon variant="check" />
              </span>
              <div>
                <span className="status-tag">{es["workspace.task.completed.status"]}</span>
                <h2>{item.title}</h2>
                <p>{es["workspace.achievements.local"]}</p>
              </div>
              <div className="achievement-row-tools">
                <time dateTime={item.at}>
                  {new Intl.DateTimeFormat("es-EC", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  }).format(new Date(item.at))}
                </time>
                <Button onClick={() => setSelected(item.id)}>
                  {es["workspace.achievements.inspect"]} {index + 1}
                </Button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <section className="empty-panel">
          <Icon variant="check" />
          <h2>{es["workspace.achievements.empty"]}</h2>
          <p>{es["workspace.achievements.empty.body"]}</p>
        </section>
      )}
      <div className="screen-actions">
        <RouteButton href="/inicio" primary>
          {es["workspace.achievements.start"]}
          <Icon variant="arrow" />
        </RouteButton>
      </div>
      <Dialog
        open={Boolean(detail)}
        title={es["workspace.achievements.detail.title"]}
        actions={<Button onClick={() => setSelected("")}>{es["workspace.close"]}</Button>}
      >
        {detail && (
          <>
            <p>{es["workspace.achievements.detail.body"]}</p>
            <dl className="copy-detail">
              <dt>{es["workspace.task.title.label"]}</dt>
              <dd>{detail.title}</dd>
              <dt>{es["workspace.achievements.detail.task"]}</dt>
              <dd>{detail.taskId}</dd>
              <dt>{es["workspace.achievements.detail.revision"]}</dt>
              <dd>{detail.revision}</dd>
              <dt>{es["workspace.achievements.detail.date"]}</dt>
              <dd>
                <time dateTime={detail.at}>
                  {new Intl.DateTimeFormat("es-EC", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  }).format(new Date(detail.at))}
                </time>
              </dd>
              <dt>{es["workspace.review.channel"]}</dt>
              <dd>{es["workspace.review.channel.local"]}</dd>
            </dl>
          </>
        )}
      </Dialog>
    </>
  );
}

export function SettingsScreen({
  variant: section = "settings",
}: {
  variant?: "settings" | "autonomy" | "caregiver";
}) {
  const workspace = useWorkspace();
  const speech = useLocalSpeech(workspace.registerStop);
  if (section === "autonomy")
    return (
      <>
        <PageHeading title={es["workspace.autonomy.title"]} body={es["workspace.autonomy.body"]} />
        <section className="settings-panel">
          <Icon variant="shield" />
          <h2>{es["workspace.autonomy.current"]}</h2>
          <p>{es["workspace.autonomy.note"]}</p>
          <RouteButton href="/inicio">{es["workspace.recovery.home"]}</RouteButton>
        </section>
      </>
    );
  if (section === "caregiver")
    return (
      <>
        <PageHeading
          title={es["workspace.caregiver.title"]}
          body={es["workspace.caregiver.body"]}
        />
        <section className="settings-panel">
          <Icon variant="user" />
          <h2>{es["workspace.caregiver.empty"]}</h2>
          <p>{es["workspace.caregiver.note"]}</p>
          <RouteButton href="/">{es["workspace.account.open"]}</RouteButton>
        </section>
      </>
    );
  return (
    <>
      <PageHeading title={es["workspace.settings.title"]} body={es["workspace.settings.body"]} />
      <div className="settings-grid">
        <section className="settings-panel">
          <Icon variant="voice" />
          <h2>{es["workspace.audio.alerts"]}</h2>
          <p>{es["workspace.audio.alerts.body"]}</p>
          <Button
            aria-pressed={workspace.audioAlerts}
            disabled={!speech.ready}
            disabledReason={AUDIO_REASON}
            onClick={() => workspace.setAudioAlerts(!workspace.audioAlerts)}
          >
            {es["workspace.audio.alerts"]}
          </Button>
        </section>
        <section className="settings-panel">
          <Icon variant="contrast" />
          <h2>{es["workspace.contrast"]}</h2>
          <Button
            aria-pressed={workspace.contrast}
            onClick={() => workspace.setContrast(!workspace.contrast)}
          >
            {es["workspace.settings.contrast"]}
          </Button>
        </section>
        <section className="settings-panel">
          <Icon variant="document" />
          <h2>{es["workspace.settings.text"]}</h2>
          <div className="screen-actions">
            <Button
              aria-pressed={!workspace.largeText}
              onClick={() => workspace.setLargeText(false)}
            >
              {es["workspace.settings.text.normal"]}
            </Button>
            <Button aria-pressed={workspace.largeText} onClick={() => workspace.setLargeText(true)}>
              {es["workspace.settings.text.large"]}
            </Button>
          </div>
        </section>
        <section className="settings-panel">
          <Icon variant="keyboard" />
          <h2>{es["workspace.input.title"]}</h2>
          <RouteButton href="/bienvenida">{es["workspace.settings.input"]}</RouteButton>
        </section>
        <section className="settings-panel">
          <Icon variant="user" />
          <h2>{es["workspace.nav.account"]}</h2>
          <RouteButton href="/">{es["workspace.settings.account"]}</RouteButton>
        </section>
      </div>
    </>
  );
}
