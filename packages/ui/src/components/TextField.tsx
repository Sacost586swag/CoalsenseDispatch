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
}

export function TextField({ label, hint, error, id, className, ...rest }: TextFieldProps) {
  const generated = useId();
  const inputId = id ?? generated;
  const hintId = `${inputId}-hint`;
  const errorId = `${inputId}-error`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ");
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
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy || undefined}
      />
      {error && (
        <p id={errorId} className="cs-field__error">
          <strong>{es["state.error.label"]}:</strong> {error}
        </p>
      )}
    </div>
  );
}
