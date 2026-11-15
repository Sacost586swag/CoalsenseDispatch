import { useState, type ReactNode } from "react";
import { es } from "../i18n/es.ts";
import { Button } from "./Button.tsx";

const kind = {
  info: es["status.info.label"],
  success: es["status.success.label"],
  warning: es["status.warning.label"],
  error: es["state.error.label"],
} as const;

export interface StatusBannerProps {
  variant: keyof typeof kind;
  children: ReactNode;
  /** Actions that work in any input modality, e.g. a retry Button (AX-11). */
  actions?: ReactNode;
  /** Default true. The banner never hides on its own; only this action removes it. */
  dismissible?: boolean;
  onDismiss?: () => void;
}

/** No timer anywhere: a notice stays until the person dismisses it (REQ-00-043). */
export function StatusBanner({
  variant,
  children,
  actions,
  dismissible = true,
  onDismiss,
}: StatusBannerProps) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={`cs-banner cs-banner--${variant}`}
    >
      <div className="cs-banner__message">
        <strong className="cs-banner__kind">{kind[variant]}:</strong> {children}
      </div>
      {(actions || dismissible) && (
        <div className="cs-banner__actions">
          {actions}
          {dismissible && (
            <Button
              onClick={() => {
                setDismissed(true);
                onDismiss?.();
              }}
            >
              {es["banner.dismiss.label"]}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
