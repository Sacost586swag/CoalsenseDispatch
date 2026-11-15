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
  // Clone first and validate the clone: a hostile getter must not pass the checks and then
  // hand different values to the clone (it is read exactly once, by structuredClone).
  const clone = structuredClone(theme) as Theme;
  for (const key of ["min", "head"] as const) {
    if (!Number.isFinite(clone.target[key]) || clone.target[key] < 44) {
      throw new RangeError(`target.${key} must be at least 44 CSS px`);
    }
  }
  if (!Number.isFinite(clone.target.gap) || clone.target.gap < 16) {
    throw new RangeError("target.gap must be at least 16 CSS px");
  }
  if (!Number.isFinite(clone.textScale) || clone.textScale < 1 || clone.textScale > 2) {
    throw new RangeError("textScale must be between 1 and 2");
  }
  if (
    !Number.isFinite(clone.motion.duration) ||
    clone.motion.duration < 0 ||
    clone.motion.duration > 150 ||
    clone.motion.property !== "opacity"
  ) {
    throw new RangeError("motion must be opacity only, from 0 to 150 ms");
  }
  const result = deepFreeze(clone) as unknown as ValidatedTheme<T>;
  validated.add(result);
  return result;
}
