import type { color, space } from "./base.ts";

export interface Theme {
  readonly color: { readonly [K in keyof typeof color]: string };
  readonly space: { readonly [K in keyof typeof space]: number };
  readonly font: {
    readonly family: string;
    readonly base: number;
    readonly lineHeight: number;
    readonly regular: number;
    readonly bold: number;
  };
  readonly motion: { readonly property: "opacity"; readonly duration: number };
  readonly target: { readonly min: number; readonly head: number; readonly gap: number };
  readonly border: { readonly width: number };
  readonly ring: { readonly width: number };
  readonly textScale: number;
}

/** Type-only brand: a Theme that went through defineTheme (floors checked, deep-frozen). */
export declare const validatedBrand: unique symbol;
export type ValidatedTheme<T extends Theme = Theme> = T & { readonly [validatedBrand]: true };

const validated = new WeakSet<object>();

/** True only for objects returned by defineTheme; spread copies are not. */
export const isValidatedTheme = (theme: object): boolean => validated.has(theme);

function deepFreeze<V>(value: V): V {
  if (value !== null && typeof value === "object") {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

type Below44<T extends number[] = []> = T["length"] extends 44
  ? T[number]
  : Below44<[...T, T["length"]]>;

/** Dynamic numbers are validated at runtime; invalid literals fail tsc. */
export type TargetSize<N extends number> = N extends N
  ? `${N}` extends `-${string}` | `${Below44}` | `${Below44}.${string}`
    ? never
    : N
  : never;

export function defineTheme<const T extends Theme>(
  theme: T & {
    readonly target: {
      readonly min: TargetSize<NoInfer<T["target"]["min"]>>;
      readonly head: TargetSize<NoInfer<T["target"]["head"]>>;
    };
  },
): ValidatedTheme<T> {
  for (const key of ["min", "head"] as const) {
    if (!Number.isFinite(theme.target[key]) || theme.target[key] < 44) {
      throw new RangeError(`target.${key} must be at least 44 CSS px`);
    }
  }
  if (!Number.isFinite(theme.target.gap) || theme.target.gap < 16) {
    throw new RangeError("target.gap must be at least 16 CSS px");
  }
  if (!Number.isFinite(theme.textScale) || theme.textScale < 1 || theme.textScale > 2) {
    throw new RangeError("textScale must be between 1 and 2");
  }
  if (
    !Number.isFinite(theme.motion.duration) ||
    theme.motion.duration < 0 ||
    theme.motion.duration > 150 ||
    theme.motion.property !== "opacity"
  ) {
    throw new RangeError("motion must be opacity only, from 0 to 150 ms");
  }
  // Clone so callers keep no mutable reference to the validated theme.
  const result = deepFreeze(structuredClone(theme)) as unknown as ValidatedTheme<T>;
  validated.add(result);
  return result;
}
