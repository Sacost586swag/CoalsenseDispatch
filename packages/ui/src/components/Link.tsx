import type { AnchorHTMLAttributes, ReactNode } from "react";

export interface LinkProps extends Omit<
  AnchorHTMLAttributes<HTMLAnchorElement>,
  "title" | "aria-label" | "aria-labelledby"
> {
  href: string;
  /** A disabled link keeps its text and role but has no destination. */
  disabled?: boolean;
  children: ReactNode;
}

export function Link({ href, disabled = false, className, children, ...rest }: LinkProps) {
  const classes = ["cs-link", className].filter(Boolean).join(" ");
  if (disabled) {
    return (
      <a {...rest} role="link" aria-disabled="true" className={classes}>
        {children}
      </a>
    );
  }
  return (
    <a {...rest} href={href} className={classes}>
      {children}
    </a>
  );
}
