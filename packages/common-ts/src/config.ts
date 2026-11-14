import { inspect } from "node:util";
import { ZodError, type z } from "zod";

/** Envolver los campos secretos con una transformación del esquema Zod. */
export class Secret {
  #value: string;

  constructor(value: string) {
    this.#value = value;
    Object.freeze(this);
  }

  getSecretValue(): string {
    return this.#value;
  }

  toString(): string {
    return "***";
  }

  toJSON(): string {
    return "***";
  }

  [inspect.custom](): string {
    return "***";
  }
}

export class ConfigError extends Error {
  constructor(detail: string) {
    super(`La configuración no permite iniciar la aplicación (${detail}).`);
    this.name = "ConfigError";
  }
}

/**
 * Validar al arrancar. El mensaje lista solo nombres de variables, nunca valores
 * ni mensajes del validador. Solo se capturan errores de esquema (ZodError).
 */
export function loadConfig<T>(
  schema: z.ZodType<T>,
  env: Readonly<Record<string, string | undefined>> = process.env,
): T {
  try {
    return schema.parse({ ...env });
  } catch (error) {
    if (!(error instanceof ZodError)) throw error;
    const missing = new Set<string>();
    const invalid = new Set<string>();
    for (const issue of error.issues) {
      const name = issue.path.join(".") || "(raíz)";
      const key = issue.path[0];
      (typeof key === "string" && env[key] === undefined ? missing : invalid).add(name);
    }
    const parts: string[] = [];
    if (missing.size) parts.push(`faltan: ${[...missing].join(", ")}`);
    if (invalid.size) parts.push(`inválidas: ${[...invalid].join(", ")}`);
    throw new ConfigError(parts.join("; "));
  }
}
