import { createRequire } from "node:module";
import { expect, test, type Page } from "@playwright/test";
import { auditTargetSizes } from "../../../../tools/audit/a11y_target_size.ts";
import { es } from "../../../../packages/ui/src/i18n/es.ts";

const require = createRequire(import.meta.url);
const error = {
  code: "auth.code.invalid",
  message_es: es["auth.code.invalid.message"],
  recoverable: true,
  next_actions: [es["auth.next.checkCode"]],
};

async function checkAccessibility(page: Page) {
  await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
  const violations = await page.evaluate(async () => {
    const axe = (window as unknown as { axe: typeof import("axe-core") }).axe;
    return (
      await axe.run(document, {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] },
      })
    ).violations;
  });
  expect(violations).toEqual([]);
  expect(await page.evaluate(auditTargetSizes, 44)).toEqual([]);
}

async function setup(page: Page) {
  let authenticated = false;
  const requests: { action: string; body: unknown }[] = [];
  await page.route("**/api/auth/*", async (route) => {
    const action = new URL(route.request().url()).pathname.split("/").at(-1) ?? "";
    if (action === "session") {
      await route.fulfill({
        status: authenticated ? 200 : 401,
        json: authenticated
          ? { account_id: "a", device_id: "d", session_id: "s", role: "person" }
          : { ...error, code: "auth.session.required" },
      });
      return;
    }
    const body: unknown = route.request().postDataJSON();
    requests.push({ action, body });
    if (action === "verify-code") authenticated = true;
    if (action === "sign-out") authenticated = false;
    await route.fulfill({
      json:
        action === "request-code"
          ? { requested: true }
          : action === "verify-code"
            ? { authenticated: true }
            : action === "pair"
              ? { status: "pending" }
              : { signed_out: true },
    });
  });
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: es["auth.request.label"], exact: true }),
  ).toBeEnabled();
  await expect(page.locator("#auth-request")).not.toHaveAttribute("aria-disabled", "true");
  return requests;
}

test("full flow by keyboard, including paste, pairing and sign out", async ({ page }) => {
  const requests = await setup(page);
  await checkAccessibility(page);
  await page.screenshot({ path: "test-results/auth-entry.png", fullPage: true });
  await page.keyboard.press("Tab");
  await page.keyboard.type("persona@example.org");
  await page.keyboard.press("Tab"); // nombre del equipo conserva un valor editable
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { name: es["auth.code.title"], exact: true }),
  ).toBeFocused();
  await checkAccessibility(page);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: es["banner.dismiss.label"] })).toBeFocused();
  await page.keyboard.press("Tab");
  await page.keyboard.insertText("123456");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { name: es["auth.signedIn.title"], exact: true }),
  ).toBeVisible();
  await checkAccessibility(page);
  await page.keyboard.press("Tab");
  await page.keyboard.insertText("654321");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { name: es["auth.pair.pending.title"], exact: true }),
  ).toBeVisible();
  await checkAccessibility(page);
  await page.getByRole("button", { name: es["auth.signOut.label"] }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel(es["auth.email.label"])).toBeVisible();
  expect(requests.map((item) => item.action)).toEqual([
    "request-code",
    "verify-code",
    "pair",
    "sign-out",
  ]);
});

test("simulated selection and dictation use registered visible targets, without mouse or keyboard", async ({
  page,
}) => {
  await page.addInitScript(() => {
    window.addEventListener("cs:nav-targets", (event) => {
      (window as unknown as { targets: unknown }).targets = (event as CustomEvent).detail;
    });
  });
  const requests = await setup(page);
  const select = async (label: string) => {
    await expect
      .poll(() =>
        page.evaluate((name) => {
          const targets =
            (window as unknown as { targets?: { id: string; label: string; disabled: boolean }[] })
              .targets ?? [];
          return targets.some((target) => target.label === name && !target.disabled);
        }, label),
      )
      .toBe(true);
    await page.evaluate((name) => {
      const targets = (window as unknown as { targets: { id: string; label: string }[] }).targets;
      const target = targets.find((item) => item.label === name);
      const element = target ? document.getElementById(target.id) : null;
      if (!element) throw new Error("Registered navigation target is missing");
      element.focus();
      element.click();
    }, label);
  };
  const dictate = async (text: string) => {
    await page.evaluate((value) => {
      const element = document.activeElement;
      if (!(element instanceof HTMLInputElement))
        throw new Error("Dictation needs a focused field");
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
      setter?.call(element, value);
      element.dispatchEvent(new Event("input", { bubbles: true }));
    }, text);
  };
  await select(es["auth.email.label"]);
  await dictate("persona@example.org");
  await select(es["auth.request.label"]);
  await select(es["auth.code.label"]);
  await dictate("123456");
  await select(es["auth.verify.label"]);
  await select(es["auth.pair.code.label"]);
  await dictate("654321");
  await select(es["auth.pair.label"]);
  await expect(
    page.getByRole("heading", { name: es["auth.pair.pending.title"], exact: true }),
  ).toBeVisible();
  expect(requests.map((item) => item.action)).toEqual(["request-code", "verify-code", "pair"]);
});

test("errors, offline and enlarged text retain entered data and expose Alto", async ({
  page,
  context,
}) => {
  await setup(page);
  await page.getByLabel(es["auth.email.label"]).fill("persona@example.org");
  await page.route("**/api/auth/request-code", (route) =>
    route.fulfill({ status: 429, json: { ...error, message_es: es["auth.wait.message"] } }),
  );
  await page.getByRole("button", { name: es["auth.request.label"], exact: true }).click();
  await expect(page.getByText(es["auth.wait.message"])).toBeVisible();
  await expect(page.getByLabel(es["auth.email.label"])).toHaveValue("persona@example.org");
  await checkAccessibility(page);
  await context.setOffline(true);
  await expect(
    page.getByRole("heading", { name: es["state.offline.label"], exact: true }),
  ).toBeVisible();
  await checkAccessibility(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addStyleTag({ content: ":root { --text-scale: 2; }" });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByRole("button", { name: es["stop.label"], exact: true })).toBeVisible();
});

test("Alto aborts loading without losing fields; help dialog leaves Alto reachable", async ({
  page,
}) => {
  await setup(page);
  let release: (() => void) | undefined;
  const hold = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/auth/request-code", async (route) => {
    await hold;
    await route.fulfill({ json: { requested: true } }).catch(() => {});
  });
  await page.getByLabel(es["auth.email.label"]).fill("persona@example.org");
  await page.getByRole("button", { name: es["auth.request.label"], exact: true }).click();
  await expect(page.getByText(es["auth.loading.message"])).toBeVisible();
  await checkAccessibility(page);
  await page.getByRole("button", { name: es["stop.label"], exact: true }).click();
  release?.();
  await expect(page.getByText(es["auth.stopped.message"])).toBeVisible();
  await expect(page.getByLabel(es["auth.email.label"])).toHaveValue("persona@example.org");
  await page.getByRole("button", { name: es["help.label"], exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await checkAccessibility(page);
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: es["stop.label"], exact: true })).toBeFocused();
});

test("high contrast also passes authentication accessibility", async ({ page }) => {
  await setup(page);
  await page.getByRole("button", { name: es["auth.theme.label"] }).click();
  await checkAccessibility(page);
});
