import type { ButtonHTMLAttributes, ReactNode } from "react";
import { es } from "../i18n/es.ts";

export interface ButtonProps extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "title" | "aria-label" | "aria-labelledby"
> {
  /** One primary action per screen (AX-13); "stop" is reserved for the Alto control. */
  variant?: "primary" | "secondary" | "stop";
  /** Keeps the visible label, adds the catalog "Cargando" text and ignores activation. */
  loading?: boolean;
  children: ReactNode;
}

/** The accessible name is the visible text: aria-label/title are not accepted (WCAG 2.5.3). */
export function Button({
  variant = "secondary",
  loading = false,
  className,
  children,
  onClick,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      type={type}
      className={["cs-button", `cs-button--${variant}`, loading && "cs-button--loading", className]
        .filter(Boolean)
        .join(" ")}
      aria-busy={loading || undefined}
      aria-disabled={loading || undefined}
      onClick={loading ? undefined : onClick}
    >
      {children}
      {loading && <span className="cs-button__status">{es["state.loading.label"]}</span>}
    </button>
  );
}
