import { defineConfig } from "vitest/config";

// Tokens keep their node:test suite (tests/*.test.ts); Vitest runs only the component suite.
// shortcut: timeouts and worker count are [SUPUESTO] values chosen after one unexplained
// "unhandled error" under load (jsdom + axe-core import took 79 s); tune with CI numbers.
export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.tsx"],
    testTimeout: 30_000,
    hookTimeout: 30_000,
    pool: "forks",
    maxWorkers: 2,
  },
});
