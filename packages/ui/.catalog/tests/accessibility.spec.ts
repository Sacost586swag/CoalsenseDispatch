import { expect, test } from "@playwright/test";
import { createRequire } from "node:module";
import { auditTargetSizes } from "../../../../tools/audit/a11y_target_size.ts";
import { cases } from "../cases.ts";
import { es } from "../../src/i18n/es.ts";

const require = createRequire(import.meta.url);
for (const theme of ["default", "contrast"]) {
  for (const scenario of cases) {
    test(`${theme}: ${scenario}`, async ({ page }) => {
      await page.goto(`/?case=${scenario}&theme=${theme}`);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
      const violations = await page.evaluate(async () => {
        const axe = (window as unknown as { axe: typeof import("axe-core") }).axe;
        const result = await axe.run(document, {
          runOnly: {
            type: "tag",
            values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"],
          },
        });
        return result.violations;
      });
      expect(violations).toEqual([]);
      expect(await page.evaluate(auditTargetSizes)).toEqual([]);
      await expect(page.getByRole("button", { name: es["stop.label"], exact: true })).toBeVisible();
    });
  }
}

test("geometry rejects 40 px and accepts 44 px, including inactive controls", async ({ page }) => {
  for (const size of [40, 44]) {
    await page.setContent(
      `<button style="width:${size}px;height:${size}px;padding:0" aria-disabled="true">X</button>`,
    );
    expect(await page.evaluate(auditTargetSizes)).toHaveLength(size === 40 ? 1 : 0);
  }
});

test("keyboard dialog keeps Alto reachable and restores focus", async ({ page }) => {
  await page.goto("/?case=dialog-closed");
  const opener = page.getByRole("button", { name: es["catalog.openDialog"] });
  await opener.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: es["catalog.closeDialog"] })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: es["stop.label"], exact: true })).toBeFocused();
  await page.keyboard.press("Enter");
  await page.keyboard.press("Shift+Tab");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(opener).toBeFocused();
});

test("narrow viewport, enlarged text and head targets remain usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?case=dialog-open&mode=head");
  await page.addStyleTag({ content: ":root { --text-scale: 2; }" });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(await page.evaluate(auditTargetSizes, 64)).toEqual([]);
  const stop = page.getByRole("button", { name: es["stop.label"], exact: true });
  const box = await stop.boundingBox();
  expect(box).not.toBeNull();
  expect(
    await stop.evaluate((node) => {
      const rect = node.getBoundingClientRect();
      return document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2) === node;
    }),
  ).toBe(true);
});
