import { inspect } from "node:util";
import type { z } from "zod";

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
  constructor() {
    super("La configuración es inválida o faltan variables requeridas.");
    this.name = "ConfigError";
  }
}

/** Validar al arrancar. No propagar mensajes, causas ni valores del validador. */
export function loadConfig<T>(
  schema: z.ZodType<T>,
  env: Readonly<Record<string, string | undefined>> = process.env,
): T {
  try {
    return schema.parse({ ...env });
  } catch {
    throw new ConfigError();
  }
}
