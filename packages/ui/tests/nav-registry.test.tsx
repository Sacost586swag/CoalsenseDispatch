import { createRef, StrictMode } from "react";
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Button } from "../src/components/Button.tsx";
import { Link } from "../src/components/Link.tsx";
import { NavTargetProvider, NavTargetRegistry, navTargetRegistry } from "../src/index.ts";
import type { NavTarget, NavTargetMeasure } from "../src/index.ts";

let resize: ResizeObserverCallback;
let disconnect: ReturnType<typeof vi.fn>;
let frames: Map<number, FrameRequestCallback>;
let sequence: number;

beforeEach(() => {
  frames = new Map();
  sequence = 0;
  disconnect = vi.fn();
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(callback: ResizeObserverCallback) {
        resize = callback;
      }
      observe = vi.fn();
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
      <NavTargetProvider registry={registry}>
        <Button id="empty">
          {" "}
          <span aria-hidden="true">Icon</span>{" "}
        </Button>
      </NavTargetProvider>,
    );
    expect(registry.snapshot()).toEqual([]);
    expect(error).toHaveBeenCalledWith(expect.stringContaining("non-empty visible label"));
    view.rerender(
      <NavTargetProvider registry={registry}>
        <Button id="empty">Listo</Button>
      </NavTargetProvider>,
    );
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
        <NavTargetProvider registry={registry}>
          <Link id="home" href="/">
            Inicio
          </Link>
        </NavTargetProvider>,
      );
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
    const view = render(
      <StrictMode>
        <Button>Acción</Button>
        <Link href="/">Inicio</Link>
      </StrictMode>,
    );
    expect(navTargetRegistry.snapshot().map((target) => target.label)).toEqual([
      "Acción",
      "Inicio",
    ]);
    expect(new Set(navTargetRegistry.snapshot().map((target) => target.id)).size).toBe(2);
    view.unmount();
    expect(navTargetRegistry.snapshot()).toEqual([]);
  });

  it("keeps a consumer ref working next to the registration (object and callback refs)", () => {
    const registry = new NavTargetRegistry();
    const objectRef = createRef<HTMLButtonElement>();
    const seen: Array<HTMLAnchorElement | null> = [];
    const view = render(
      <NavTargetProvider registry={registry}>
        <Button ref={objectRef}>Uno</Button>
        <Link href="/" ref={(node) => void seen.push(node)}>
          Dos
        </Link>
      </NavTargetProvider>,
    );
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
    expect(registry.snapshot()).toMatchObject([{ label: "Inicio", disabled: false }]);
    view.rerender(tree(true));
    expect(registry.snapshot()).toMatchObject([{ label: "Inicio", disabled: true }]);
    expect(measure.mock.lastCall?.[0]).toBe(view.container.querySelector("a"));
    view.rerender(tree(false));
    expect(registry.snapshot()).toMatchObject([{ label: "Inicio", disabled: false }]);
    expect(measure.mock.lastCall?.[0]).toBe(view.container.querySelector("a"));
  });
});
