import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".catalog/tests",
  fullyParallel: true,
  workers: 2,
  use: { baseURL: "http://127.0.0.1:4173", headless: true, screenshot: "only-on-failure" },
  webServer: {
    command:
      "node node_modules/vite/bin/vite.js build .catalog --outDir ../catalog-dist && node node_modules/vite/bin/vite.js preview .catalog --outDir ../catalog-dist --host 127.0.0.1 --port 4173 --strictPort",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: false,
  },
});
