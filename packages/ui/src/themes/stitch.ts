/** Approved Stitch UI-UX palette; the safety and target floors still come from the shared theme. */
import { defaultTheme } from "./default.ts";
import { defineTheme } from "../tokens/theme.ts";

export const stitchTheme = defineTheme({
  ...defaultTheme,
  color: {
    background: "#FCF9F4",
    foreground: "#1C1C19",
    secondaryText: "#3F4947",
    primary: "#00433F",
    onPrimary: "#FFFFFF",
    accent: "#805600",
    onAccent: "#FFFFFF",
    border: "#6F7977",
    ring: "#0F5C57",
    stop: "#BA1A1A",
    onStop: "#FFFFFF",
  },
  font: {
    ...defaultTheme.font,
    family: '"Atkinson Hyperlegible Next", "Atkinson Hyperlegible", system-ui, sans-serif',
    base: 20,
  },
} as const);
