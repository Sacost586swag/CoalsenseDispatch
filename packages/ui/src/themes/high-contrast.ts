import { defaultTheme } from "./default.ts";
import { defineTheme } from "../tokens/theme.ts";

export const highContrast = defineTheme({
  ...defaultTheme,
  color: {
    background: "#000000",
    foreground: "#FFFFFF",
    secondaryText: "#FFFFFF",
    primary: "#FFD166",
    onPrimary: "#000000",
    accent: "#FFFFFF",
    onAccent: "#000000",
    border: "#FFFFFF",
    ring: "#FFD166",
    stop: "#FFFFFF",
    onStop: "#000000",
  },
  border: { width: 2 },
} as const);
