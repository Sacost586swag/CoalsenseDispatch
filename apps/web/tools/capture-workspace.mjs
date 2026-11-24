/* global document, innerWidth */
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import process from "node:process";
import { log } from "node:console";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await mkdir("test-results", { recursive: true });
const base = process.argv[2] ?? "http://127.0.0.1:4175";
try {
  for (const route of ["inicio", "bienvenida", "calibracion", "primera-tarea", "logros"]) {
    await page.goto(`${base}/${route}`);
    await page.getByRole("heading", { level: 1 }).waitFor();
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: `test-results/stitch-${route}.png`, fullPage: true });
    const size = await page.evaluate(() => ({
      width: innerWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    log(route, size);
  }
} finally {
  await browser.close();
}
