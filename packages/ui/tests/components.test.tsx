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
  it("normal, disabled and loading pass axe and keep the visible label in the name", async () => {
    for (const props of [{}, { disabled: true }, { loading: true }]) {
      const { unmount } = render(<Button {...props}>Guardar</Button>);
      const button = screen.getByRole("button", { name: nameContains("Guardar") });
      expect(button.className).toContain("cs-button");
      expect(button.hasAttribute("aria-label")).toBe(false);
      expect(await violations()).toEqual([]);
      unmount();
    }
  });

  it("loading shows the catalog text, announces busy and ignores activation", async () => {
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
    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
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

  it("disabled does not activate; variants only change the class", async () => {
    const onClick = vi.fn();
    render(
      <Button disabled variant="stop" onClick={onClick}>
        Alto
      </Button>,
    );
    const button = screen.getByRole("button", { name: nameContains("Alto") });
    expect(button.className).toContain("cs-button--stop");
    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe("Link", () => {
  it("normal and disabled pass axe; the name is the visible text", async () => {
    for (const props of [{ href: "/ayuda" }, { href: "/ayuda", disabled: true }]) {
      const { unmount } = render(<Link {...props}>Ver ayuda</Link>);
      const link = screen.getByRole("link", { name: nameContains("Ver ayuda") });
      expect(link.className).toContain("cs-link");
      expect(await violations()).toEqual([]);
      unmount();
    }
  });

  it("a disabled link is not navigable", () => {
    render(
      <Link href="/ayuda" disabled>
        Ver ayuda
      </Link>,
    );
    const link = screen.getByRole("link", { name: nameContains("Ver ayuda") });
    expect(link.getAttribute("aria-disabled")).toBe("true");
    expect(link.hasAttribute("href")).toBe(false);
  });
});

describe("TextField", () => {
  it("normal, hint, error and disabled pass axe; the label names the field", async () => {
    const variants = [
      {},
      { hint: "Solo letras" },
      { error: "Falta el nombre" },
      { disabled: true },
    ];
    for (const props of variants) {
      const { unmount } = render(<TextField label="Nombre" {...props} />);
      const input = screen.getByRole("textbox", { name: nameContains("Nombre") });
      expect(input.className).toContain("cs-input");
      expect(await violations()).toEqual([]);
      unmount();
    }
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
      <Dialog open={false} title="Enviar correo" actions={null}>
        Texto
      </Dialog>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("open dialog passes axe, is modal and is named by its title", async () => {
    render(open());
    const dialog = screen.getByRole("dialog", { name: nameContains("Enviar correo") });
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(await violations()).toEqual([]);
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
          <Dialog open={isOpen} title="Enviar correo" actions={null}>
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
  it("determinate and indeterminate pass axe and are named by the visible label", async () => {
    for (const props of [{ value: 40 }, {}]) {
      const { unmount } = render(<Progress label="Subiendo archivo" {...props} />);
      const bar = screen.getByRole("progressbar", { name: nameContains("Subiendo archivo") });
      expect(bar.className).toContain("cs-progress");
      expect(await violations()).toEqual([]);
      unmount();
    }
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

  it("every variant passes axe and names its kind in text, not only color", async () => {
    for (const variant of ["info", "success", "warning", "error"] as const) {
      const { unmount } = render(<StatusBanner variant={variant}>No se pudo enviar.</StatusBanner>);
      const banner = document.querySelector(".cs-banner");
      expect(banner?.textContent).toContain(labels[variant]);
      expect(banner?.textContent).toContain("No se pudo enviar.");
      expect(["status", "alert"]).toContain(banner?.getAttribute("role"));
      expect(await violations()).toEqual([]);
      unmount();
    }
  });

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
