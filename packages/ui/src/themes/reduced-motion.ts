import { defaultTheme } from "./default.ts";
import { defineTheme } from "../tokens/theme.ts";

export const reducedMotion = defineTheme({
  ...defaultTheme,
  motion: { ...defaultTheme.motion, duration: 0 },
} as const);
