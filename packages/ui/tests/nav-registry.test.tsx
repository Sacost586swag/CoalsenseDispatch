import { createRef, StrictMode } from "react";
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApprovalCard } from "../src/components/ApprovalCard.tsx";
import { Button } from "../src/components/Button.tsx";
import { Dialog } from "../src/components/Dialog.tsx";
import { StopUndoBar } from "../src/components/StopUndoBar.tsx";
import { TextField } from "../src/components/TextField.tsx";
import { Link } from "../src/components/Link.tsx";
import { NavTargetProvider, NavTargetRegistry, navTargetRegistry } from "../src/index.ts";
import type { NavTarget, NavTargetMeasure } from "../src/index.ts";

let resize: ResizeObserverCallback;
let observed: Element[];
let disconnect: ReturnType<typeof vi.fn>;
let frames: Map<number, FrameRequestCallback>;
let sequence: number;

beforeEach(() => {
  frames = new Map();
  sequence = 0;
  observed = [];
  disconnect = vi.fn();
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(callback: ResizeObserverCallback) {
        resize = callback;
      }
      observe = (element: Element) => void observed.push(element);
      unobserve = vi.fn();
      disconnect = disconnect;
    },
  );
  vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
    frames.set(++sequence, callback);
    return sequence;
  });
  vi.spyOn(window, "cancelAnimationFrame").mockImplementation((id) => {
    frames.delete(id);
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function flushFrame() {
  act(() => {
    const pending = [...frames.values()];
    frames.clear();
    for (const callback of pending) callback(0);
  });
}

describe("navigation target registry", () => {
  it("registers controls, updates geometry in one frame and updates visible labels on commit", () => {
    const registry = new NavTargetRegistry();
    let bounds = new DOMRect(12, 30, 120, 44);
    const measure = vi.fn(() => bounds);
    const control = (label: string) => (
      <NavTargetProvider registry={registry} measure={measure}>
        <Button>{label}</Button>
      </NavTargetProvider>
    );
    const view = render(control("Continuar"));
    flushFrame();
    const id = registry.snapshot()[0]?.id;
    expect(id).toBeTruthy();
    expect(registry.snapshot()).toEqual([
      {
        id,
        label: "Continuar",
        role: "button",
        disabled: false,
        bounds: { x: 12, y: 30, width: 120, height: 44 },
      },
    ]);
    measure.mockClear();
    bounds = new DOMRect(22, 70, 150, 48);
    act(() => {
      resize([], {} as ResizeObserver);
      window.dispatchEvent(new Event("scroll"));
      window.dispatchEvent(new Event("resize"));
    });
    expect(measure).not.toHaveBeenCalled();
    expect(frames.size).toBe(1);
    flushFrame();
    expect(measure).toHaveBeenCalledTimes(1);
    expect(registry.snapshot()[0]?.bounds).toEqual({ x: 22, y: 70, width: 150, height: 48 });
    view.rerender(control("Confirmar"));
    flushFrame();
    expect(registry.snapshot()[0]).toMatchObject({ id, label: "Confirmar" });
    view.unmount();
    expect(registry.snapshot()).toEqual([]);
    expect(disconnect).toHaveBeenCalled();
  });

  it("sorts by top then left and includes disabled and loading controls", () => {
    const registry = new NavTargetRegistry();
    const positions: Record<string, DOMRect> = {
      bottom: new DOMRect(0, 100, 44, 44),
      right: new DOMRect(70, 0, 44, 44),
      left: new DOMRect(10, 0, 44, 44),
    };
    render(
      <NavTargetProvider
        registry={registry}
        measure={(element) => {
          const position = positions[element.id];
          if (!position) throw new Error(`Missing test geometry: ${element.id}`);
          return position;
        }}
      >
        <Button id="bottom" disabled>
          Guardar
        </Button>
        <Link id="right" href="/" disabled>
          Inicio
        </Link>
        <Button id="left" loading>
          Enviar
        </Button>
      </NavTargetProvider>,
    );
    flushFrame();
    expect(registry.snapshot().map(({ id, role, disabled }) => ({ id, role, disabled }))).toEqual([
      { id: "left", role: "button", disabled: true },
      { id: "right", role: "link", disabled: true },
      { id: "bottom", role: "button", disabled: true },
    ]);
    expect(registry.snapshot()[0]?.label).toBe("Enviar Cargando");
  });

  it("rejects empty labels with a development diagnostic and recovers on update", () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    const registry = new NavTargetRegistry();
    const view = render(
      <NavTargetProvider registry={registry} measure={() => new DOMRect(0, 0, 100, 44)}>
        <Button id="empty">
          {" "}
          <span aria-hidden="true">Icon</span>{" "}
        </Button>
      </NavTargetProvider>,
    );
    flushFrame();
    expect(registry.snapshot()).toEqual([]);
    expect(error).toHaveBeenCalledWith(expect.stringContaining("non-empty visible label"));
    view.rerender(
      <NavTargetProvider registry={registry} measure={() => new DOMRect(0, 0, 100, 44)}>
        <Button id="empty">Listo</Button>
      </NavTargetProvider>,
    );
    flushFrame();
    expect(registry.snapshot()[0]?.label).toBe("Listo");
  });

  it("publishes detached snapshots to subscribers and the companion, including removal", () => {
    const registry = new NavTargetRegistry();
    const listener = vi.fn();
    const unsubscribe = registry.subscribe(listener);
    const details: NavTarget[][] = [];
    const onEvent = (event: Event) => details.push((event as CustomEvent<NavTarget[]>).detail);
    window.addEventListener("cs:nav-targets", onEvent);
    try {
      const view = render(
        <NavTargetProvider registry={registry} measure={() => new DOMRect(0, 0, 44, 44)}>
          <Link id="home" href="/">
            Inicio
          </Link>
        </NavTargetProvider>,
      );
      flushFrame();
      expect(listener).toHaveBeenCalledTimes(1);
      expect(details[0]).toEqual(registry.snapshot());
      const eventTarget = details[0]?.[0];
      if (!eventTarget) throw new Error("Missing event target");
      eventTarget.bounds.x = 999;
      const snapshot = registry.snapshot();
      const snapshotTarget = snapshot[0];
      if (!snapshotTarget) throw new Error("Missing snapshot target");
      snapshotTarget.label = "changed";
      expect(registry.snapshot()[0]).toMatchObject({ label: "Inicio", bounds: { x: 0 } });
      flushFrame();
      registry.refresh();
      expect(listener).toHaveBeenCalledTimes(1);
      unsubscribe();
      view.unmount();
      expect(details.at(-1)).toEqual([]);
      expect(listener).toHaveBeenCalledTimes(1);
    } finally {
      window.removeEventListener("cs:nav-targets", onEvent);
    }
  });

  it("handles nested scrolling and cancels pending work and listeners on unmount", () => {
    const registry = new NavTargetRegistry();
    let y = 100;
    const view = render(
      <NavTargetProvider registry={registry} measure={() => new DOMRect(0, y, 44, 44)}>
        <div data-testid="scroller">
          <Button>Acción</Button>
        </div>
      </NavTargetProvider>,
    );
    flushFrame();
    y = 20;
    act(() => view.getByTestId("scroller").dispatchEvent(new Event("scroll")));
    flushFrame();
    expect(registry.snapshot()[0]?.bounds.y).toBe(20);
    act(() => window.dispatchEvent(new Event("resize")));
    expect(frames.size).toBe(1);
    view.unmount();
    expect(frames.size).toBe(0);
    act(() => window.dispatchEvent(new Event("resize")));
    expect(frames.size).toBe(0);
  });

  it("self-registers without a provider and survives StrictMode effect replay", () => {
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 0, 44, 44),
    );
    const view = render(
      <StrictMode>
        <Button>Acción</Button>
        <Link href="/">Inicio</Link>
      </StrictMode>,
    );
    flushFrame();
    expect(navTargetRegistry.snapshot().map((target) => target.label)).toEqual([
      "Acción",
      "Inicio",
    ]);
    expect(new Set(navTargetRegistry.snapshot().map((target) => target.id)).size).toBe(2);
    for (const target of navTargetRegistry.snapshot()) {
      expect(document.getElementById(target.id)).toBe(view.getByRole(target.role));
    }
    view.unmount();
    expect(navTargetRegistry.snapshot()).toEqual([]);
  });

  it("keeps a consumer ref working next to the registration (object and callback refs)", () => {
    const registry = new NavTargetRegistry();
    const objectRef = createRef<HTMLButtonElement>();
    const seen: Array<HTMLAnchorElement | null> = [];
    const view = render(
      <NavTargetProvider registry={registry} measure={() => new DOMRect(0, 0, 44, 44)}>
        <Button ref={objectRef}>Uno</Button>
        <Link href="/" ref={(node) => void seen.push(node)}>
          Dos
        </Link>
      </NavTargetProvider>,
    );
    flushFrame();
    expect(objectRef.current).toBe(view.getByRole("button"));
    expect(seen.at(-1)).toBe(view.getByRole("link"));
    expect(registry.snapshot().map((target) => target.label)).toEqual(["Uno", "Dos"]);
    view.unmount();
    expect(objectRef.current).toBeNull();
    expect(seen.at(-1)).toBeNull();
    expect(registry.snapshot()).toEqual([]);
  });

  it("follows a Link to its new element when it toggles disabled, label without the reason", () => {
    const registry = new NavTargetRegistry();
    const measure = vi.fn<NavTargetMeasure>(() => new DOMRect(0, 0, 44, 44));
    const tree = (disabled: boolean) => (
      <NavTargetProvider registry={registry} measure={measure}>
        <Link href="/" disabled={disabled} disabledReason="state.loading.message">
          Inicio
        </Link>
      </NavTargetProvider>
    );
    const view = render(tree(false));
    flushFrame();
    expect(registry.snapshot()).toMatchObject([{ label: "Inicio", disabled: false }]);
    view.rerender(tree(true));
    flushFrame();
    expect(registry.snapshot()).toMatchObject([{ label: "Inicio", disabled: true }]);
    expect(measure.mock.lastCall?.[0]).toBe(view.container.querySelector("a"));
    view.rerender(tree(false));
    flushFrame();
    expect(registry.snapshot()).toMatchObject([{ label: "Inicio", disabled: false }]);
    expect(measure.mock.lastCall?.[0]).toBe(view.container.querySelector("a"));
  });

  it("registers a TextField by its visible label and never publishes its value", () => {
    const registry = new NavTargetRegistry();
    const details: NavTarget[][] = [];
    const onEvent = (event: Event) => details.push((event as CustomEvent<NavTarget[]>).detail);
    window.addEventListener("cs:nav-targets", onEvent);
    try {
      const ref = createRef<HTMLInputElement>();
      const view = render(
        <NavTargetProvider registry={registry} measure={() => new DOMRect(5, 6, 200, 44)}>
          <TextField
            ref={ref}
            label="Correo del cliente"
            hint="Ayuda"
            defaultValue="secreto@example.com"
          />
        </NavTargetProvider>,
      );
      flushFrame();
      expect(ref.current).toBe(view.getByRole("textbox"));
      expect(registry.snapshot()).toMatchObject([
        { label: "Correo del cliente", role: "textbox", disabled: false },
      ]);
      expect(details.length).toBeGreaterThan(0);
      expect(JSON.stringify([registry.snapshot(), details])).not.toContain("secreto@example.com");
      expect(Object.keys(registry.snapshot()[0] ?? {}).sort()).toEqual([
        "bounds",
        "disabled",
        "id",
        "label",
        "role",
      ]);
    } finally {
      window.removeEventListener("cs:nav-targets", onEvent);
    }
  });

  it("registers the buttons of the stop bar and the approval card", () => {
    const registry = new NavTargetRegistry();
    render(
      <NavTargetProvider registry={registry} measure={() => new DOMRect(0, 0, 44, 44)}>
        <StopUndoBar onStop={() => {}} onUndo={() => {}} onHelp={() => {}} undoAvailable={false} />
        <ApprovalCard
          what="Enviar correo"
          recipient="Ana"
          effect="Se envía"
          onApprove={() => {}}
          onReject={() => {}}
          onDecideLater={() => {}}
        />
      </NavTargetProvider>,
    );
    flushFrame();
    const targets = registry.snapshot();
    expect(targets.map((target) => target.id)).toEqual(
      expect.arrayContaining(["cs-stop", "cs-undo", "cs-help"]),
    );
    expect(targets.find((target) => target.id === "cs-undo")?.disabled).toBe(true);
    expect(targets.filter((target) => target.role === "button")).toHaveLength(6);
  });

  it("follows position-only changes: page observers, transitions, animations and visualViewport", async () => {
    const registry = new NavTargetRegistry();
    const viewport = new EventTarget();
    Object.defineProperty(window, "visualViewport", { value: viewport, configurable: true });
    try {
      let y = 10;
      const view = render(
        <NavTargetProvider registry={registry} measure={() => new DOMRect(0, y, 80, 44)}>
          <Button>Acción</Button>
        </NavTargetProvider>,
      );
      flushFrame();
      expect(observed).toEqual(expect.arrayContaining([document.documentElement, document.body]));
      // A banner inserted above shifts the control: no scroll, no resize of the control.
      y = 60;
      await act(async () => {
        view.container.insertAdjacentHTML("beforebegin", "<p>Aviso</p>");
        await Promise.resolve();
      });
      expect(frames.size).toBe(1);
      flushFrame();
      expect(registry.snapshot()[0]?.bounds.y).toBe(60);
      const triggers: Array<[string, EventTarget, number]> = [
        ["transitionend", document.body, 70],
        ["animationend", document.body, 80],
        ["resize", viewport, 90],
        ["scroll", viewport, 100],
      ];
      for (const [type, target, nextY] of triggers) {
        y = nextY;
        act(() => {
          target.dispatchEvent(new Event(type, { bubbles: true }));
        });
        flushFrame();
        expect(registry.snapshot()[0]?.bounds.y).toBe(nextY);
      }
      view.unmount();
      act(() => {
        viewport.dispatchEvent(new Event("resize"));
      });
      expect(frames.size).toBe(0);
    } finally {
      Reflect.deleteProperty(window, "visualViewport");
    }
  });

  it("measures once per frame for 200 controls, never inside a commit", () => {
    const registry = new NavTargetRegistry();
    const measure = vi.fn<NavTargetMeasure>(() => new DOMRect(0, 0, 44, 44));
    const labels = Array.from({ length: 200 }, (_, index) => `Acción ${index}`);
    const tree = (suffix: string) => (
      <NavTargetProvider registry={registry} measure={measure}>
        {labels.map((label) => (
          <Button key={label}>{label + suffix}</Button>
        ))}
      </NavTargetProvider>
    );
    const view = render(tree(""));
    expect(measure).not.toHaveBeenCalled();
    expect(frames.size).toBe(1);
    flushFrame();
    expect(measure).toHaveBeenCalledTimes(200);
    expect(registry.snapshot()).toHaveLength(200);
    measure.mockClear();
    view.rerender(tree("!"));
    expect(measure).not.toHaveBeenCalled();
    expect(frames.size).toBe(1);
    flushFrame();
    expect(measure).toHaveBeenCalledTimes(200);
    expect(frames.size).toBe(0);
  });

  it("skips hidden, aria-hidden and zero-size controls; an open Dialog hides the page", async () => {
    const registry = new NavTargetRegistry();
    const measure = (element: HTMLElement) =>
      element.id === "flat" ? new DOMRect(0, 0, 0, 0) : new DOMRect(0, 0, 44, 44);
    const tree = (open: boolean) => (
      <NavTargetProvider registry={registry} measure={measure}>
        <div id="page">
          <Button id="behind">Detrás</Button>
          <div hidden>
            <Button id="closed">Cerrado</Button>
          </div>
          <div aria-hidden="true">
            <Button id="decor">Decorado</Button>
          </div>
          <Button id="flat">Plano</Button>
        </div>
        <StopUndoBar onStop={() => {}} onUndo={() => {}} onHelp={() => {}} undoAvailable />
        <Dialog open={open} title="Enviar correo" actions={<Button id="ok">Aprobar</Button>}>
          <p>Cuerpo</p>
        </Dialog>
      </NavTargetProvider>
    );
    const view = render(tree(false));
    flushFrame();
    const ids = () => registry.snapshot().map((target) => target.id);
    expect(ids()).toEqual(expect.arrayContaining(["behind", "cs-stop"]));
    for (const hidden of ["closed", "decor", "flat"]) expect(ids()).not.toContain(hidden);
    await act(async () => {
      view.rerender(tree(true));
      await Promise.resolve();
    });
    flushFrame();
    expect(ids()).toEqual(expect.arrayContaining(["ok", "cs-stop", "cs-undo", "cs-help"]));
    expect(ids()).not.toContain("behind");
    await act(async () => {
      view.rerender(tree(false));
      await Promise.resolve();
    });
    flushFrame();
    expect(ids()).toContain("behind");
    expect(ids()).not.toContain("ok");
  });
});
