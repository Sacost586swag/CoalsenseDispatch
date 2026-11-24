import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: true,
  workers: 2,
  use: { baseURL: "http://127.0.0.1:4174", headless: true, screenshot: "only-on-failure" },
  webServer: {
    timeout: 180_000,
    stdout: "pipe",
    command:
      "node node_modules/next/dist/bin/next build && node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 4174",
    url: "http://127.0.0.1:4174",
    reuseExistingServer: false,
    env: {
      COALSENSE_WEB_ORIGIN: "https://app.example.org",
      COALSENSE_AUTH_ORIGIN: "https://api.example.org",
    },
  },
});
