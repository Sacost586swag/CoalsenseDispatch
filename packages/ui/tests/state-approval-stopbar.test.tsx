// T-00-015 (a11y): StateScreen (AX-11), ApprovalCard (AX-09), StopUndoBar (AX-05).
// jsdom computes no layout: size and position are checked on the stylesheet and on class wiring;
// the geometric 44x44 / 64x64 measurement arrives in T-00-017 (Playwright). color-contrast is the
// only axe rule turned off (T-00-013 already proves the token pairs).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render as rtlRender, screen, within } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { userEvent } from "@testing-library/user-event";
import axe from "axe-core";
import { ApprovalCard } from "../src/components/ApprovalCard.tsx";
import { StateScreen, type StateScreenProps } from "../src/components/StateScreen.tsx";
import { StopUndoBar } from "../src/components/StopUndoBar.tsx";
import { Button, Dialog, TextField, STOP_BAR_ATTRIBUTE } from "../src/components/index.ts";
import { NavTargetProvider, NavTargetRegistry, es } from "../src/index.ts";

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

const EIGHT_HOURS = 8 * 60 * 60 * 1000;
const css = readFileSync(
  join(process.cwd(), "src", "components", "components.css"),
  "utf8",
).replace(/\/\*[\s\S]*?\*\//g, "");
const rule = (selector: string): string =>
  [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)]
    .filter(([, list]) => list?.split(",").some((s) => s.trim() === selector))
    .map(([, , body]) => body)
    .join(" ");

const STATES = [
  ["loading", es["state.loading.label"], es["state.loading.message"]],
  ["empty", es["state.empty.label"], es["state.empty.message"]],
  ["error", es["state.error.label"], es["state.error.message"]],
  ["offline", es["state.offline.label"], es["state.offline.message"]],
  [
    "calibration_failed",
    es["state.calibrationFailed.label"],
    es["state.calibrationFailed.message"],
  ],
  [
    "modality_missing",
    es["state.modalityNotDetected.label"],
    es["state.modalityNotDetected.message"],
  ],
] as const;

describe("StateScreen", () => {
  const screenFor = (state: StateScreenProps["state"], extra: Partial<StateScreenProps> = {}) => (
    <StateScreen
      state={state}
      actions={[{ label: "Reintentar", onAction: () => undefined }]}
      stillWorks={["Tus datos guardados"]}
      {...extra}
    />
  );

  it.each(STATES)(
    "%s is complete: name, what happened, an operable action, what still works; passes axe",
    async (state, label, message) => {
      render(screenFor(state));
      expect(screen.getByRole("heading", { name: label })).toBeTruthy();
      expect(screen.getByText(message)).toBeTruthy(); // catalog default for whatHappened
      expect(screen.getByText(es["state.whatHappened.label"])).toBeTruthy();
      expect(screen.getByRole("button", { name: "Reintentar" })).toBeTruthy();
      expect(screen.getByText("Tus datos guardados")).toBeTruthy();
      expect(screen.getByText(es["state.stillWorks.label"])).toBeTruthy();
      expect(await violations()).toEqual([]);
    },
  );

  it("uses the supplied whatHappened instead of the default", () => {
    render(screenFor("error", { whatHappened: "No se guardó el borrador." }));
    expect(screen.getByText("No se guardó el borrador.")).toBeTruthy();
    expect(screen.queryByText(es["state.error.message"])).toBeNull();
  });

  it("says what still works even when the screen gave nothing (Alto and Deshacer stay)", () => {
    render(screenFor("offline", { stillWorks: [] }));
    expect(screen.getByText(es["state.stillWorks.default"])).toBeTruthy();
  });

  it("every action runs its handler and is reachable by Tab", async () => {
    const retry = vi.fn();
    const other = vi.fn();
    render(
      screenFor("error", {
        actions: [
          { label: "Reintentar", onAction: retry },
          { label: "Pedir ayuda", onAction: other },
        ],
      }),
    );
    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Reintentar" }));
    await userEvent.keyboard("{Enter}");
    expect(retry).toHaveBeenCalledTimes(1);
    await userEvent.tab();
    await userEvent.keyboard(" ");
    expect(other).toHaveBeenCalledTimes(1);
  });

  it("one primary action per screen: the first; the rest are secondary", () => {
    render(
      screenFor("error", {
        actions: [
          { label: "Reintentar", onAction: () => undefined },
          { label: "Pedir ayuda", onAction: () => undefined },
        ],
      }),
    );
    expect(screen.getByRole("button", { name: "Reintentar" }).className).toContain(
      "cs-button--primary",
    );
    expect(screen.getByRole("button", { name: "Pedir ayuda" }).className).toContain(
      "cs-button--secondary",
    );
  });

  it("loading is busy and shows an indeterminate progress, no timer", () => {
    render(screenFor("loading"));
    expect(document.querySelector("[aria-busy='true']")).not.toBeNull();
    expect(screen.getByRole("progressbar").hasAttribute("aria-valuenow")).toBe(false);
  });

  it("the state is announced from a live region that is always mounted", () => {
    const { rerender } = render(screenFor("loading"));
    const region = document.querySelector(".cs-state__what") as HTMLElement;
    expect(region.getAttribute("role")).toBe("status");
    rerender(screenFor("error"));
    // same node: the region persisted, only its text changed
    expect(document.querySelector(".cs-state__what")).toBe(region);
    expect(region.textContent).toContain(es["state.error.message"]);
  });

  it("never blames the person; calibration failure points at the equipment (AX-12)", () => {
    for (const [, , message] of STATES) {
      expect(message).not.toMatch(/\b(fallaste|tu culpa|te equivocaste|hiciste mal|tú)\b/i);
    }
    expect(es["state.calibrationFailed.message"]).toMatch(/equipo/i);
    expect(es["state.modalityNotDetected.message"]).toMatch(/equipo/i);
  });

  it("the state is named in text, not by color alone, and nothing times out", () => {
    vi.useFakeTimers();
    render(screenFor("error"));
    act(() => vi.advanceTimersByTime(EIGHT_HOURS));
    expect(screen.getByRole("heading", { name: es["state.error.label"] })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeTruthy();
  });
});

describe("ApprovalCard", () => {
  const card = (extra: Partial<Parameters<typeof ApprovalCard>[0]> = {}) => (
    <ApprovalCard
      what="Enviar el correo del texto de abajo"
      recipient="Ana Pérez"
      effect="Ana recibe el correo y no se puede retirar"
      onApprove={() => undefined}
      onReject={() => undefined}
      onDecideLater={() => undefined}
      {...extra}
    >
      Hola Ana, mañana te llamo.
    </ApprovalCard>
  );

  it("shows what is approved, to whom it goes, its effect and the exact content; passes axe", async () => {
    render(card());
    const group = screen.getByRole("region", { name: es["approval.title"] });
    for (const [label, value] of [
      [es["approval.what.label"], "Enviar el correo del texto de abajo"],
      [es["approval.recipient.label"], "Ana Pérez"],
      [es["approval.effect.label"], "Ana recibe el correo y no se puede retirar"],
    ] as const) {
      const term = within(group).getByText(label);
      expect(term.tagName).toBe("DT");
      expect(term.nextElementSibling?.textContent).toBe(value);
    }
    expect(within(group).getByText("Hola Ana, mañana te llamo.")).toBeTruthy();
    expect(await violations()).toEqual([]);
  });

  it("has approve, reject and decide later with the catalog labels, in that order", async () => {
    render(card());
    const names = screen.getAllByRole("button").map((b) => b.textContent);
    expect(names).toEqual([
      es["approval.approve.label"],
      es["approval.reject.label"],
      es["approval.defer.label"],
    ]);
  });

  it("preselects nothing: no initial focus on an action, no pressed/checked/primary option", () => {
    render(card());
    const heading = screen.getByRole("heading", { name: es["approval.title"] });
    expect(document.activeElement).toBe(heading);
    const buttons = screen.getAllByRole("button");
    for (const b of buttons) {
      expect(b.hasAttribute("aria-pressed")).toBe(false);
      expect(b.hasAttribute("autofocus")).toBe(false);
      expect(b.getAttribute("aria-disabled")).toBeNull();
    }
    // reject is as easy as approve: identical visual weight, none is the primary action
    expect(new Set(buttons.map((b) => b.className)).size).toBe(1);
    expect(buttons[0]?.className).not.toContain("cs-button--primary");
    expect(document.querySelector("input[checked], [aria-checked='true']")).toBeNull();
  });

  it("each action calls only its own handler", async () => {
    const handlers = { onApprove: vi.fn(), onReject: vi.fn(), onDecideLater: vi.fn() };
    render(card(handlers));
    await userEvent.click(screen.getByRole("button", { name: es["approval.reject.label"] }));
    expect(handlers.onReject).toHaveBeenCalledTimes(1);
    expect(handlers.onApprove).not.toHaveBeenCalled();
    expect(handlers.onDecideLater).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: es["approval.defer.label"] }));
    expect(handlers.onDecideLater).toHaveBeenCalledTimes(1);
    expect(handlers.onApprove).not.toHaveBeenCalled();
  });

  it("Enter on the title or Tab alone never approves; the first Tab reaches the first action", async () => {
    const onApprove = vi.fn();
    render(card({ onApprove }));
    await userEvent.keyboard("{Enter}");
    await userEvent.tab();
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: es["approval.approve.label"] }),
    );
    expect(onApprove).not.toHaveBeenCalled();
  });

  it("nothing expires: after eight hours it is still pending and no handler ran", () => {
    vi.useFakeTimers();
    const handlers = { onApprove: vi.fn(), onReject: vi.fn(), onDecideLater: vi.fn() };
    render(card(handlers));
    act(() => vi.advanceTimersByTime(EIGHT_HOURS));
    expect(screen.getByRole("heading", { name: es["approval.title"] })).toBeTruthy();
    expect(screen.getAllByRole("button")).toHaveLength(3);
    for (const handler of Object.values(handlers)) expect(handler).not.toHaveBeenCalled();
  });

  it("says in text that it is pending and does not expire (not by color alone)", () => {
    render(card());
    const region = document.querySelector(".cs-approval__pending") as HTMLElement;
    expect(region.textContent).toContain(es["approval.pending.label"]);
    expect(region.textContent).toContain(es["approval.noExpiry.message"]);
    expect(region.getAttribute("role")).toBe("status");
  });
});

describe("StopUndoBar", () => {
  const bar = (extra: Partial<Parameters<typeof StopUndoBar>[0]> = {}) => (
    <StopUndoBar
      onStop={() => undefined}
      onUndo={() => undefined}
      onHelp={() => undefined}
      undoAvailable
      {...extra}
    />
  );
  const marker = () => document.querySelector(`[${STOP_BAR_ATTRIBUTE}]`) as HTMLElement;

  it("is marked for the Dialog, has Alto, Deshacer and Ayuda humana, passes axe", async () => {
    render(bar());
    expect(marker()).not.toBeNull();
    expect(
      within(marker())
        .getAllByRole("button")
        .map((b) => b.textContent),
    ).toEqual([es["stop.label"], es["undo.label"], es["help.label"]]);
    expect(await violations()).toEqual([]);
  });

  it("each control calls its handler", async () => {
    const handlers = { onStop: vi.fn(), onUndo: vi.fn(), onHelp: vi.fn() };
    render(bar(handlers));
    await userEvent.click(screen.getByRole("button", { name: es["stop.label"] }));
    await userEvent.click(screen.getByRole("button", { name: es["undo.label"] }));
    await userEvent.click(screen.getByRole("button", { name: es["help.label"] }));
    expect(handlers.onStop).toHaveBeenCalledTimes(1);
    expect(handlers.onUndo).toHaveBeenCalledTimes(1);
    expect(handlers.onHelp).toHaveBeenCalledTimes(1);
  });

  it("with nothing to undo, Deshacer stays visible, focusable, inert to clicks, and says why", async () => {
    const onUndo = vi.fn();
    render(bar({ undoAvailable: false, onUndo }));
    const undo = screen.getByRole("button", { name: es["undo.label"] });
    expect(undo.getAttribute("aria-disabled")).toBe("true");
    expect(undo.hasAttribute("disabled")).toBe(false);
    await userEvent.click(undo);
    expect(onUndo).not.toHaveBeenCalled();
    expect(screen.getByText(es["undo.none.reason"])).toBeTruthy();
    const ids = (undo.getAttribute("aria-describedby") ?? "").split(" ");
    expect(ids.map((id) => document.getElementById(id)?.textContent)).toContain(
      es["undo.none.reason"],
    );
    expect(await violations()).toEqual([]);
  });

  it("Alto and Ayuda humana are never disabled", () => {
    render(bar({ undoAvailable: false }));
    for (const name of [es["stop.label"], es["help.label"]]) {
      expect(screen.getByRole("button", { name }).getAttribute("aria-disabled")).toBeNull();
    }
    expect(screen.getByRole("button", { name: es["stop.label"] }).className).toContain(
      "cs-button--stop",
    );
  });

  it("is fixed, always visible, above dialogs, with head-size targets (stylesheet)", () => {
    const body = rule(".cs-stop-bar[data-cs-stop-bar]");
    expect(body).toMatch(/position:\s*fixed/);
    expect(body).toMatch(/bottom:\s*0/);
    expect(body).toMatch(/z-index:\s*var\(--layer-stop-bar\)/);
    expect(rule(".cs-stop-bar .cs-button")).toMatch(/min-height:\s*var\(--target-head\)/);
    expect(rule(".cs-stop-bar .cs-button")).toMatch(/min-width:\s*var\(--target-head\)/);
    expect(rule(".cs-stop-bar")).toMatch(/gap:\s*var\(--target-gap\)/);
    expect(css).toMatch(/--stop-bar-reserved:\s*calc\(var\(--target-head\)/);
    expect(body).not.toMatch(/display:\s*none|visibility|opacity/);
  });

  it("registers its three controls in the navigation registry", () => {
    const registry = new NavTargetRegistry();
    rtlRender(
      <NavTargetProvider registry={registry} measure={() => new DOMRect(0, 0, 100, 64)}>
        <main>{bar()}</main>
      </NavTargetProvider>,
    );
    registry.refresh();
    expect(
      registry
        .snapshot()
        .map((t) => t.label.trim())
        .sort(),
    ).toEqual([es["help.label"], es["stop.label"], es["undo.label"]].sort());
  });

  it("publishes its real height as --stop-bar-reserved and removes it on unmount", () => {
    const { unmount } = render(bar());
    expect(document.documentElement.style.getPropertyValue("--stop-bar-reserved")).not.toBe("");
    unmount();
    expect(document.documentElement.style.getPropertyValue("--stop-bar-reserved")).toBe("");
  });

  describe("with a Dialog open", () => {
    const withDialog = (handlers: Partial<Parameters<typeof StopUndoBar>[0]> = {}) => (
      <>
        <p>Contenido de la pantalla</p>
        {bar(handlers)}
        <Dialog open title="Enviar correo" actions={<Button>Aprobar</Button>}>
          Se enviará a Ana.
        </Dialog>
      </>
    );

    it("is not inert and neither is any ancestor; the page behind is", async () => {
      render(withDialog());
      await act(async () => undefined);
      expect(screen.getByText("Contenido de la pantalla").hasAttribute("inert")).toBe(true);
      for (let node: Element | null = marker(); node; node = node.parentElement) {
        expect(node.hasAttribute("inert"), node.outerHTML.slice(0, 60)).toBe(false);
      }
      for (const b of within(marker()).getAllByRole("button")) {
        expect(b.closest("[inert]")).toBeNull();
      }
      expect(await violations()).toEqual([]);
    });

    it("stays in the accessibility tree (no aria-modal hiding it) and keeps working", async () => {
      const onStop = vi.fn();
      render(withDialog({ onStop }));
      await act(async () => undefined);
      expect(document.querySelector("[aria-modal]")).toBeNull();
      expect(screen.getByRole("button", { name: es["stop.label"] })).toBeTruthy();
      await userEvent.click(screen.getByRole("button", { name: es["stop.label"] }));
      expect(onStop).toHaveBeenCalledTimes(1);
    });

    it("Tab reaches Alto, Deshacer and Ayuda humana from inside the dialog", async () => {
      render(withDialog());
      await act(async () => undefined);
      const visited = new Set<string>();
      for (let i = 0; i < 6; i++) {
        await userEvent.tab();
        visited.add(document.activeElement?.textContent ?? "");
      }
      for (const name of [es["stop.label"], es["undo.label"], es["help.label"]]) {
        expect(visited.has(name), name).toBe(true);
      }
    });

    it("the backdrop stops above the bar's reserved space and the bar is on a higher layer", () => {
      expect(rule(".cs-dialog__backdrop")).toMatch(/bottom:\s*var\(--stop-bar-reserved/);
      expect(css).toMatch(/--layer-stop-bar:\s*200/);
      expect(css).toMatch(/--layer-dialog:\s*100/);
    });
  });

  it("nothing changes after eight hours", () => {
    vi.useFakeTimers();
    render(bar());
    act(() => vi.advanceTimersByTime(EIGHT_HOURS));
    expect(within(marker()).getAllByRole("button")).toHaveLength(3);
  });
});

describe("shared fixes from T-00-014", () => {
  it("TextField mounts its status region before any error and fills the same node", () => {
    const { rerender } = render(<TextField label="Nombre" />);
    const region = screen.getByRole("status");
    expect(region.textContent).toBe("");
    rerender(<TextField label="Nombre" error="Falta el nombre" />);
    expect(screen.getByRole("status")).toBe(region);
    expect(region.textContent).toContain("Falta el nombre");
  });

  it("Button mounts its status region even when loading was not passed", () => {
    render(<Button>Guardar</Button>);
    expect(screen.getByRole("status").textContent).toBe("");
  });

  it("Button announces by changing the text of the same region", () => {
    const { rerender } = render(<Button loading={false}>Guardar</Button>);
    const region = screen.getByRole("status");
    rerender(<Button loading>Guardar</Button>);
    expect(screen.getByRole("status")).toBe(region);
    expect(region.textContent).toBe(es["state.loading.label"]);
  });
});
