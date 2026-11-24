"use client";

import {
  useEffect,
  useRef,
  type FocusEvent,
  type ReactNode,
  type TextareaHTMLAttributes,
} from "react";
import { es, useNavTarget } from "@coalsense/ui";
import { Link } from "@coalsense/ui/components";
import { useWorkspace } from "./state.tsx";

export type IconName =
  | "home"
  | "tasks"
  | "check"
  | "voice"
  | "head"
  | "eye"
  | "keyboard"
  | "arrow"
  | "mail"
  | "document"
  | "social"
  | "shield"
  | "settings"
  | "contrast"
  | "help"
  | "user"
  | "clock"
  | "pause";
const paths: Record<IconName, ReactNode> = {
  home: (
    <>
      <path d="m3 10 9-7 9 7v10H3Z" />
      <path d="M9 20v-7h6v7" />
    </>
  ),
  tasks: (
    <>
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <path d="M9 3h6v4H9zm0 9h6m-6 4h6" />
    </>
  ),
  check: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m7 12 3 3 7-7" />
    </>
  ),
  voice: (
    <>
      <rect x="9" y="2" width="6" height="13" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0m-7 7v4m-4 0h8" />
    </>
  ),
  head: (
    <>
      <path d="M7 20v-4c-5-7-1-14 6-13 6 1 5 5 8 9h-4v6h-5v3" />
      <path d="M10 8h3" />
    </>
  ),
  eye: (
    <>
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  keyboard: (
    <>
      <rect x="2" y="5" width="20" height="14" rx="2" />
      <path d="M6 9h1m4 0h1m4 0h1M6 13h1m4 0h1m4 0h1m-9 3h8" />
    </>
  ),
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 6 9 7 9-7" />
    </>
  ),
  document: (
    <>
      <path d="M5 3h10l4 4v14H5Z" />
      <path d="M14 3v5h5M8 12h8m-8 4h6" />
    </>
  ),
  social: (
    <>
      <path d="M5 4h14v12H9l-4 4Z" />
      <path d="M8 8h8m-8 4h5" />
    </>
  ),
  shield: (
    <>
      <path d="m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6Z" />
      <path d="m8 11 3 3 5-6" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2" />
    </>
  ),
  contrast: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3v18" />
      <path d="M12 3a9 9 0 0 1 0 18Z" fill="currentColor" />
    </>
  ),
  help: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9 8a3 3 0 1 1 4 3v3m-1 3h.01" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21v-3c0-6 16-6 16 0v3Z" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 6v6l4 2" />
    </>
  ),
  pause: (
    <>
      <path d="M8 5v14m8-14v14" />
    </>
  ),
};
export function Icon({ variant, className = "" }: { variant: IconName; className?: string }) {
  return (
    <svg
      className={`workspace-icon ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[variant]}
    </svg>
  );
}
export function RouteButton({
  href,
  children,
  primary = false,
  className = "",
  onNavigate,
  current = false,
  disabled = false,
  disabledReason,
}: {
  href: string;
  children: ReactNode;
  primary?: boolean;
  className?: string;
  onNavigate?: () => void;
  current?: boolean;
  disabled?: boolean;
  disabledReason?: keyof typeof es;
}) {
  const workspace = useWorkspace();
  return (
    <Link
      className={`cs-button cs-button--${primary ? "primary" : "secondary"} ${className}`}
      href={href}
      disabled={disabled}
      disabledReason={disabledReason}
      aria-current={current ? "page" : undefined}
      onClick={(event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        onNavigate?.();
        workspace.navigate(href);
      }}
    >
      {children}
    </Link>
  );
}
export function VoiceCue({ children }: { children: ReactNode }) {
  return (
    <span className="voice-cue" aria-hidden="true">
      <span>{es["workspace.say"]}</span> {children}
    </span>
  );
}
export function PageHeading({ title, body }: { title: string; body?: string }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, [title]);
  return (
    <header className="page-heading">
      <h1 ref={heading} tabIndex={-1}>
        {title}
      </h1>
      {body && <p>{body}</p>}
    </header>
  );
}

/** Browser focus scrolling does not account for our fixed safety controls. */
export function revealFocus(event: FocusEvent<HTMLElement>) {
  const target = event.target;
  const boundary =
    document.querySelector(".workspace-input-strip") ??
    document.querySelector("[data-cs-stop-bar]");
  if (!(target instanceof HTMLElement) || !boundary) return;
  const bottom = boundary.getBoundingClientRect().top;
  const bounds = target.getBoundingClientRect();
  if (bounds.bottom > bottom || bounds.top < 0) {
    target.scrollIntoView({
      block: bounds.height > bottom ? "start" : "nearest",
      inline: "nearest",
      behavior: "instant",
    });
  }
}
export function Area({
  label,
  hint,
  error,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & {
  id: string;
  label: string;
  hint?: string;
  error?: string;
}) {
  const ref = useNavTarget<HTMLTextAreaElement>({ id: props.id, role: "textbox" });
  return (
    <div className="workspace-field">
      <label htmlFor={props.id}>{label}</label>
      {hint && <p id={`${props.id}-hint`}>{hint}</p>}
      <textarea
        {...props}
        ref={ref}
        aria-invalid={error ? true : props["aria-invalid"]}
        aria-describedby={
          [props["aria-describedby"], hint && `${props.id}-hint`, error && `${props.id}-error`]
            .filter(Boolean)
            .join(" ") || undefined
        }
      />
      {error && (
        <p id={`${props.id}-error`} role="alert">
          {es["state.error.label"]}: {error}
        </p>
      )}
    </div>
  );
}
