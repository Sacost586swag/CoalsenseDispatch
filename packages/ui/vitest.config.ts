import { defineConfig } from "vitest/config";

// Tokens keep their node:test suite (tests/*.test.ts); Vitest runs only the component suite.
export default defineConfig({
  test: { environment: "jsdom", include: ["tests/**/*.test.tsx"] },
});
