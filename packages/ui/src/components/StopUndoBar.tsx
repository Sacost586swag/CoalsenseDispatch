import { useLayoutEffect, useRef } from "react";
import { es } from "../i18n/es.ts";
import { Button } from "./Button.tsx";
import { STOP_BAR_ATTRIBUTE } from "./Dialog.tsx";

export interface StopUndoBarProps {
  onStop: () => void;
  onUndo: () => void;
  /** Emits help.request_human in every modality (PA-08, V-04). */
  onHelp: () => void;
  /** With nothing to undo, Deshacer stays visible and focusable but inactive, with its reason. */
  undoAvailable: boolean;
}

const RESERVED = "--stop-bar-reserved";
const NO_UNDO_REASON = "undo.none.reason"; // catalog key, not visible text

/**
 * Fixed, always visible, never covered by a Dialog (AX-05). Its controls register themselves in
 * the navigation registry through Button. It publishes its real height in --stop-bar-reserved so
 * the dialog backdrop and the page content stop above it even when the text wraps.
 */
export function StopUndoBar({ onStop, onUndo, onHelp, undoAvailable }: StopUndoBarProps) {
  const ref = useRef<HTMLElement>(null);
  useLayoutEffect(() => {
    const bar = ref.current;
    if (!bar) return;
    const root = document.documentElement;
    const publish = (): void => {
      const control = bar.querySelector("button") ?? bar;
      const controlFont = Number.parseFloat(window.getComputedStyle(control).fontSize);
      // [SUPUESTO] below 16 control-font units, three columns split even short labels.
      // Width/font does not depend on row height, so the reflow cannot oscillate.
      bar.toggleAttribute(
        "data-cs-compact",
        Number.isFinite(controlFont) && bar.clientWidth < controlFont * 16,
      );
      root.style.setProperty(RESERVED, `${bar.offsetHeight}px`);
    };
    publish();
    // shortcut: without ResizeObserver (jsdom, old WebViews) only the first measure applies.
    const observer =
      typeof ResizeObserver === "undefined" ? undefined : new ResizeObserver(publish);
    observer?.observe(bar);
    return () => {
      observer?.disconnect();
      root.style.removeProperty(RESERVED);
    };
  }, []);
  return (
    <>
      <section
        ref={ref}
        {...{ [STOP_BAR_ATTRIBUTE]: "" }}
        aria-label={es["stopbar.label"]}
        className="cs-stop-bar"
      >
        <Button id="cs-stop" variant="stop" onClick={onStop}>
          {es["stop.label"]}
        </Button>
        <Button
          id="cs-undo"
          disabled={!undoAvailable}
          disabledReason={NO_UNDO_REASON}
          onClick={onUndo}
        >
          {es["undo.label"]}
        </Button>
        <Button id="cs-help" onClick={onHelp}>
          {es["help.label"]}
        </Button>
      </section>
      <div aria-hidden="true" className="cs-stop-bar__spacer" />
    </>
  );
}
