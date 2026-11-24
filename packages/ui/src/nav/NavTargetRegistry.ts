export interface NavTarget {
  id: string;
  label: string;
  bounds: { x: number; y: number; width: number; height: number };
  role: string;
  disabled: boolean;
}

export type NavTargetMeasure = (element: HTMLElement) => DOMRect;
type Registration = {
  element: HTMLElement;
  role: string;
  measure: NavTargetMeasure;
  warned: boolean;
};

// The controls use their visible contents as their accessible name. Decorative
// and hidden descendants must not contribute (for example an aria-hidden icon).
function visibleLabel(element: Node): string {
  if (element.nodeType === 3) return element.textContent ?? "";
  if (element instanceof HTMLElement) {
    if (element.hidden || element.getAttribute("aria-hidden") === "true") return "";
    const style = window.getComputedStyle(element);
    if (style.display === "none" || style.visibility === "hidden") return "";
  }
  return Array.from(element.childNodes, visibleLabel).join(" ");
}

// aria-labelledby, then the <label>s of a form control, then the visible contents. A control's
// value is never read: only this label text can leave the module.
function labelText(element: HTMLElement): string {
  const ids = element.getAttribute("aria-labelledby")?.split(/\s+/).filter(Boolean) ?? [];
  const named = ids.flatMap((id) => document.getElementById(id) ?? []);
  const labels = named.length ? named : Array.from((element as HTMLInputElement).labels ?? []);
  return (labels.length ? labels : [element]).map(visibleLabel).join(" ");
}

// Controls behind a modal ([inert]), under aria-hidden or not rendered must not get numbers.
function isVisible(element: HTMLElement): boolean {
  if (element.closest("[inert],[aria-hidden='true']")) return false;
  if (typeof element.checkVisibility === "function") {
    return element.checkVisibility({ visibilityProperty: true });
  }
  for (let node: HTMLElement | null = element; node; node = node.parentElement) {
    const style = window.getComputedStyle(node);
    if (style.display === "none" || style.visibility === "hidden") return false;
  }
  return true;
}

const sameTargets = (a: NavTarget[], b: NavTarget[]): boolean =>
  a.length === b.length &&
  a.every((t, i) => {
    const o = b[i];
    return (
      o !== undefined &&
      t.id === o.id &&
      t.label === o.label &&
      t.role === o.role &&
      t.disabled === o.disabled &&
      t.bounds.x === o.bounds.x &&
      t.bounds.y === o.bounds.y &&
      t.bounds.width === o.bounds.width &&
      t.bounds.height === o.bounds.height
    );
  });

const MUTATION_ATTRIBUTES = [
  "class",
  "style",
  "hidden",
  "inert",
  "aria-hidden",
  "aria-disabled",
  "aria-labelledby",
  "disabled",
  "role",
  "open",
];

/** Viewport coordinates, in CSS pixels. No polling or expiry timers. */
export class NavTargetRegistry {
  private registrations = new Map<string, Registration>();
  private targets: NavTarget[] = [];
  private listeners = new Set<() => void>();
  private observer?: ResizeObserver;
  private mutations?: MutationObserver;
  private frame?: number;

  snapshot = (): NavTarget[] =>
    this.targets.map((target) => ({ ...target, bounds: { ...target.bounds } }));

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  register(
    id: string,
    element: HTMLElement,
    role: string,
    measure: NavTargetMeasure = (node) => node.getBoundingClientRect(),
  ): () => void {
    if (this.registrations.has(id)) throw new Error(`Duplicate navigation target id: ${id}`);
    const registration = { element, role, measure, warned: false };
    this.registrations.set(id, registration);
    if (this.registrations.size === 1) this.start();
    this.observer?.observe(element);
    this.schedule();
    return () => {
      if (this.registrations.get(id) !== registration) return;
      this.registrations.delete(id);
      this.observer?.unobserve(element);
      if (this.registrations.size) {
        this.schedule();
        return;
      }
      this.stop();
      this.publish([]);
    };
  }

  /** Measures every target once. Runs from the animation-frame batch, never inside a commit. */
  refresh = (): void => {
    const next: NavTarget[] = [];
    for (const [id, registration] of this.registrations) {
      const { element, measure } = registration;
      if (!isVisible(element)) continue;
      const label = labelText(element).replace(/\s+/g, " ").trim();
      if (!label) {
        if (
          !registration.warned &&
          (typeof process === "undefined" || process.env.NODE_ENV !== "production")
        ) {
          console.error(`Navigation target "${id}" requires a non-empty visible label.`);
        }
        registration.warned = true;
        continue;
      }
      registration.warned = false;
      const { x, y, width, height } = measure(element);
      if (!width || !height) continue;
      next.push({
        id,
        label,
        bounds: { x, y, width, height },
        role: element.getAttribute("role") || registration.role,
        disabled: element.matches(":disabled") || element.getAttribute("aria-disabled") === "true",
      });
    }
    next.sort((a, b) => a.bounds.y - b.bounds.y || a.bounds.x - b.bounds.x);
    this.publish(next);
  };

  /** Coalesces every trigger (commits, observers, events) into one pass per frame. */
  schedule = (): void => {
    if (this.frame !== undefined) return;
    this.frame = window.requestAnimationFrame(() => {
      this.frame = undefined;
      this.refresh();
    });
  };

  private publish(next: NavTarget[]): void {
    if (sameTargets(next, this.targets)) return;
    this.targets = next;
    for (const listener of this.listeners) listener();
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent<NavTarget[]>("cs:nav-targets", { detail: this.snapshot() }),
      );
    }
  }

  private start(): void {
    if (typeof ResizeObserver !== "undefined") {
      this.observer = new ResizeObserver(this.schedule);
      // A sibling or ancestor can move a target without resizing it: watch the page itself.
      this.observer.observe(document.documentElement);
      this.observer.observe(document.body);
    }
    if (typeof MutationObserver !== "undefined") {
      // One root observer: insertions, label text, visibility and disabled attributes.
      this.mutations = new MutationObserver(this.schedule);
      this.mutations.observe(document.body, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: MUTATION_ATTRIBUTES,
      });
    }
    window.addEventListener("scroll", this.schedule, true);
    window.addEventListener("resize", this.schedule);
    // Transitions and animations move controls without any resize or scroll.
    window.addEventListener("transitionend", this.schedule, true);
    window.addEventListener("animationend", this.schedule, true);
    window.visualViewport?.addEventListener("resize", this.schedule);
    window.visualViewport?.addEventListener("scroll", this.schedule);
  }

  private stop(): void {
    this.observer?.disconnect();
    this.mutations?.disconnect();
    this.observer = undefined;
    this.mutations = undefined;
    window.removeEventListener("scroll", this.schedule, true);
    window.removeEventListener("resize", this.schedule);
    window.removeEventListener("transitionend", this.schedule, true);
    window.removeEventListener("animationend", this.schedule, true);
    window.visualViewport?.removeEventListener("resize", this.schedule);
    window.visualViewport?.removeEventListener("scroll", this.schedule);
    if (this.frame !== undefined) window.cancelAnimationFrame(this.frame);
    this.frame = undefined;
  }
}

/** Default channel for controls outside an explicit provider. */
export const navTargetRegistry = new NavTargetRegistry();
