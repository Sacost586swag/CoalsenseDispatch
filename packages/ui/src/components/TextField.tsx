import { useId, type InputHTMLAttributes } from "react";
import { es } from "../i18n/es.ts";

export interface TextFieldProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "aria-label" | "aria-labelledby" | "title" | "placeholder"
> {
  /** Always visible and the accessible name; a placeholder is never a label. */
  label: string;
  hint?: string;
  /** Message in plain language; shown with the catalog "Error" word, never by color alone. */
  error?: string;
  /** `disabled` keeps focus (aria-disabled + readOnly); this catalog key says why. */
  disabledReason?: keyof typeof es;
}

export function TextField({
  label,
  hint,
  error,
  disabled = false,
  disabledReason,
  id,
  className,
  "aria-describedby": describedByProp,
  ...rest
}: TextFieldProps) {
  const generated = useId();
  const inputId = id ?? generated;
  const hintId = `${inputId}-hint`;
  const errorId = `${inputId}-error`;
  const reasonId = `${inputId}-reason`;
  const reason = disabled && disabledReason ? es[disabledReason] : undefined;
  const describedBy = [describedByProp, hint && hintId, error && errorId, reason && reasonId]
    .filter(Boolean)
    .join(" ");
  return (
    <div className="cs-field">
      <label htmlFor={inputId} className="cs-field__label">
        {label}
      </label>
      {hint && (
        <p id={hintId} className="cs-field__hint">
          {hint}
        </p>
      )}
      <input
        {...rest}
        id={inputId}
        className={["cs-input", error && "cs-input--error", className].filter(Boolean).join(" ")}
        readOnly={disabled || rest.readOnly}
        aria-disabled={disabled || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy || undefined}
      />
      {reason && (
        <p id={reasonId} className="cs-field__hint">
          {reason}
        </p>
      )}
      {error && (
        <p id={errorId} role="status" className="cs-field__error">
          <strong>{es["state.error.label"]}:</strong> {error}
        </p>
      )}
    </div>
  );
}
