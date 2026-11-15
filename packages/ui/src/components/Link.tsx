import { useId, type AnchorHTMLAttributes, type MouseEvent, type ReactNode } from "react";
import { es } from "../i18n/es.ts";

export interface LinkProps extends Omit<
  AnchorHTMLAttributes<HTMLAnchorElement>,
  "title" | "aria-label" | "aria-labelledby"
> {
  href: string;
  /** Keeps text, role and focus but has no destination and ignores onClick. */
  disabled?: boolean;
  /** Catalog key of the visible text that says why it is disabled and what still works. */
  disabledReason?: keyof typeof es;
  children: ReactNode;
}

export function Link({
  href,
  disabled = false,
  disabledReason,
  className,
  children,
  onClick,
  "aria-describedby": describedBy,
  ...rest
}: LinkProps) {
  const reasonId = useId();
  const classes = ["cs-link", className].filter(Boolean).join(" ");
  if (disabled) {
    const reason = disabledReason ? es[disabledReason] : undefined;
    return (
      <>
        <a
          {...rest}
          role="link"
          tabIndex={0}
          aria-disabled="true"
          aria-describedby={
            [describedBy, reason && reasonId].filter(Boolean).join(" ") || undefined
          }
          className={classes}
          onClick={(event: MouseEvent<HTMLAnchorElement>) => event.preventDefault()}
        >
          {children}
        </a>
        {reason && (
          <span id={reasonId} className="cs-reason">
            {reason}
          </span>
        )}
      </>
    );
  }
  return (
    <a
      {...rest}
      href={href}
      aria-describedby={describedBy}
      className={classes}
      onClick={onClick}
    >
      {children}
    </a>
  );
}
