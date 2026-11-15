import { AppError } from "./errors.ts";
import { newId, wallClockIso } from "./ids.ts";

const contentKeys = [
  "text",
  "body",
  "dictation",
  "profile",
  "filename",
  "recipient",
  "prompt",
  "completion",
  "audio",
  "video",
  "landmarks",
];
const omitted = "[omitido]";
const levels = { DEBUG: 10, INFO: 20, WARNING: 30, ERROR: 40, CRITICAL: 50 };
export type LogLevel = keyof typeof levels;
export interface LoggerOptions {
  level?: LogLevel;
  contentKeys?: readonly string[];
  /** Receives one JSON record with a terminating newline. Defaults to stderr. */
  sink?: (line: string) => void;
}

function event(value: unknown): string {
  return typeof value === "string" && /^[A-Za-z][A-Za-z0-9_.-]{0,63}$/.test(value)
    ? value
    : omitted;
}

function scrub(
  value: unknown,
  keys: readonly string[],
  seen = new Set<object>(),
  depth = 0,
): unknown {
  if (depth >= 16) return omitted;
  if (value instanceof Error) {
    return {
      type: event(Object.getPrototypeOf(value).constructor.name),
      id: newId(),
      ...(value instanceof AppError ? { code: event(value.code) } : {}),
    };
  }
  if (value === null || typeof value === "boolean") return value;
  if (typeof value === "number") return Number.isFinite(value) ? value : omitted;
  if (typeof value === "string") return Array.from(value).length <= 64 ? value : omitted;
  if (typeof value !== "object" || seen.has(value)) return omitted;
  if (
    !Array.isArray(value) &&
    Object.getPrototypeOf(value) !== Object.prototype &&
    Object.getPrototypeOf(value) !== null
  )
    return omitted;
  seen.add(value);
  try {
    if (Array.isArray(value)) return value.map((item) => scrub(item, keys, seen, depth + 1));
    const result: Record<string, unknown> = Object.create(null);
    for (const [key, descriptor] of Object.entries(Object.getOwnPropertyDescriptors(value))) {
      if (Array.from(key).length > 64 || keys.some((part) => key.toLowerCase().includes(part)))
        continue;
      result[key] =
        "value" in descriptor ? scrub(descriptor.value, keys, seen, depth + 1) : omitted;
    }
    return result;
  } finally {
    seen.delete(value);
  }
}

/** Messages must be constant event identifiers; put technical metadata in extra. */
export function createLogger(name: string, opts: LoggerOptions = {}) {
  const keys = [...contentKeys, ...(opts.contentKeys ?? []).map((key) => key.toLowerCase())];
  const threshold = levels[opts.level ?? "INFO"];
  const sink =
    opts.sink ??
    ((line: string) => {
      process.stderr.write(line);
    });
  const write = (level: LogLevel, message: string, extra: Record<string, unknown> = {}) => {
    if (levels[level] < threshold) return;
    sink(
      JSON.stringify({
        timestamp: wallClockIso(),
        level,
        logger: event(name),
        message: event(message),
        extra: scrub(extra, keys),
      }) + "\n",
    );
  };
  return {
    debug: (message: string, extra?: Record<string, unknown>) => write("DEBUG", message, extra),
    info: (message: string, extra?: Record<string, unknown>) => write("INFO", message, extra),
    warn: (message: string, extra?: Record<string, unknown>) => write("WARNING", message, extra),
    error: (message: string, extra?: Record<string, unknown>) => write("ERROR", message, extra),
    critical: (message: string, extra?: Record<string, unknown>) =>
      write("CRITICAL", message, extra),
  };
}
