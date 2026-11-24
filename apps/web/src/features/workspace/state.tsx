"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  useTransition,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { es } from "@coalsense/ui";
import {
  appendVersion,
  sameDraft,
  validDraft,
  versionInput,
  type DraftInput,
  type TaskVersion,
} from "./versions.ts";
import { hasBlockChange, type BlockDraft } from "./blocks.ts";

export type InputMode = "keyboard" | "voice" | "head" | "gaze";
export type TaskKind = "email" | "document" | "social";
export type Task = {
  id: string;
  kind: TaskKind;
  title: string;
  subject: string;
  recipient: string;
  body: string;
  revision: number;
  createdAt: string;
  updatedAt?: string;
  status: "draft" | "review" | "copied";
};
type Achievement = { id: string; taskId: string; revision: number; title: string; at: string };
type Data = { mode: InputMode; practice: string; tasks: Task[]; achievements: Achievement[] };
type TaskInput = DraftInput;
type Workspace = {
  data: Data;
  navigating: boolean;
  navigate: (href: string) => void;
  paused: boolean;
  contrast: boolean;
  largeText: boolean;
  copying: boolean;
  audioAlerts: boolean;
  setAudioAlerts: (enabled: boolean) => void;
  notice: string;
  canUndo: boolean;
  newKind: TaskKind;
  setNewKind: (kind: TaskKind) => void;
  setContrast: (value: boolean) => void;
  setLargeText: (value: boolean) => void;
  changeMode: (mode: InputMode) => void;
  savePractice: (text: string) => boolean;
  createTask: (input: TaskInput) => string | null;
  updateTask: (id: string, input: TaskInput, expectedRevision: number) => boolean;
  versionsFor: (id: string) => readonly TaskVersion[];
  restoreVersion: (id: string, revision: number, expectedRevision: number) => boolean;
  readBlockEditor: (key: string) => BlockDraft | undefined;
  writeBlockEditor: (key: string, draft: BlockDraft | undefined) => void;
  discardEdits: (id: string) => void;
  pendingEdit: (id: string) => "whole" | "blocks" | null;
  cancelTask: (id: string) => void;
  readEditor: (key: string) => TaskInput | undefined;
  writeEditor: (key: string, input: TaskInput) => void;
  clearEditor: (key: string) => void;
  exportAchievements: () => void;
  copyTask: (id: string, revision: number) => Promise<boolean>;
  stop: () => void;
  resume: () => void;
  undo: () => void;
  registerStop: (signal: () => void) => () => void;
};
const Context = createContext<Workspace | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [navigating, startNavigation] = useTransition();
  const navigatingRef = useRef(false);
  const navigationOrigin = useRef("");
  useEffect(() => {
    navigatingRef.current = navigating;
  }, [navigating]);
  // Private text stays in this tab's memory. No localStorage, telemetry or provider calls.
  const [data, setData] = useState<Data>({
    mode: "keyboard",
    practice: "",
    tasks: [],
    achievements: [],
  });
  const current = useRef(data);
  const editors = useRef(new Map<string, TaskInput>());
  const blockEditors = useRef(new Map<string, BlockDraft>());
  const versions = useRef(new Map<string, readonly TaskVersion[]>());
  const history = useRef<Array<Data | null>>([]);
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);
  const [contrast, setContrast] = useState(false);
  const [largeText, setLargeText] = useState(false);
  const [notice, setNotice] = useState("");
  const [copying, setCopying] = useState(false);
  const [audioAlerts, setAudioAlerts] = useState(false);
  const copyingRef = useRef(false);
  const generation = useRef(0);
  const stopSignals = useRef(new Set<() => void>());
  const registerStop = useCallback((signal: () => void) => {
    stopSignals.current.add(signal);
    return () => {
      stopSignals.current.delete(signal);
    };
  }, []);
  const [newKind, setNewKind] = useState<TaskKind>("email");

  function commit(next: Data, reversible = true) {
    history.current.push(reversible ? current.current : null);
    if (history.current.length > 30) history.current.shift(); // [SUPUESTO] memory-only undo capacity
    current.current = next;
    setData(next);
  }
  function updateTask(id: string, input: TaskInput, expectedRevision: number): boolean {
    if (pausedRef.current || copyingRef.current) return false;
    const task = current.current.tasks.find((item) => item.id === id);
    if (!task || task.revision !== expectedRevision) {
      setNotice(es["workspace.review.changed"]);
      return false;
    }
    if (!validDraft(input)) {
      setNotice(es["workspace.editor.invalid.draft"]);
      return false;
    }
    const at = new Date().toISOString();
    const saved = appendVersion(versions.current.get(id) ?? [], input, at);
    const revision = saved.at(-1)?.revision;
    if (!revision) return false;
    versions.current.set(id, saved);
    commit({
      ...current.current,
      tasks: current.current.tasks.map((item) =>
        item.id === id ? { ...item, ...input, revision, status: "review", updatedAt: at } : item,
      ),
    });
    setNotice(es["workspace.editor.saved"]);
    return true;
  }
  function pendingEdit(id: string): "whole" | "blocks" | null {
    const task = current.current.tasks.find((item) => item.id === id);
    if (!task) return null;
    const key = `${id}:${task.revision}`;
    const whole = editors.current.get(key);
    if (whole && !sameDraft(task, whole)) return "whole";
    return hasBlockChange(task.body, blockEditors.current.get(key)) ? "blocks" : null;
  }
  const value: Workspace = {
    data,
    navigating,
    navigate(href) {
      navigationOrigin.current = window.location.pathname + window.location.search;
      navigatingRef.current = true;
      startNavigation(() => router.push(href));
    },
    paused,
    contrast,
    largeText,
    copying,
    audioAlerts,
    setAudioAlerts,
    notice,
    canUndo: Boolean(history.current.at(-1)),
    newKind,
    setNewKind,
    setContrast,
    setLargeText,
    updateTask,
    pendingEdit,
    versionsFor(id) {
      return versions.current.get(id) ?? [];
    },
    restoreVersion(id, revision, expectedRevision) {
      const task = current.current.tasks.find((item) => item.id === id);
      if (!task) return false;
      if (pendingEdit(id)) {
        setNotice(es["workspace.editor.pending"]);
        return false;
      }
      const saved = versions.current.get(id)?.find((item) => item.revision === revision);
      if (!saved || !updateTask(id, versionInput(saved), expectedRevision)) return false;
      setNotice(es["workspace.versions.restored"]);
      return true;
    },
    readBlockEditor(key) {
      return blockEditors.current.get(key);
    },
    writeBlockEditor(key, draft) {
      if (draft) blockEditors.current.set(key, draft);
      else blockEditors.current.delete(key);
    },
    discardEdits(id) {
      const task = current.current.tasks.find((item) => item.id === id);
      if (!task) return;
      const key = `${id}:${task.revision}`;
      editors.current.delete(key);
      blockEditors.current.delete(key);
      setNotice(es["workspace.editor.discarded"]);
    },
    readEditor(key) {
      return editors.current.get(key);
    },
    writeEditor(key, input) {
      editors.current.set(key, input);
    },
    clearEditor(key) {
      editors.current.delete(key);
    },
    changeMode(mode) {
      commit({ ...current.current, mode });
    },
    savePractice(practice) {
      if (pausedRef.current || copyingRef.current) return false;
      commit({ ...current.current, practice });
      return true;
    },
    createTask(input) {
      if (pausedRef.current || copyingRef.current) return null;
      if (!validDraft(input)) {
        setNotice(es["workspace.editor.invalid.draft"]);
        return null;
      }
      const id = crypto.randomUUID();
      const at = new Date().toISOString();
      versions.current.set(id, appendVersion([], input, at));
      commit({
        ...current.current,
        tasks: [
          ...current.current.tasks,
          { ...input, id, revision: 1, status: "review", createdAt: at },
        ],
      });
      return id;
    },
    cancelTask(id) {
      commit({
        ...current.current,
        tasks: current.current.tasks.map((task) =>
          task.id === id ? { ...task, status: "draft" } : task,
        ),
      });
      setNotice(es["workspace.review.cancelled"]);
    },
    exportAchievements() {
      if (pausedRef.current || !current.current.achievements.length) return;
      const text = [
        es["catalog.product"],
        es["workspace.achievements.export.title"],
        "",
        ...current.current.achievements.map(
          (item) =>
            `${new Intl.DateTimeFormat("es-EC", { dateStyle: "medium", timeStyle: "short" }).format(new Date(item.at))}\n${item.title}\n${es["workspace.task.completed.status"]}\n`,
        ),
      ].join("\n");
      const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "coalsense-logros.txt";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 0);
      commit({ ...current.current }, false);
      setNotice(es["workspace.achievements.export.ready"]);
    },
    stop() {
      generation.current += 1;
      pausedRef.current = true;
      setPaused(true);
      if (navigatingRef.current && navigationOrigin.current) {
        navigatingRef.current = false;
        startNavigation(() => router.replace(navigationOrigin.current, { scroll: false }));
      }
      setNotice(es["workspace.stop.notice"]);
      for (const signal of stopSignals.current) {
        try {
          signal();
        } catch {
          setNotice(es["workspace.stop.cleanup"]);
        }
      }
    },
    registerStop,
    resume() {
      pausedRef.current = false;
      setPaused(false);
      setNotice("");
    },
    undo() {
      const previous = history.current.at(-1);
      if (!previous) {
        setNotice(es[history.current.length ? "workspace.undo.barrier" : "workspace.undo.none"]);
        return;
      }
      const invalidatesPending = current.current.tasks.some(
        (task) =>
          pendingEdit(task.id) &&
          previous.tasks.find((item) => item.id === task.id)?.revision !== task.revision,
      );
      if (invalidatesPending) {
        setNotice(es["workspace.editor.undo.pending"]);
        return;
      }
      history.current.pop();
      current.current = previous;
      setData(previous);
      setNotice(es["workspace.undo.done"]);
    },
    async copyTask(id, revision) {
      const task = current.current.tasks.find((item) => item.id === id);
      if (!task || task.revision !== revision) {
        setNotice(es["workspace.review.changed"]);
        return false;
      }
      if (pausedRef.current) {
        setNotice(es["workspace.review.paused"]);
        return false;
      }
      if (copyingRef.current) return false;
      if (pendingEdit(id)) {
        setNotice(es["workspace.editor.pending"]);
        return false;
      }
      const permissionGeneration = generation.current;
      copyingRef.current = true;
      setCopying(true);
      try {
        const text =
          task.kind === "email"
            ? `${es["workspace.task.recipient"]}: ${task.recipient}\n${es["workspace.task.subject"]}: ${task.subject || task.title}\n\n${task.body}`
            : task.body;
        await navigator.clipboard.writeText(text);
        const changed = current.current.tasks.find((item) => item.id === id)?.revision !== revision;
        if (permissionGeneration !== generation.current || changed) {
          commit({ ...current.current }, false);
          setNotice(es[changed ? "workspace.review.changed" : "workspace.review.cancel.wait"]);
          return false;
        }
        commit(
          {
            ...current.current,
            tasks: current.current.tasks.map((item) =>
              item.id === id ? { ...item, status: "copied" } : item,
            ),
            achievements: current.current.achievements.some(
              (item) => item.taskId === task.id && item.revision === revision,
            )
              ? current.current.achievements
              : [
                  ...current.current.achievements,
                  {
                    id: crypto.randomUUID(),
                    taskId: task.id,
                    revision,
                    title: task.title,
                    at: new Date().toISOString(),
                  },
                ],
          },
          false,
        );
        setNotice(es["workspace.review.copy.done"]);
        return true;
      } catch {
        setNotice(es["workspace.review.copy.failed"]);
        return false;
      } finally {
        copyingRef.current = false;
        setCopying(false);
      }
    },
  };
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useWorkspace() {
  const value = useContext(Context);
  if (!value) throw new Error("Workspace context is required");
  return value;
}
