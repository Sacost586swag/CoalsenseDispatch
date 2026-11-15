import { useId, type AnchorHTMLAttributes, type MouseEvent, type ReactNode, type Ref } from "react";
import { es } from "../i18n/es.ts";
import { useNavTarget } from "../nav/useNavTarget.ts";

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
  /** Merged with the navigation-target registration (React 19 passes `ref` as a prop). */
  ref?: Ref<HTMLAnchorElement>;
}

export function Link({
  href,
  disabled = false,
  disabledReason,
  className,
  children,
  onClick,
  "aria-describedby": describedBy,
  ref,
  ...rest
}: LinkProps) {
  const reasonId = useId();
  const navRef = useNavTarget<HTMLAnchorElement>({ id: rest.id, role: "link", ref });
  const classes = ["cs-link", className].filter(Boolean).join(" ");
  if (disabled) {
    const reason = disabledReason ? es[disabledReason] : undefined;
    return (
      <>
        <a
          {...rest}
          ref={navRef}
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
      ref={navRef}
      href={href}
      aria-describedby={describedBy}
      className={classes}
      onClick={onClick}
    >
      {children}
    </a>
  );
}
