import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

/**
 * Mark the Alto and Deshacer bar with this attribute (T-00-015). While a Dialog is open the bar
 * stays visible (the backdrop stops above it, see --stop-bar-reserved in components.css), above
 * the backdrop (--layer-stop-bar) and inside the Tab cycle (AX-05).
 */
export const STOP_BAR_ATTRIBUTE = "data-cs-stop-bar";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface DialogProps {
  open: boolean;
  title: string;
  children: ReactNode;
  /** Buttons for the person to decide; every dialog needs at least one way out. */
  actions: ReactNode;
  onClose?: () => void;
  /** Escape closes only when the person asked for it (a setting); default off. */
  closeOnEscape?: boolean;
}

/** Modal that never closes by itself, by backdrop click or by a timer. */
export function Dialog({
  open,
  title,
  children,
  actions,
  onClose,
  closeOnEscape = false,
}: DialogProps) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef({ onClose, closeOnEscape });
  closeRef.current = { onClose, closeOnEscape };

  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    dialogRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent): void => {
      const dialog = dialogRef.current;
      if (!dialog) return;
      if (event.key === "Escape") {
        const { onClose: close, closeOnEscape: allowed } = closeRef.current;
        if (allowed && close) close();
        return;
      }
      if (event.key !== "Tab") return;
      const inBar = Array.from(document.querySelectorAll(`[${STOP_BAR_ATTRIBUTE}]`)).flatMap(
        (bar) => Array.from(bar.querySelectorAll<HTMLElement>(FOCUSABLE)),
      );
      const cycle = [...Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE)), ...inBar];
      if (cycle.length === 0) return;
      event.preventDefault();
      const index = cycle.indexOf(document.activeElement as HTMLElement);
      const step = event.shiftKey ? -1 : 1;
      const next =
        index === -1
          ? event.shiftKey
            ? cycle.length - 1
            : 0
          : (index + step + cycle.length) % cycle.length;
      cycle[next]?.focus();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      if (opener?.isConnected) opener.focus();
    };
  }, [open]);

  if (!open || typeof document === "undefined") return null;
  return createPortal(
    <div className="cs-dialog__backdrop">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="cs-dialog"
      >
        <h2 id={titleId} className="cs-dialog__title">
          {title}
        </h2>
        <div className="cs-dialog__body">{children}</div>
        {actions && <div className="cs-dialog__actions">{actions}</div>}
      </div>
    </div>,
    document.body,
  );
}
