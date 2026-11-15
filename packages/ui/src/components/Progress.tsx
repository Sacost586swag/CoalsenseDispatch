import { useId } from "react";
import { es } from "../i18n/es.ts";

export interface ProgressProps {
  label: string;
  /** Omit for an indeterminate (loading) state. Progress only adds: no countdown or loss. */
  value?: number;
  max?: number;
}

export function Progress({ label, value, max = 100 }: ProgressProps) {
  const labelId = useId();
  const current = value === undefined ? undefined : Math.min(Math.max(value, 0), max);
  const percent = current === undefined ? undefined : Math.round((current / max) * 100);
  return (
    <div className="cs-progress">
      <div className="cs-progress__header">
        <span id={labelId} className="cs-progress__label">
          {label}
        </span>
        <span className="cs-progress__value">
          {percent === undefined ? es["state.loading.label"] : `${percent} %`}
        </span>
      </div>
      <div
        role="progressbar"
        aria-labelledby={labelId}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={current}
        className="cs-progress__track"
      >
        <div
          className={
            percent === undefined
              ? "cs-progress__bar cs-progress__bar--indeterminate"
              : "cs-progress__bar"
          }
          style={percent === undefined ? undefined : { inlineSize: `${percent}%` }}
        />
      </div>
    </div>
  );
}
