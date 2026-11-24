import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";
import { es } from "../../../../packages/ui/src/i18n/es.ts";
import { auditTargetSizes } from "../../../../tools/audit/a11y_target_size.ts";

const require = createRequire(import.meta.url);
async function audit(page: Page, minimum = 44, waitNavigation = true) {
  if (waitNavigation) await expect(page.locator(".navigation-notice")).toHaveCount(0);
  const routeTitles: Record<string, keyof typeof es> = {
    "/bienvenida": "workspace.welcome.title",
    "/calibracion": "workspace.calibration.title",
    "/primera-tarea": "workspace.practice.title",
    "/inicio": "workspace.nav.home",
    "/tareas": "workspace.task.list.title",
    "/tareas/nueva": "workspace.task.new.title",
    "/logros": "workspace.achievements.title",
    "/ajustes": "workspace.nav.settings",
    "/autonomia": "workspace.nav.autonomy",
    "/cuidador": "workspace.nav.caregiver",
  };
  const path = new URL(page.url()).pathname;
  const title = (await page.locator(".emergency-recovery").count())
    ? "workspace.recovery.root.title"
    : (routeTitles[path] ??
      (path.endsWith("/revision")
        ? "workspace.review.title"
        : /^\/tareas\/[^/]+$/.test(path)
          ? "workspace.task.progress.title"
          : "workspace.recovery.missing.title"));
  // Wait for this route's metadata, rather than accepting the previous page's product suffix.
  await expect(page).toHaveTitle(`${es[title]} · ${es["catalog.product"]}`);
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
  const duplicateLabels = await page.evaluate(() => {
    const controls = Array.from(
      document.querySelectorAll<HTMLElement>("button, a[href], input, textarea, select"),
    ).filter(
      (element) =>
        element.getBoundingClientRect().width > 0 &&
        !element.closest("[inert], [aria-hidden='true']"),
    );
    const labels = controls
      .map((element) => {
        if (
          element instanceof HTMLInputElement ||
          element instanceof HTMLTextAreaElement ||
          element instanceof HTMLSelectElement
        ) {
          return Array.from(element.labels ?? [])
            .map((label) => label.textContent ?? "")
            .join(" ");
        }
        const copy = element.cloneNode(true) as HTMLElement;
        copy
          .querySelectorAll("[aria-hidden='true'], .cs-visually-hidden")
          .forEach((node) => node.remove());
        return copy.textContent ?? "";
      })
      .map((label) => label.replace(/\s+/g, " ").trim().toLocaleLowerCase("es-EC"));
    return labels.filter((label, index) => labels.indexOf(label) !== index);
  });
  expect(duplicateLabels).toEqual([]);
  expect(await page.evaluate(auditTargetSizes, minimum)).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.locator("#cs-stop")).toBeInViewport();
  await expect(page.locator("#cs-undo")).toBeInViewport();
  await expect(page.locator("#cs-help")).toBeInViewport();
}

for (const route of [
  "bienvenida",
  "calibracion",
  "primera-tarea",
  "inicio",
  "tareas",
  "logros",
  "ajustes",
  "autonomia",
  "cuidador",
]) {
  test(`${route}: Stitch layout, default and high contrast, accessible controls`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(`/${route}`);
    await page.getByRole("heading", { level: 1 }).waitFor();
    await audit(page);
    await page.screenshot({ path: `test-results/stitch-${route}.png`, fullPage: true });
    await page.locator("#workspace-contrast").click();
    await audit(page);
  });
}

async function createTask(page: Page, body = "Contenido privado de mi borrador.") {
  await page.goto("/inicio");
  await page.getByRole("link", { name: new RegExp(es["workspace.task.email.start"]) }).click();
  await page.getByLabel(es["workspace.task.title.label"]).fill("Seguimiento profesional");
  await page
    .getByLabel(es["workspace.task.recipient"], { exact: true })
    .fill("persona@example.org");
  await page.getByLabel(es["workspace.task.subject"], { exact: true }).fill("Notas de la reunión");
  await page.getByLabel(es["workspace.task.notes"], { exact: true }).fill(body);
  await page.getByRole("button", { name: es["workspace.task.prepare"], exact: true }).click();
  await expect(
    page.getByRole("heading", { name: es["workspace.task.progress.title"] }),
  ).toBeFocused();
}

test("numbered block edits preserve neighbours, Undo keeps versions, restoration makes a new revision", async ({
  page,
}) => {
  await mockClipboard(page);
  const original = "# Título\n\nPrimer párrafo.\n\n- Uno\n- Dos\n\nFinal intacto.";
  const changed = original.replace("Primer párrafo.", "Mi párrafo corregido.");
  await createTask(page, original);
  await page.getByRole("button", { name: es["workspace.editor.blocks"], exact: true }).click();
  await page
    .getByRole("button", { name: `${es["workspace.editor.select"]} 2`, exact: true })
    .click();
  await page.getByLabel(es["workspace.editor.text"], { exact: true }).fill("Mi párrafo corregido.");
  await expect(
    page.getByRole("button", { name: `${es["workspace.editor.select"]} 3`, exact: true }),
  ).toHaveAttribute("aria-disabled", "true");
  await page.getByRole("button", { name: es["workspace.editor.compare"], exact: true }).click();
  await expect(page.locator(".editor-comparison > section").nth(0)).toContainText(
    "Primer párrafo.",
  );
  await expect(page.locator(".editor-comparison > section").nth(1)).toContainText(
    "Mi párrafo corregido.",
  );
  await audit(page);
  await page.screenshot({ path: "test-results/stitch-editor-bloques.png", fullPage: true });
  await page.getByRole("button", { name: es["workspace.editor.apply"], exact: true }).click();
  await expect(page.locator(".document-preview")).toHaveText(changed);
  await page.locator("#cs-undo").click();
  await expect(page.locator(".document-preview")).toHaveText(original);
  await page.getByRole("button", { name: es["workspace.versions.button"], exact: true }).click();
  await page
    .getByRole("button", { name: `${es["workspace.versions.show"]} 2`, exact: true })
    .click();
  await audit(page);
  await page.getByRole("button", { name: es["workspace.versions.use"], exact: true }).click();
  await expect(page.locator(".document-preview")).toHaveText(changed);
  await expect(
    page.getByText(`${es["workspace.versions.current"]} 3`, { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await page.locator("#approve-copy").click();
  await expect(
    page.getByRole("heading", { name: es["workspace.achievements.title"] }),
  ).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { copied?: string }).copied)).toBe(
    `Destinatario: persona@example.org\nAsunto: Notas de la reunión\n\n${changed}`,
  );
});

test("pending block edits survive navigation and prevent copying an older preview", async ({
  page,
}) => {
  await mockClipboard(page);
  await createTask(page, "Uno.\n\nDos.");
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.review.open.editor"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.editor.back"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.editor.blocks"], exact: true }).click();
  await page
    .getByRole("button", { name: `${es["workspace.editor.select"]} 2`, exact: true })
    .click();
  await page
    .getByLabel(es["workspace.editor.text"], { exact: true })
    .fill("Un cambio todavía pendiente.");
  await page.locator("#cs-undo").click();
  await expect(page.getByText(es["workspace.editor.undo.pending"], { exact: true })).toBeVisible();
  await expect(page.getByLabel(es["workspace.editor.text"], { exact: true })).toHaveValue(
    "Un cambio todavía pendiente.",
  );
  await page.goBack();
  await expect(page.locator("#approve-copy")).toHaveAttribute("aria-disabled", "true");
  await page.locator("#approve-copy").dispatchEvent("click");
  expect(
    await page.evaluate(() => (window as unknown as { copied?: string }).copied),
  ).toBeUndefined();
  await page.getByRole("button", { name: es["workspace.review.open.editor"], exact: true }).click();
  await expect(page.getByLabel(es["workspace.editor.text"], { exact: true })).toHaveValue(
    "Un cambio todavía pendiente.",
  );
  await page.getByRole("button", { name: es["workspace.editor.compare"], exact: true }).click();
  await page.locator("#cs-stop").click();
  await page
    .getByRole("button", { name: es["workspace.editor.apply"], exact: true })
    .dispatchEvent("click");
  await expect(page.locator(".editor-comparison")).toBeVisible();
  await page.locator("#workspace-resume").click();
  await page.getByRole("button", { name: es["workspace.editor.apply"], exact: true }).click();
  await expect(page.locator(".document-preview")).toHaveText(
    "Uno.\n\nUn cambio todavía pendiente.",
  );
});

test("numbered editor reaches later pages, adds and deletes text without losing other blocks", async ({
  page,
}) => {
  const original = Array.from({ length: 12 }, (_, index) => `Párrafo ${index + 1}.`).join("\n\n");
  await createTask(page, original);
  await page.getByRole("button", { name: es["workspace.editor.blocks"], exact: true }).click();
  await page.getByLabel(es["workspace.editor.jump"], { exact: true }).fill("99");
  await page.getByRole("button", { name: es["workspace.editor.show"], exact: true }).click();
  await expect(page.getByLabel(es["workspace.editor.jump"], { exact: true })).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await page.getByLabel(es["workspace.editor.jump"], { exact: true }).fill("12");
  await page.getByRole("button", { name: es["workspace.editor.show"], exact: true }).click();
  await expect(
    page.getByRole("button", { name: `${es["workspace.editor.select"]} 12`, exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: es["workspace.editor.insert"], exact: true }).click();
  await page.getByLabel(es["workspace.editor.text"], { exact: true }).fill("Un bloque nuevo.");
  await page.getByRole("button", { name: es["workspace.editor.compare"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.editor.apply"], exact: true }).click();
  await expect(page.locator(".document-preview")).toHaveText(`${original}\n\nUn bloque nuevo.`);
  await page.getByRole("button", { name: es["workspace.editor.blocks"], exact: true }).click();
  await page.getByLabel(es["workspace.editor.jump"], { exact: true }).fill("13");
  await page.getByRole("button", { name: es["workspace.editor.show"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.editor.delete"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.editor.compare"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.editor.apply"], exact: true }).click();
  await expect(page.locator(".document-preview")).toHaveText(`${original}\n\n`);
});

test("version recovery compares all fields and requires resuming a paused task", async ({
  page,
}) => {
  await createTask(page);
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await page.getByLabel(es["workspace.task.recipient"], { exact: true }).fill("otra@example.org");
  await page.getByLabel(es["workspace.task.subject"], { exact: true }).fill("Asunto corregido");
  await page
    .getByLabel(es["workspace.task.notes"], { exact: true })
    .fill("Segunda versión completa.");
  await page.getByRole("button", { name: es["workspace.task.save"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.versions.button"], exact: true }).click();
  await page
    .getByRole("button", { name: `${es["workspace.versions.show"]} 1`, exact: true })
    .click();
  await expect(page.locator(".editor-comparison > section").nth(0)).toContainText(
    "otra@example.org",
  );
  await expect(page.locator(".editor-comparison > section").nth(1)).toContainText(
    "persona@example.org",
  );
  await audit(page);
  await page.screenshot({ path: "test-results/stitch-versiones.png", fullPage: true });
  await page.locator("#cs-stop").click();
  await expect(
    page.getByRole("button", { name: es["workspace.versions.use"], exact: true }),
  ).toHaveAttribute("aria-disabled", "true");
  await page.locator("#workspace-resume").click();
  await page.getByRole("button", { name: es["workspace.versions.use"], exact: true }).click();
  await expect(page.locator(".document-preview")).toHaveText("Contenido privado de mi borrador.");
  await expect(page.getByText("persona@example.org", { exact: true })).toBeVisible();
  await expect(
    page.getByText(`${es["workspace.versions.current"]} 3`, { exact: true }),
  ).toBeVisible();
});

test("unknown routes show Spanish recovery with reachable safety controls", async ({ page }) => {
  const response = await page.goto("/pantalla-inexistente");
  expect(response?.status()).toBe(404);
  await expect(
    page.getByRole("heading", { name: es["workspace.recovery.missing.title"] }),
  ).toBeFocused();
  await page.screenshot({ path: "test-results/stitch-no-encontrada.png", fullPage: true });
  await audit(page);
  await page.locator("#workspace-contrast").click();
  await audit(page);
  await page.locator("#cs-help").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.locator("#cs-stop").click();
  await expect(page.getByText(es["workspace.stop.notice"], { exact: true })).toBeVisible();
  await page.getByRole("button", { name: es["workspace.close"], exact: true }).click();
  await page.getByRole("link", { name: es["workspace.recovery.home"], exact: true }).click();
  await expect(page.getByRole("heading", { name: es["workspace.home.title"] })).toBeVisible();
});

test("slow route navigation announces loading and retains the safety controls", async ({
  page,
}) => {
  let release = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(/\/logros\?/, async (route) => {
    await gate;
    await route.continue();
  });
  await page.goto("/inicio");
  const requested = page.waitForRequest(
    (request) => new URL(request.url()).pathname === "/logros" && request.headers().rsc === "1",
  );
  try {
    await page
      .getByRole("navigation")
      .getByRole("link", { name: es["workspace.nav.achievements"], exact: true })
      .click();
    await requested;
    await expect(
      page.getByText(es["workspace.recovery.loading.body"], { exact: true }),
    ).toBeVisible({ timeout: 3000 });
    await audit(page, 44, false);
    await expect(page.locator("#cs-stop")).toBeInViewport();
    await page.screenshot({ path: "test-results/stitch-cargando.png", fullPage: true });
  } finally {
    release();
  }
  await expect(
    page.getByRole("heading", { name: es["workspace.achievements.title"] }),
  ).toBeVisible();
});

test("Alto abandons slow navigation and keeps the current editor", async ({ page }) => {
  let release = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(/\/logros\?/, async (route) => {
    await gate;
    await route.continue();
  });
  await page.goto("/tareas/nueva");
  await page.getByLabel(es["workspace.task.title.label"]).fill("Mi tarea todavía abierta");
  await page
    .getByLabel(es["workspace.task.notes"], { exact: true })
    .fill("Mis notas no deben perderse.");
  const requested = page.waitForRequest(
    (request) => new URL(request.url()).pathname === "/logros" && request.headers().rsc === "1",
  );
  try {
    await page
      .getByRole("navigation")
      .getByRole("link", { name: es["workspace.nav.achievements"], exact: true })
      .click();
    await requested;
    await expect(
      page.getByText(es["workspace.recovery.loading.body"], { exact: true }),
    ).toBeVisible();
    await page.locator("#cs-stop").click();
    await expect(page.getByText(es["workspace.pause.label"], { exact: true })).toBeVisible();
  } finally {
    release();
  }
  await expect(page.locator(".navigation-notice")).toHaveCount(0);
  await expect(page).toHaveURL(/\/tareas\/nueva$/);
  await expect(page.getByLabel(es["workspace.task.notes"], { exact: true })).toHaveValue(
    "Mis notas no deben perderse.",
  );
});

test("a render error recovers the task and its unsaved editor without a full reload", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const Original = Intl.DateTimeFormat;
    Intl.DateTimeFormat = new Proxy(Original, {
      construct(target, args) {
        if ((window as unknown as { failDate?: boolean }).failDate)
          throw new Error("test-render-failure");
        return Reflect.construct(target, args);
      },
    });
  });
  await createTask(page);
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await page
    .getByLabel(es["workspace.task.notes"], { exact: true })
    .fill("Mi edición pendiente de guardar.");
  await page.evaluate(() => {
    (window as unknown as { failDate: boolean }).failDate = true;
  });
  await page.locator("#workspace-contrast").click();
  await expect(
    page.getByRole("heading", { name: es["workspace.recovery.error.title"] }),
  ).toBeFocused();
  await expect(page.getByText("test-render-failure", { exact: false })).toHaveCount(0);
  await audit(page);
  await page.screenshot({ path: "test-results/stitch-error.png", fullPage: true });
  await page.locator("#cs-stop").click();
  await page.evaluate(() => {
    (window as unknown as { failDate: boolean }).failDate = false;
  });
  await page.getByRole("button", { name: es["workspace.recovery.retry"], exact: true }).click();
  await expect(
    page.getByRole("heading", { name: es["workspace.task.progress.title"] }),
  ).toBeFocused();
  await expect(page.getByText(es["workspace.pause.label"], { exact: true })).toBeVisible();
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await expect(page.getByLabel(es["workspace.task.notes"], { exact: true })).toHaveValue(
    "Mi edición pendiente de guardar.",
  );
});

test("a layout failure closes camera tracks and offers independent safety controls", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const state = window as unknown as {
      failInert: boolean;
      stoppedTracks: number;
      cameraCalls: number;
    };
    state.failInert = false;
    state.stoppedTracks = 0;
    state.cameraCalls = 0;
    const setAttribute = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function (name, value) {
      if (name === "inert" && state.failInert) {
        state.failInert = false;
        throw new Error("test-layout-failure");
      }
      return setAttribute.call(this, name, value);
    };
    Object.defineProperty(navigator.mediaDevices, "getUserMedia", {
      configurable: true,
      value: async () => {
        state.cameraCalls += 1;
        const stream = new MediaStream();
        const track = {
          stop: () => {
            state.stoppedTracks += 1;
          },
        };
        Object.defineProperty(stream, "getTracks", { value: () => [track] });
        Object.defineProperty(stream, "getVideoTracks", { value: () => [track] });
        return stream;
      },
    });
  });
  await page.goto("/calibracion");
  await page
    .getByRole("button", { name: es["workspace.calibration.camera.start"], exact: true })
    .click();
  await expect(
    page.getByText(es["workspace.calibration.camera.active"], { exact: true }),
  ).toBeVisible();
  await page.evaluate(() => {
    (window as unknown as { failInert: boolean }).failInert = true;
  });
  await page.locator("#workspace-help").click();
  await expect(
    page.getByRole("heading", { name: es["workspace.recovery.root.title"] }),
  ).toBeFocused();
  await expect(page.getByText("test-layout-failure", { exact: false })).toHaveCount(0);
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { stoppedTracks: number }).stoppedTracks))
    .toBe(1);
  await audit(page, 64);
  await page.locator("#recovery-contrast").click();
  await audit(page, 64);
  await page.locator("#cs-help").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.locator("#cs-stop").click();
  await expect(page.getByText(es["workspace.recovery.root.stop"], { exact: true })).toBeVisible();
  await page.getByRole("button", { name: es["workspace.close"], exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await audit(page, 64);
  await page.screenshot({ path: "test-results/stitch-error-general.png", fullPage: true });
  await expect(
    page.getByRole("button", { name: es["workspace.recovery.retry"], exact: true }),
  ).toHaveAttribute("aria-disabled", "true");
  await page
    .getByRole("button", { name: es["workspace.recovery.root.enable"], exact: true })
    .click();
  await page.getByRole("button", { name: es["workspace.recovery.retry"], exact: true }).click();
  await expect(
    page.getByRole("heading", { name: es["workspace.calibration.title"] }),
  ).toBeFocused();
  await expect(
    page.getByText(es["workspace.calibration.no.camera"], { exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => (window as unknown as { cameraCalls: number }).cameraCalls),
  ).toBe(1);
});

test("large drafts keep exact text and reflow with head targets at 200 percent", async ({
  page,
}) => {
  const runtimeErrors: string[] = [];
  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  await mockClipboard(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/bienvenida");
  await page
    .locator(".mode-grid")
    .getByRole("button", { name: /Cabeza y gestos/ })
    .click();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: es["workspace.nav.tasks"], exact: true })
    .click();
  await page.getByRole("link", { name: es["workspace.achievements.start"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.task.document"], exact: true }).click();
  const body = "Árbol".repeat(10_000);
  await page.getByLabel(es["workspace.task.title.label"]).fill("Á".repeat(180));
  await page.getByLabel(es["workspace.task.notes"], { exact: true }).fill(body);
  await page.evaluate(() => document.documentElement.style.setProperty("font-size", "200%"));
  await page.getByRole("button", { name: es["workspace.task.prepare"], exact: true }).click();
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await audit(page, 64);
  await page.screenshot({ path: "test-results/stitch-reflujo-200.png", fullPage: false });
  await page.locator("#approve-copy").click();
  await expect(
    page.getByRole("heading", { name: es["workspace.achievements.title"] }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      (expected) => (window as unknown as { copied?: string }).copied === expected,
      body,
    ),
  ).toBe(true);
  await audit(page, 64);
  expect(runtimeErrors).toEqual([]);
});

test("seven Stitch screens complete by simulated selection and dictation without a pointer", async ({
  page,
}) => {
  await page.addInitScript(() => {
    addEventListener("cs:nav-targets", (event) => {
      (window as unknown as { targets: unknown }).targets = (event as CustomEvent).detail;
    });
  });
  await mockClipboard(page);
  await page.goto("/bienvenida");
  const select = async (label: string) => {
    await expect
      .poll(() =>
        page.evaluate(
          (name) =>
            (
              (window as unknown as { targets?: { label: string; disabled: boolean }[] }).targets ??
              []
            ).some((item) => item.label.startsWith(name) && !item.disabled),
          label,
        ),
      )
      .toBe(true);
    await page.evaluate((name) => {
      const targets = (
        window as unknown as { targets: { id: string; label: string; disabled: boolean }[] }
      ).targets;
      const target = targets.find((item) => item.label.startsWith(name) && !item.disabled);
      const element = target && document.getElementById(target.id);
      if (!element) throw new Error("Target unavailable");
      element.focus();
      element.click();
    }, label);
  };
  const dictate = async (text: string) => {
    await page.evaluate((value) => {
      const element = document.activeElement;
      if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement))
        throw new Error("Expected text field");
      const prototype =
        element instanceof HTMLTextAreaElement
          ? HTMLTextAreaElement.prototype
          : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(prototype, "value")?.set?.call(element, value);
      element.dispatchEvent(new Event("input", { bubbles: true }));
    }, text);
  };
  await select(es["workspace.keyboard"]);
  await select(es["workspace.welcome.start"]);
  await select(es["workspace.calibration.practice"]);
  await select(es["workspace.practice.prompt"]);
  await dictate("Una nota para practicar.");
  await select(es["workspace.practice.action"]);
  await select(es["workspace.practice.to.home"]);
  await select(es["workspace.task.document.start"]);
  await select(es["workspace.task.title.label"]);
  await dictate("Mis notas de trabajo");
  await select(es["workspace.task.notes"]);
  await dictate("Mis notas privadas de la reunión.");
  await select(es["workspace.task.prepare"]);
  await select(es["workspace.editor.blocks"]);
  await select(`${es["workspace.editor.select"]} 1`);
  await select(es["workspace.editor.text"]);
  await dictate("Mi versión revisada por bloques.");
  await select(es["workspace.editor.compare"]);
  await select(es["workspace.editor.apply"]);
  await select(es["workspace.task.review"]);
  await expect(page.getByRole("heading", { name: es["workspace.review.title"] })).toBeVisible();
  expect(
    await page.evaluate(() => JSON.stringify((window as unknown as { targets: unknown }).targets)),
  ).not.toContain("Mis notas privadas de la reunión.");
  expect(
    await page.evaluate(() => JSON.stringify((window as unknown as { targets: unknown }).targets)),
  ).not.toContain("Mi versión revisada por bloques.");
  await select(es["workspace.review.copy"]);
  await expect(
    page.getByRole("heading", { name: es["workspace.achievements.title"] }),
  ).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { copied?: string }).copied)).toBe(
    "Mi versión revisada por bloques.",
  );
  await select(es["stop.label"]);
  await expect(page.getByText(es["workspace.stop.notice"], { exact: true })).toBeVisible();
});

test("paused forms reject direct submission and retain text for resuming", async ({ page }) => {
  await page.goto("/tareas/nueva");
  await page.getByLabel(es["workspace.task.title.label"]).fill("Trabajo en pausa");
  await page.getByLabel(es["workspace.task.notes"], { exact: true }).fill("Texto que se conserva.");
  await page.locator("#cs-stop").click();
  await page.locator(".task-form").evaluate((form) => (form as HTMLFormElement).requestSubmit());
  await expect(page).toHaveURL(/\/tareas\/nueva$/);
  await expect(page.getByLabel(es["workspace.task.notes"], { exact: true })).toHaveValue(
    "Texto que se conserva.",
  );
  await page.locator("#workspace-resume").click();
  await page.getByRole("button", { name: es["workspace.task.prepare"], exact: true }).click();
  await expect(page.getByText("Texto que se conserva.", { exact: true })).toBeVisible();
});

test("missing draft body identifies and focuses the field without losing its title", async ({
  page,
}) => {
  await page.goto("/tareas/nueva");
  await page.getByLabel(es["workspace.task.title.label"]).fill("Título que conservo");
  await page.getByRole("button", { name: es["workspace.task.prepare"], exact: true }).click();
  const notes = page.getByLabel(es["workspace.task.notes"], { exact: true });
  await expect(notes).toBeFocused();
  await expect(notes).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByLabel(es["workspace.task.title.label"])).toHaveValue(
    "Título que conservo",
  );
  await audit(page);
});

test("offline editing preserves the current draft without reload or network", async ({
  page,
  context,
}) => {
  await createTask(page);
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await context.setOffline(true);
  await expect(page.getByText(es["workspace.offline"], { exact: true })).toBeVisible();
  await page
    .getByLabel(es["workspace.task.notes"], { exact: true })
    .fill("Mi texto sigue aquí sin conexión.");
  await page.getByRole("button", { name: es["workspace.task.save"], exact: true }).click();
  await expect(page.getByText("Mi texto sigue aquí sin conexión.", { exact: true })).toBeVisible();
  await context.setOffline(false);
});

test("selected blocks read with a local voice, pause and resume; completion and Alto retain usable focus", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const state = window as unknown as {
      spoken: string[];
      pauses: number;
      resumes: number;
      cancelled: number;
      endReading: () => void;
    };
    state.spoken = [];
    state.pauses = 0;
    state.resumes = 0;
    state.cancelled = 0;
    Object.defineProperty(window, "SpeechSynthesisUtterance", {
      configurable: true,
      value: class {
        text: string;
        constructor(text: string) {
          this.text = text;
        }
      },
    });
    Object.defineProperty(window, "speechSynthesis", {
      configurable: true,
      value: {
        getVoices: () => [{ voiceURI: "test-local", lang: "es-EC", localService: true }],
        addEventListener: () => {},
        removeEventListener: () => {},
        cancel: () => {
          state.cancelled += 1;
        },
        pause: () => {
          state.pauses += 1;
        },
        resume: () => {
          state.resumes += 1;
        },
        speak: (utterance: {
          text: string;
          voice: { localService: boolean };
          onend?: () => void;
        }) => {
          if (!utterance.voice.localService) throw new Error("Remote voice");
          state.spoken.push(utterance.text);
          state.endReading = () => utterance.onend?.();
        },
      },
    });
  });
  await createTask(page, "Uno.\n\nDos.");
  await page.getByRole("button", { name: es["workspace.editor.blocks"], exact: true }).click();
  await page
    .getByRole("button", { name: `${es["workspace.editor.select"]} 2`, exact: true })
    .click();
  const read = page.getByRole("button", { name: es["workspace.audio.read"], exact: true });
  await read.click();
  await page.getByRole("button", { name: es["workspace.audio.pause"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.audio.resume"], exact: true }).click();
  expect(
    await page.evaluate(() => ({
      pauses: (window as unknown as { pauses: number }).pauses,
      resumes: (window as unknown as { resumes: number }).resumes,
    })),
  ).toEqual({ pauses: 1, resumes: 1 });
  await page.evaluate(() => (window as unknown as { endReading: () => void }).endReading());
  await expect(read).toBeFocused();
  await read.click();
  await page
    .getByRole("button", { name: `${es["workspace.editor.select"]} 1`, exact: true })
    .click();
  await read.click();
  expect(await page.evaluate(() => (window as unknown as { spoken: string[] }).spoken.at(-1))).toBe(
    "Uno.",
  );
  await page.locator("#cs-stop").click();
  await expect(read).toHaveAttribute("aria-disabled", "true");
  await expect(
    page.getByRole("button", { name: es["workspace.audio.resume"], exact: true }),
  ).toHaveCount(0);
  expect(
    await page.evaluate(() => (window as unknown as { cancelled: number }).cancelled),
  ).toBeGreaterThanOrEqual(2);
  await audit(page);
});

for (const local of [true, false]) {
  test(`speech uses only a Spanish local voice: local=${local}`, async ({ page }) => {
    await page.addInitScript((isLocal) => {
      const state = window as unknown as {
        spoken: { text: string; local: boolean }[];
        cancellations: number;
      };
      state.spoken = [];
      state.cancellations = 0;
      Object.defineProperty(window, "SpeechSynthesisUtterance", {
        configurable: true,
        value: class {
          text: string;
          voice?: { localService: boolean };
          constructor(text: string) {
            this.text = text;
          }
        },
      });
      Object.defineProperty(window, "speechSynthesis", {
        configurable: true,
        value: {
          getVoices: () => [{ voiceURI: "test-es", lang: "es-EC", localService: isLocal }],
          addEventListener: () => {},
          removeEventListener: () => {},
          cancel: () => {
            state.cancellations += 1;
          },
          speak: (utterance: { text: string; voice: { localService: boolean } }) =>
            state.spoken.push({ text: utterance.text, local: utterance.voice.localService }),
        },
      });
    }, local);
    await createTask(page);
    const read = page.getByRole("button", { name: es["workspace.audio.read"], exact: true });
    if (local) {
      await read.click();
      expect(
        await page.evaluate(() => (window as unknown as { spoken: unknown[] }).spoken),
      ).toEqual([{ text: "Contenido privado de mi borrador.", local: true }]);
      await page.locator("#cs-stop").click();
      await expect(read).toBeVisible();
    } else {
      await expect(read).toHaveAttribute("aria-disabled", "true");
      expect(
        await page.evaluate(() => (window as unknown as { spoken: unknown[] }).spoken),
      ).toEqual([]);
    }
  });
}
async function mockClipboard(page: Page) {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (text: string) => {
          (window as unknown as { copied: string }).copied = text;
        },
      },
    });
  });
}

test("prepare, review, edit and approve a local copy without any external transmission", async ({
  page,
}) => {
  await mockClipboard(page);
  const external: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).hostname !== "127.0.0.1") external.push(request.url());
  });
  await createTask(page);
  await audit(page);
  await page.screenshot({ path: "test-results/stitch-tarea.png", fullPage: true });
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await page
    .getByLabel(es["workspace.task.notes"], { exact: true })
    .fill("Texto corregido y revisado por mí.");
  await page.getByRole("button", { name: es["workspace.task.save"], exact: true }).click();
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await audit(page);
  await page.screenshot({ path: "test-results/stitch-revision.png", fullPage: true });
  await expect(page.locator("#approve-send")).toHaveAttribute("aria-disabled", "true");
  await page.locator("#approve-send").dispatchEvent("click");
  expect(
    await page.evaluate(() => (window as unknown as { copied?: string }).copied),
  ).toBeUndefined();
  await page.locator("#approve-copy").click();
  await expect(
    page.getByRole("heading", { name: es["workspace.achievements.title"] }),
  ).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { copied?: string }).copied)).toBe(
    "Destinatario: persona@example.org\nAsunto: Notas de la reunión\n\nTexto corregido y revisado por mí.",
  );
  await expect(page.getByRole("heading", { name: "Seguimiento profesional" })).toBeVisible();
  expect(external).toEqual([]);
  expect(
    await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length })),
  ).toEqual({ local: 0, session: 0 });
  await expect(page.locator("#cs-undo")).toHaveAttribute("aria-disabled", "true");
  const downloadEvent = page.waitForEvent("download");
  await page
    .getByRole("button", { name: es["workspace.achievements.export"], exact: true })
    .click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe("coalsense-logros.txt");
  const file = await download.path();
  if (!file) throw new Error("Download unavailable");
  const exported = await readFile(file, "utf8");
  expect(exported).toContain("Seguimiento profesional");
  expect(exported).not.toContain("Texto corregido y revisado por mí.");
  await expect(page.locator(".achievement-row")).toHaveCount(1);
  await page
    .getByRole("button", { name: `${es["workspace.achievements.inspect"]} 1`, exact: true })
    .click();
  const detail = page.getByRole("dialog");
  await expect(
    detail.getByText(es["workspace.achievements.detail.body"], { exact: true }),
  ).toBeVisible();
  await expect(detail.getByText("Seguimiento profesional", { exact: true })).toBeVisible();
  await expect(page.locator("#cs-stop")).toBeInViewport();
  await page.getByRole("button", { name: es["workspace.close"], exact: true }).click();
  await expect(detail).toHaveCount(0);
  await audit(page);
});

test("keyboard focus in a mobile editor stays above the safety bars", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/tareas/nueva");
  await page.getByRole("heading", { level: 1 }).focus();
  for (let index = 0; index < 14; index += 1) {
    await page.keyboard.press("Tab");
    const covered = await page.evaluate(() => {
      const active = document.activeElement;
      if (!(active instanceof HTMLElement) || !active.closest(".workspace-main")) return null;
      const strip = document.querySelector(".workspace-input-strip")?.getBoundingClientRect();
      const bounds = active.getBoundingClientRect();
      return strip && (bounds.bottom > strip.top + 1 || bounds.top < -1)
        ? { tag: active.tagName, top: bounds.top, bottom: bounds.bottom, available: strip.top }
        : null;
    });
    expect(covered).toBeNull();
  }
});

test("changing task kind preserves writing and review opens the editor directly", async ({
  page,
}) => {
  await page.goto("/tareas/nueva");
  await page.getByLabel(es["workspace.task.title.label"]).fill("Mi documento");
  await page.getByLabel(es["workspace.task.notes"], { exact: true }).fill("Conserva mis palabras.");
  await page.getByRole("button", { name: es["workspace.task.document"], exact: true }).click();
  await expect(page.getByLabel(es["workspace.task.notes"], { exact: true })).toHaveValue(
    "Conserva mis palabras.",
  );
  await page.getByRole("button", { name: es["workspace.task.prepare"], exact: true }).click();
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).first().click();
  await expect(page.getByLabel(es["workspace.task.notes"], { exact: true })).toHaveValue(
    "Conserva mis palabras.",
  );
  await expect(page.getByLabel(es["workspace.task.title.label"])).toHaveValue("Mi documento");
});

test("unsaved editor text survives visiting settings within the workspace", async ({ page }) => {
  await createTask(page);
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await page
    .getByLabel(es["workspace.task.notes"], { exact: true })
    .fill("Cambio todavía sin guardar.");
  await page
    .getByRole("navigation")
    .getByRole("link", { name: es["workspace.nav.settings"], exact: true })
    .click();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: es["workspace.nav.tasks"], exact: true })
    .click();
  await page.getByRole("link", { name: `${es["workspace.task.open"]} 1`, exact: true }).click();
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await expect(page.getByLabel(es["workspace.task.notes"], { exact: true })).toHaveValue(
    "Cambio todavía sin guardar.",
  );
  await page.getByRole("button", { name: es["workspace.task.save"], exact: true }).click();
  await expect(page.getByText("Cambio todavía sin guardar.", { exact: true })).toBeVisible();
  await page.locator("#cs-undo").click();
  await expect(page.getByText("Contenido privado de mi borrador.", { exact: true })).toBeVisible();
});

test("Undo removes practice success while keeping the editable note", async ({ page }) => {
  await page.goto("/primera-tarea");
  await page.getByLabel(es["workspace.practice.prompt"], { exact: true }).fill("Mi primera nota.");
  await page.getByRole("button", { name: es["workspace.practice.action"], exact: true }).click();
  await expect(page.getByRole("heading", { name: es["workspace.practice.success"] })).toBeVisible();
  await page.locator("#cs-undo").click();
  await expect(page.getByRole("heading", { name: es["workspace.practice.success"] })).toHaveCount(
    0,
  );
  await expect(page.getByLabel(es["workspace.practice.prompt"], { exact: true })).toHaveValue(
    "Mi primera nota.",
  );
});

test("Alto pauses decisions, Undo reverses edits, deferred review does not expire", async ({
  page,
}) => {
  await mockClipboard(page);
  await createTask(page);
  await page.getByRole("button", { name: es["workspace.task.edit"], exact: true }).click();
  await page
    .getByLabel(es["workspace.task.notes"], { exact: true })
    .fill("Un cambio que puedo deshacer.");
  await page.getByRole("button", { name: es["workspace.task.save"], exact: true }).click();
  await page.locator("#cs-stop").click();
  await page.locator("#cs-undo").click();
  await expect(page.getByText("Contenido privado de mi borrador.", { exact: true })).toBeVisible();
  await expect(page.getByText(es["workspace.pause.label"], { exact: true })).toBeVisible();
  await page.locator("#workspace-resume").click();
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await page.getByRole("link", { name: es["workspace.review.defer"], exact: true }).click();
  await expect(page.getByText(es["workspace.task.review.status"], { exact: true })).toBeVisible();
  await audit(page);
});

test("clipboard failure never records an achievement or sends content", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => {
          throw new Error("blocked");
        },
      },
    });
  });
  await createTask(page);
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await page.locator("#approve-copy").click();
  await expect(page.getByText(es["workspace.review.copy.failed"], { exact: true })).toBeVisible();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: es["workspace.nav.achievements"], exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: es["workspace.achievements.empty"] }),
  ).toBeVisible();
});

test("Alto during a pending copy records no achievement and never retries", async ({ page }) => {
  await page.addInitScript(() => {
    const state = window as unknown as { copyCalls: number; finishCopy: () => void };
    state.copyCalls = 0;
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: () => {
          state.copyCalls += 1;
          return new Promise<void>((resolve) => {
            state.finishCopy = resolve;
          });
        },
      },
    });
  });
  await createTask(page);
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await page.locator("#approve-copy").click();
  await page.locator("#cs-stop").click();
  await page.evaluate(() => (window as unknown as { finishCopy: () => void }).finishCopy());
  await expect(page.getByText(es["workspace.review.cancel.wait"], { exact: true })).toBeVisible();
  await page.locator("#approve-copy").dispatchEvent("click");
  expect(await page.evaluate(() => (window as unknown as { copyCalls: number }).copyCalls)).toBe(1);
  await page
    .getByRole("navigation")
    .getByRole("link", { name: es["workspace.nav.achievements"], exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: es["workspace.achievements.empty"] }),
  ).toBeVisible();
  await expect(page.locator("#cs-undo")).toHaveAttribute("aria-disabled", "true");
});

test("a pending copy cannot navigate away from the screen the person chose", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: () =>
          new Promise<void>((resolve) => {
            (window as unknown as { finishCopy: () => void }).finishCopy = resolve;
          }),
      },
    });
  });
  await createTask(page);
  await page.getByRole("link", { name: es["workspace.task.review"], exact: true }).click();
  await page.locator("#approve-copy").click();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: es["workspace.nav.settings"], exact: true })
    .click();
  await expect(page).toHaveURL(/\/ajustes$/);
  await page.evaluate(() => (window as unknown as { finishCopy: () => void }).finishCopy());
  await expect(page.getByText(es["workspace.review.copy.done"], { exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/ajustes$/);
});

test("Alto during camera permission cancels late media and no capture starts automatically", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const state = window as unknown as {
      cameraCalls: number;
      stoppedTracks: number;
      resolveCamera: () => void;
    };
    state.cameraCalls = 0;
    state.stoppedTracks = 0;
    Object.defineProperty(navigator.mediaDevices, "getUserMedia", {
      configurable: true,
      value: () => {
        state.cameraCalls += 1;
        return new Promise((resolve) => {
          state.resolveCamera = () => {
            const stream = new MediaStream();
            Object.defineProperty(stream, "getTracks", {
              value: () => [
                {
                  stop: () => {
                    state.stoppedTracks += 1;
                  },
                },
              ],
            });
            resolve(stream);
          };
        });
      },
    });
  });
  await page.goto("/calibracion");
  expect(
    await page.evaluate(() => (window as unknown as { cameraCalls: number }).cameraCalls),
  ).toBe(0);
  await page
    .getByRole("button", { name: es["workspace.calibration.camera.start"], exact: true })
    .click();
  await page.locator("#cs-stop").click();
  await page.evaluate(() => (window as unknown as { resolveCamera: () => void }).resolveCamera());
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { stoppedTracks: number }).stoppedTracks))
    .toBe(1);
  await expect(
    page.getByText(es["workspace.calibration.no.camera"], { exact: true }),
  ).toBeVisible();
  await audit(page);
});

test("mobile, enlarged text and head targets keep safety controls visible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/bienvenida");
  await page
    .locator(".mode-grid")
    .getByRole("button", { name: /Cabeza y gestos/ })
    .click();
  await audit(page, 64);
  await page
    .getByRole("navigation")
    .getByRole("link", { name: es["workspace.nav.settings"], exact: true })
    .click();
  await page
    .getByRole("button", { name: es["workspace.settings.text.large"], exact: true })
    .click();
  await page.evaluate(() => document.documentElement.style.setProperty("font-size", "200%"));
  await audit(page, 64);
  await page.locator("#cs-help").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator("#cs-stop")).toBeInViewport();
  await page.locator("#cs-stop").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText(es["workspace.stop.notice"], { exact: true })).toBeVisible();
});
