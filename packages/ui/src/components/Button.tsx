import { useId, type ButtonHTMLAttributes, type MouseEvent, type ReactNode, type Ref } from "react";
import { es } from "../i18n/es.ts";
import { useNavTarget } from "../nav/useNavTarget.ts";

export interface ButtonProps extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "title" | "aria-label" | "aria-labelledby"
> {
  /** One primary action per screen (AX-13); "stop" is reserved for the Alto control. */
  variant?: "primary" | "secondary" | "stop";
  /**
   * Keeps the visible label, adds the catalog "Cargando" text, blocks click and submit, and
   * announces it politely in a live region that is always mounted (so the change is read).
   */
  loading?: boolean;
  /**
   * `disabled` keeps the control in the focus order (aria-disabled, guarded handler) instead of
   * the native attribute, so the person can still reach it and learn why (AX-11).
   */
  disabled?: boolean;
  /** Catalog key of the visible text that says why it is disabled and what still works. */
  disabledReason?: keyof typeof es;
  children: ReactNode;
  /** Merged with the navigation-target registration (React 19 passes `ref` as a prop). */
  ref?: Ref<HTMLButtonElement>;
}

/** The accessible name is the visible text: aria-label/title are not accepted (WCAG 2.5.3). */
export function Button({
  variant = "secondary",
  loading,
  disabled = false,
  disabledReason,
  className,
  children,
  onClick,
  "aria-describedby": describedBy,
  type = "button",
  ref,
  ...rest
}: ButtonProps) {
  const navRef = useNavTarget<HTMLButtonElement>({ id: rest.id, role: "button", ref });
  const reasonId = useId();
  const inactive = Boolean(loading) || disabled;
  const reason = disabled && disabledReason ? es[disabledReason] : undefined;
  const guard = (event: MouseEvent<HTMLButtonElement>): void => {
    if (inactive) {
      event.preventDefault(); // also stops a type="submit" from submitting the form
      return;
    }
    onClick?.(event);
  };
  return (
    <>
      <button
        {...rest}
        ref={navRef}
        type={type}
        className={[
          "cs-button",
          `cs-button--${variant}`,
          loading && "cs-button--loading",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        aria-busy={loading || undefined}
        aria-disabled={inactive || undefined}
        aria-describedby={[describedBy, reason && reasonId].filter(Boolean).join(" ") || undefined}
        onClick={guard}
      >
        {children}
        {loading && <span className="cs-button__status">{es["state.loading.label"]}</span>}
      </button>
      {reason && (
        <span id={reasonId} className="cs-reason">
          {reason}
        </span>
      )}
      <span role="status" className="cs-visually-hidden">
        {loading ? es["state.loading.label"] : ""}
      </span>
    </>
  );
}
