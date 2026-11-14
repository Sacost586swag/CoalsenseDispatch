import { defineTheme, isValidatedTheme, type ValidatedTheme } from "./theme.ts";

const kebab = (name: string): string => name.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);

/** Complete :root stylesheet. Insert after other theme styles; no browser API needed. */
export function toCssVariables(theme: ValidatedTheme): string {
  if (!isValidatedTheme(theme)) throw new TypeError("theme must come from defineTheme");
  defineTheme(theme); // belt and braces: re-check floors
  const declarations: string[] = [];
  const add = (name: string, value: string | number): void => {
    declarations.push(`  --${name}: ${value};`);
  };
  for (const [key, value] of Object.entries(theme.color)) add(`color-${kebab(key)}`, value);
  for (const [key, value] of Object.entries(theme.space)) add(`space-${key}`, `${value}px`);
  for (const [key, value] of Object.entries(theme.target)) add(`target-${key}`, `${value}px`);
  add("text-scale", theme.textScale);
  add("font-family", theme.font.family);
  // Relative to the browser root size (16px default), preserving user font preferences.
  add("font-base", `calc(${theme.font.base / 16}rem * var(--text-scale))`);
  add("font-line-height", theme.font.lineHeight);
  add("font-regular", theme.font.regular);
  add("font-bold", theme.font.bold);
  add("border-width", `${theme.border.width}px`);
  add("ring-width", `${theme.ring.width}px`);
  add("motion-property", theme.motion.property);
  add("motion-duration", `${theme.motion.duration}ms`);
  return `:root {\n${declarations.join("\n")}\n}\n@media (prefers-reduced-motion: reduce) {\n  :root {\n    --motion-duration: 0ms;\n  }\n}\n`;
}
