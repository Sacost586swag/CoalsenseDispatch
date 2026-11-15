// T-00-014 (a11y): axe-core per component and state, accessible name contains the visible label,
// nothing disappears without an action. jsdom computes no layout: target size is checked on the
// stylesheet and class wiring here; the geometric 44x44 measurement arrives in T-00-017 (Playwright).
// color-contrast is the only axe rule turned off: jsdom has no rendering, and T-00-013 already
// proves the token pairs.
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render as rtlRender, screen } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { userEvent } from "@testing-library/user-event";
import axe from "axe-core";
import {
  Button,
  Dialog,
  Link,
  NumberedList,
  Progress,
  StatusBanner,
  Stepper,
  TextField,
  STOP_BAR_ATTRIBUTE,
} from "../src/components/index.ts";
import { defaultTheme, highContrast, reducedMotion, es } from "../src/index.ts";

// A screen supplies its own landmarks (T-00-015+); components are tested inside one <main> so the
// page-level axe "region" rule keeps running instead of being switched off.
const render = (ui: ReactElement) =>
  rtlRender(ui, { wrapper: ({ children }: { children: ReactNode }) => <main>{children}</main> });

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

async function violations(node: Element = document.body): Promise<string[]> {
  const result = await axe.run(node, { rules: { "color-contrast": { enabled: false } } });
  return result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(" | ")}`);
}

/** WCAG 2.5.3: the accessible name must contain the visible text. */
const nameContains =
  (visible: string) =>
  (name: string): boolean =>
    name.includes(visible);

// Vitest runs from the package directory (turbo and pnpm both set it).
const componentsDir = join(process.cwd(), "src", "components");
const EIGHT_HOURS = 8 * 60 * 60 * 1000;
const css = readFileSync(join(componentsDir, "components.css"), "utf8").replace(
  /\/\*[\s\S]*?\*\//g,
  "",
);
/** Declarations of every rule whose selector list contains exactly `selector`. */
const rule = (selector: string): string =>
  [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)]
    .filter(([, list]) => list?.split(",").some((s) => s.trim() === selector))
    .map(([, , body]) => body)
    .join(" ");

describe("harness", () => {
  it("axe really reports a control without an accessible name", async () => {
    render(<button type="button" />);
    expect((await violations()).join()).toContain("button-name");
  });
});

describe("stylesheet (no hard-coded values, targets, focus, motion)", () => {
  it("uses only token variables: no colors or pixel sizes in duro", () => {
    expect(css).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(css).not.toMatch(/\brgba?\(|\bhsla?\(/);
    expect(css).not.toMatch(/\d+(\.\d+)?px/);
  });

  it("every interactive class has min-width and min-height of var(--target-min)", () => {
    for (const selector of [".cs-button", ".cs-link", ".cs-input"]) {
      const body = rule(selector);
      expect(body, selector).toMatch(/min-height:\s*var\(--target-min\)/);
      expect(body, selector).toMatch(/min-width:\s*var\(--target-min\)/);
    }
    expect(css).toMatch(/data-input-mode="head"\][^{]*\{[^}]*var\(--target-head\)/);
  });

  it("the token floor never drops below 44 and gaps below 16", () => {
    for (const theme of [defaultTheme, highContrast, reducedMotion]) {
      expect(theme.target.min).toBeGreaterThanOrEqual(44);
      expect(theme.target.head).toBeGreaterThanOrEqual(44);
      expect(theme.target.gap).toBeGreaterThanOrEqual(16);
    }
    expect(css).toMatch(/gap:\s*var\(--target-gap\)/);
  });

  it("focus ring is 3 px token, always visible and never removed", () => {
    expect(css).toMatch(
      /:focus-visible[^{]*\{[^}]*outline:\s*var\(--ring-width\)\s+solid\s+var\(--color-ring\)/,
    );
    expect(css).not.toMatch(/outline(-width)?:\s*(none|0)\b/);
    expect(defaultTheme.ring.width).toBe(3);
  });

  it("has active states and nothing behind hover", () => {
    expect(css).toMatch(/\.cs-button:active/);
    expect(css).toMatch(/\.cs-link:active/);
    expect(css).not.toMatch(/:hover/);
  });

  it("pressing never changes a control's size", () => {
    for (const selector of [".cs-button:active", ".cs-link:active", ".cs-input:active"]) {
      expect(rule(selector), selector).not.toMatch(
        /(^|[;\s])(border|border-width|padding[\w-]*|margin[\w-]*|(min-|max-)?(width|height)|font[\w-]*):/,
      );
    }
  });

  it("disabled controls are styled by aria-disabled, never by the native attribute", () => {
    expect(css).toMatch(/\.cs-button\[aria-disabled="true"\]/);
    expect(css).not.toMatch(/:disabled/);
  });

  it("motion is opacity only, token duration, no keyframes", () => {
    expect(css).not.toMatch(/@keyframes|animation/);
    for (const [, value] of css.matchAll(/transition:([^;]*);/g)) {
      expect(value).toMatch(/^\s*opacity\s+var\(--motion-duration\)\s*$/);
    }
  });

  it("the dialog backdrop leaves the Alto/Undo bar uncovered and documents its layers", () => {
    expect(rule(".cs-dialog__backdrop")).toMatch(/bottom:\s*var\(--stop-bar-reserved/);
    expect(css).toMatch(/--layer-stop-bar/);
    expect(css).toMatch(/--layer-dialog/);
  });
});

describe("no component can time out on its own", () => {
  it("sources contain no timers or animation frames", () => {
    for (const name of readdirSync(componentsDir).filter((n) => n.endsWith(".tsx"))) {
      const source = readFileSync(join(componentsDir, name), "utf8");
      expect(source, name).not.toMatch(/setTimeout|setInterval|requestAnimationFrame|Date\.now/);
    }
  });
});

describe("Button", () => {
  it.each([
    ["normal", {}],
    ["disabled", { disabled: true }],
    ["loading", { loading: true }],
  ])("%s passes axe and keeps the visible label in the name", async (_state, props) => {
    render(<Button {...props}>Guardar</Button>);
    const button = screen.getByRole("button", { name: nameContains("Guardar") });
    expect(button.className).toContain("cs-button");
    expect(button.hasAttribute("aria-label")).toBe(false);
    expect(await violations()).toEqual([]);
  });

  it("loading shows the catalog text, is busy, announces politely and ignores activation", async () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Guardar
      </Button>,
    );
    const button = screen.getByRole("button", { name: nameContains("Guardar") });
    expect(button.getAttribute("aria-busy")).toBe("true");
    expect(button.getAttribute("aria-disabled")).toBe("true");
    expect(button.textContent).toContain(es["state.loading.label"]);
    expect(screen.getByRole("status").textContent).toBe(es["state.loading.label"]);
    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("a loading submit button never submits the form, by click or Enter", async () => {
    const onSubmit = vi.fn((event: { preventDefault: () => void }) => event.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <input aria-label="campo" />
        <Button type="submit" loading>
          Enviar
        </Button>
      </form>,
    );
    await userEvent.click(screen.getByRole("button", { name: nameContains("Enviar") }));
    screen.getByRole("button", { name: nameContains("Enviar") }).focus();
    await userEvent.keyboard("{Enter}");
    await userEvent.click(screen.getByRole("textbox"));
    await userEvent.keyboard("{Enter}");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("an idle submit button still submits", async () => {
    const onSubmit = vi.fn((event: { preventDefault: () => void }) => event.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <Button type="submit">Enviar</Button>
      </form>,
    );
    await userEvent.click(screen.getByRole("button", { name: nameContains("Enviar") }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("activates with click and keyboard, defaults to type=button, has no tooltip", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Aprobar</Button>);
    const button = screen.getByRole("button", { name: nameContains("Aprobar") });
    expect(button.getAttribute("type")).toBe("button");
    expect(button.hasAttribute("title")).toBe(false);
    await userEvent.click(button);
    button.focus();
    await userEvent.keyboard("{Enter}");
    await userEvent.keyboard(" ");
    expect(onClick).toHaveBeenCalledTimes(3);
  });

  it("disabled stays focusable, does not activate or submit, and says why", async () => {
    const onClick = vi.fn();
    const onSubmit = vi.fn((event: { preventDefault: () => void }) => event.preventDefault());
    render(
      <form onSubmit={onSubmit}>
        <Button
          type="submit"
          disabled
          disabledReason="state.offline.message"
          variant="stop"
          onClick={onClick}
        >
          Alto
        </Button>
      </form>,
    );
    const button = screen.getByRole("button", { name: nameContains("Alto") });
    expect(button.className).toContain("cs-button--stop");
    expect(button.getAttribute("aria-disabled")).toBe("true");
    expect(button.hasAttribute("disabled")).toBe(false);
    await userEvent.tab();
    expect(document.activeElement).toBe(button);
    await userEvent.click(button);
    await userEvent.keyboard("{Enter}");
    expect(onClick).not.toHaveBeenCalled();
    expect(onSubmit).not.toHaveBeenCalled();
    const reason = document.getElementById(button.getAttribute("aria-describedby") ?? "");
    expect(reason?.textContent).toBe(es["state.offline.message"]);
    expect(await violations()).toEqual([]);
  });
});

describe("Link", () => {
  it.each([
    ["normal", { href: "/ayuda" }],
    ["disabled", { href: "/ayuda", disabled: true }],
  ])("%s passes axe; the name is the visible text", async (_state, props) => {
    render(<Link {...props}>Ver ayuda</Link>);
    const link = screen.getByRole("link", { name: nameContains("Ver ayuda") });
    expect(link.className).toContain("cs-link");
    expect(await violations()).toEqual([]);
  });

  it("a disabled link is focusable, has no destination, ignores onClick and says why", async () => {
    const onClick = vi.fn();
    render(
      <Link href="/ayuda" disabled disabledReason="state.offline.message" onClick={onClick}>
        Ver ayuda
      </Link>,
    );
    const link = screen.getByRole("link", { name: nameContains("Ver ayuda") });
    expect(link.getAttribute("aria-disabled")).toBe("true");
    expect(link.hasAttribute("href")).toBe(false);
    await userEvent.tab();
    expect(document.activeElement).toBe(link);
    await userEvent.click(link);
    await userEvent.keyboard("{Enter}");
    expect(onClick).not.toHaveBeenCalled();
    const reason = document.getElementById(link.getAttribute("aria-describedby") ?? "");
    expect(reason?.textContent).toBe(es["state.offline.message"]);
  });

  it("an enabled link still calls onClick", async () => {
    const onClick = vi.fn((event: { preventDefault: () => void }) => event.preventDefault());
    render(
      <Link href="/ayuda" onClick={onClick}>
        Ver ayuda
      </Link>,
    );
    await userEvent.click(screen.getByRole("link"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});

describe("TextField", () => {
  it.each([
    ["normal", {}],
    ["hint", { hint: "Solo letras" }],
    ["error", { error: "Falta el nombre" }],
    ["disabled", { disabled: true }],
  ])("%s passes axe; the label names the field", async (_state, props) => {
    render(<TextField label="Nombre" {...props} />);
    const input = screen.getByRole("textbox", { name: nameContains("Nombre") });
    expect(input.className).toContain("cs-input");
    expect(await violations()).toEqual([]);
  });

  it("disabled stays focusable, cannot be edited and says why", async () => {
    render(
      <TextField
        label="Nombre"
        disabled
        disabledReason="state.offline.message"
        aria-describedby="externo"
        defaultValue="Ana"
      />,
    );
    const input = screen.getByRole("textbox", { name: nameContains("Nombre") }) as HTMLInputElement;
    expect(input.getAttribute("aria-disabled")).toBe("true");
    expect(input.hasAttribute("disabled")).toBe(false);
    await userEvent.tab();
    expect(document.activeElement).toBe(input);
    await userEvent.keyboard("xyz");
    expect(input.value).toBe("Ana");
    const ids = (input.getAttribute("aria-describedby") ?? "").split(" ");
    expect(ids).toContain("externo");
    const reason = ids.map((id) => document.getElementById(id)).find((n) => n?.textContent);
    expect(reason?.textContent).toBe(es["state.offline.message"]);
  });

  it("an error message appears in a polite live region", () => {
    render(<TextField label="Nombre" error="Falta el nombre" />);
    expect(screen.getByRole("status").textContent).toContain("Falta el nombre");
  });

  it("error is linked, flagged invalid and not conveyed by color alone", () => {
    render(<TextField label="Nombre" error="Falta el nombre" />);
    const input = screen.getByRole("textbox", { name: nameContains("Nombre") });
    expect(input.getAttribute("aria-invalid")).toBe("true");
    const message = document.getElementById(input.getAttribute("aria-describedby") ?? "");
    expect(message?.textContent).toContain(es["state.error.label"]);
    expect(message?.textContent).toContain("Falta el nombre");
  });

  it("typing works and the label focuses the field", async () => {
    render(<TextField label="Nombre" />);
    await userEvent.click(screen.getByText("Nombre"));
    await userEvent.keyboard("Ana");
    expect((screen.getByRole("textbox") as HTMLInputElement).value).toBe("Ana");
  });
});

describe("Dialog", () => {
  const open = (extra: Partial<Parameters<typeof Dialog>[0]> = {}) => (
    <>
      <div {...{ [STOP_BAR_ATTRIBUTE]: "" }}>
        <button type="button">Alto</button>
        <button type="button">Deshacer</button>
      </div>
      <Dialog
        open
        title="Enviar correo"
        actions={
          <>
            <Button>Aprobar</Button>
            <Button>Rechazar</Button>
          </>
        }
        {...extra}
      >
        Se enviará a Ana.
      </Dialog>
    </>
  );

  it("renders nothing while closed", () => {
    render(
      <Dialog open={false} title="Enviar correo" actions={<Button>Aprobar</Button>}>
        Texto
      </Dialog>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("open dialog passes axe and is named by its title; no aria-modal (it would hide the bar)", async () => {
    render(open());
    const dialog = screen.getByRole("dialog", { name: nameContains("Enviar correo") });
    expect(dialog.hasAttribute("aria-modal")).toBe(false);
    expect(await violations()).toEqual([]);
  });

  it("makes the rest of the page inert except the dialog and the Alto/Deshacer bar", () => {
    const page = (isOpen: boolean) => (
      <>
        <p>Contenido de la pantalla</p>
        {open({ open: isOpen })}
      </>
    );
    const { rerender } = render(page(true));
    expect(screen.getByText("Contenido de la pantalla").hasAttribute("inert")).toBe(true);
    // The bar, its buttons and every ancestor up to the document are not inert.
    const bar = document.querySelector(`[${STOP_BAR_ATTRIBUTE}]`) as HTMLElement;
    for (let node: Element | null = bar; node; node = node.parentElement) {
      expect(node.hasAttribute("inert"), node.outerHTML.slice(0, 60)).toBe(false);
    }
    expect(document.querySelector(".cs-dialog__backdrop")?.hasAttribute("inert")).toBe(false);
    rerender(page(false));
    expect(document.querySelectorAll("[inert]")).toHaveLength(0);
  });

  it("keeps a sibling that was already inert after closing", () => {
    const page = (isOpen: boolean) => (
      <>
        <p inert>Ya inerte</p>
        {open({ open: isOpen })}
      </>
    );
    const { rerender } = render(page(true));
    rerender(page(false));
    expect(screen.getByText("Ya inerte").hasAttribute("inert")).toBe(true);
  });

  it("restores the page when the dialog unmounts", () => {
    const { unmount } = render(
      <>
        <p>Contenido de la pantalla</p>
        {open()}
      </>,
    );
    expect(document.querySelectorAll("[inert]").length).toBeGreaterThan(0);
    unmount();
    expect(document.querySelectorAll("[inert]")).toHaveLength(0);
  });

  it("moves focus inside, traps Tab and keeps the Alto/Deshacer bar reachable", async () => {
    render(open());
    const dialog = screen.getByRole("dialog");
    await act(async () => undefined);
    expect(dialog.contains(document.activeElement)).toBe(true);
    const visited = new Set<string>();
    for (let i = 0; i < 8; i++) {
      await userEvent.tab();
      visited.add(document.activeElement?.textContent ?? "");
      const insideDialog = dialog.contains(document.activeElement);
      const insideBar = document.activeElement?.closest(`[${STOP_BAR_ATTRIBUTE}]`) != null;
      expect(
        insideDialog || insideBar,
        `focus escaped to ${document.activeElement?.outerHTML}`,
      ).toBe(true);
    }
    expect(visited).toEqual(new Set(["Aprobar", "Rechazar", "Alto", "Deshacer"]));
    for (let i = 0; i < 8; i++) {
      await userEvent.tab({ shift: true });
      const insideDialog = dialog.contains(document.activeElement);
      const insideBar = document.activeElement?.closest(`[${STOP_BAR_ATTRIBUTE}]`) != null;
      expect(insideDialog || insideBar).toBe(true);
    }
  });

  it("Escape closes only when the person asked for it", async () => {
    const onClose = vi.fn();
    const { rerender } = render(open({ onClose }));
    await userEvent.keyboard("{Escape}");
    expect(onClose).not.toHaveBeenCalled();
    rerender(open({ onClose, closeOnEscape: true }));
    await userEvent.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("a click on the backdrop never closes it", async () => {
    const onClose = vi.fn();
    render(open({ onClose, closeOnEscape: true }));
    const backdrop = document.querySelector(".cs-dialog__backdrop");
    expect(backdrop).not.toBeNull();
    await userEvent.click(backdrop as Element);
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("returns focus to the opener when it closes by prop", async () => {
    function Host({ isOpen }: { isOpen: boolean }) {
      return (
        <>
          <button type="button">Abrir</button>
          <Dialog open={isOpen} title="Enviar correo" actions={<Button>Aprobar</Button>}>
            Texto
          </Dialog>
        </>
      );
    }
    const { rerender } = render(<Host isOpen={false} />);
    screen.getByRole("button", { name: "Abrir" }).focus();
    rerender(<Host isOpen />);
    await act(async () => undefined);
    rerender(<Host isOpen={false} />);
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Abrir" }));
  });

  it("stays open for hours without any action", () => {
    vi.useFakeTimers();
    render(open());
    act(() => vi.advanceTimersByTime(EIGHT_HOURS));
    expect(screen.getByRole("dialog")).toBeTruthy();
  });
});

describe("NumberedList", () => {
  it("passes axe, shows the numbers on screen and exposes list semantics", async () => {
    render(
      <NumberedList
        aria-label="Opciones"
        items={[
          { key: "a", content: "Revisar correo" },
          { key: "b", content: "Responder a Ana" },
          { key: "c", content: "Archivar" },
        ]}
      />,
    );
    const list = screen.getByRole("list", { name: nameContains("Opciones") });
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
    expect(list.textContent).toMatch(/1.*Revisar correo.*2.*Responder a Ana.*3.*Archivar/s);
    expect(await violations()).toEqual([]);
  });
});

describe("Progress", () => {
  it.each([
    ["determinate", { value: 40 }],
    ["indeterminate", {}],
  ])("%s passes axe and is named by the visible label", async (_state, props) => {
    render(<Progress label="Subiendo archivo" {...props} />);
    const bar = screen.getByRole("progressbar", { name: nameContains("Subiendo archivo") });
    expect(bar.className).toContain("cs-progress");
    expect(await violations()).toEqual([]);
  });

  it("shows the value as text, clamps it and never advances by itself", () => {
    vi.useFakeTimers();
    render(<Progress label="Subiendo archivo" value={140} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("100");
    expect(document.body.textContent).toContain("100 %");
    act(() => vi.advanceTimersByTime(EIGHT_HOURS));
    expect(bar.getAttribute("aria-valuenow")).toBe("100");
  });

  it("NaN, infinite or negative input falls back to something sensible", () => {
    const { rerender } = render(<Progress label="Subiendo archivo" value={Number.NaN} />);
    expect(screen.getByRole("progressbar").hasAttribute("aria-valuenow")).toBe(false);
    expect(document.body.textContent).not.toContain("NaN");
    rerender(<Progress label="Subiendo archivo" value={-5} max={0} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("0");
    expect(screen.getByRole("progressbar").getAttribute("aria-valuemax")).toBe("100");
    rerender(<Progress label="Subiendo archivo" value={Number.POSITIVE_INFINITY} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("100");
  });

  it("indeterminate has no value and says it is loading in text", () => {
    render(<Progress label="Subiendo archivo" />);
    const bar = screen.getByRole("progressbar");
    expect(bar.hasAttribute("aria-valuenow")).toBe(false);
    expect(document.body.textContent).toContain(es["state.loading.label"]);
  });
});

describe("StatusBanner", () => {
  const labels = {
    info: es["status.info.label"],
    success: es["status.success.label"],
    warning: es["status.warning.label"],
    error: es["state.error.label"],
  } as const;

  it.each(["info", "success", "warning", "error"] as const)(
    "%s passes axe and names its kind in text, not only color",
    async (variant) => {
      render(<StatusBanner variant={variant}>No se pudo enviar.</StatusBanner>);
      const banner = document.querySelector(".cs-banner");
      expect(banner?.textContent).toContain(labels[variant]);
      expect(banner?.textContent).toContain("No se pudo enviar.");
      expect(["status", "alert"]).toContain(banner?.getAttribute("role"));
      expect(await violations()).toEqual([]);
    },
  );

  it("with actions and a dismiss button still passes axe; the name has the visible text", async () => {
    render(
      <StatusBanner variant="error" actions={<Button>Reintentar</Button>}>
        No se pudo enviar.
      </StatusBanner>,
    );
    screen.getByRole("button", { name: nameContains("Reintentar") });
    screen.getByRole("button", { name: nameContains(es["banner.dismiss.label"]) });
    expect(await violations()).toEqual([]);
  });

  it("never closes by itself: still visible after eight hours", () => {
    vi.useFakeTimers();
    render(<StatusBanner variant="warning">Hay una aprobación pendiente.</StatusBanner>);
    act(() => vi.advanceTimersByTime(EIGHT_HOURS));
    expect(screen.getByText("Hay una aprobación pendiente.")).toBeTruthy();
  });

  it("only the person's action dismisses it, and the app is told", async () => {
    const onDismiss = vi.fn();
    render(
      <StatusBanner variant="info" onDismiss={onDismiss}>
        Todo guardado.
      </StatusBanner>,
    );
    await userEvent.click(
      screen.getByRole("button", { name: nameContains(es["banner.dismiss.label"]) }),
    );
    expect(screen.queryByText("Todo guardado.")).toBeNull();
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("can be made non-dismissible", () => {
    render(
      <StatusBanner variant="error" dismissible={false}>
        Sin conexión.
      </StatusBanner>,
    );
    expect(screen.queryByRole("button")).toBeNull();
  });
});

describe("Stepper", () => {
  const steps = [
    { key: "a", label: "Elegir destinatario" },
    { key: "b", label: "Escribir mensaje" },
    { key: "c", label: "Revisar" },
  ];

  it("passes axe, marks the current step and states every step in text", async () => {
    render(<Stepper aria-label="Pasos" steps={steps} current={1} />);
    expect(await violations()).toEqual([]);
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(3);
    expect(items[0]?.textContent).toContain(es["step.done.label"]);
    expect(items[1]?.textContent).toContain(es["step.current.label"]);
    expect(items[2]?.textContent).toContain(es["step.pending.label"]);
    expect(items.map((i) => i.getAttribute("aria-current"))).toEqual([null, "step", null]);
    expect(items[1]?.textContent).toContain("2");
  });

  it("does not advance by itself and clamps an out-of-range current", () => {
    vi.useFakeTimers();
    render(<Stepper aria-label="Pasos" steps={steps} current={9} />);
    act(() => vi.advanceTimersByTime(EIGHT_HOURS));
    const items = screen.getAllByRole("listitem");
    expect(items.map((i) => i.getAttribute("aria-current"))).toEqual([null, null, "step"]);
  });
});
