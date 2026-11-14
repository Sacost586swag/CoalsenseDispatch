/** Semantic colors from MASTER.md's binding orchestrator decisions. */
export const color = {
  background: "#FAF7F2",
  foreground: "#1F1B16",
  secondaryText: "#57534E",
  primary: "#9A3412",
  onPrimary: "#FFFFFF",
  accent: "#3F6212",
  onAccent: "#FFFFFF",
  border: "#8A8178",
  ring: "#1D4ED8",
  stop: "#B91C1C",
  onStop: "#FFFFFF",
} as const;

/** CSS pixel values; targets use physical CSS px, typography uses rem. */
export const space = { xs: 4, sm: 8, md: 24, lg: 32, xl: 48, "2xl": 64, "3xl": 96 } as const;
export const font = {
  family: '"Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif',
  base: 18,
  lineHeight: 1.5,
  regular: 400,
  bold: 700,
} as const;
export const motion = { property: "opacity", duration: 150 } as const;
export const target = { min: 44, head: 64, gap: 16 } as const;
