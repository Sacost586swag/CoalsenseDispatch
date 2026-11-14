import { color, space, font, motion, target } from "../tokens/base.ts";
import { defineTheme } from "../tokens/theme.ts";

export const defaultTheme = defineTheme({
  color,
  space,
  font,
  motion,
  target,
  border: { width: 1 },
  ring: { width: 3 },
  textScale: 1,
} as const);
export { defaultTheme as default };
