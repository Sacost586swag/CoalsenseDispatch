import type { HTMLAttributes } from "react";
import { es } from "../i18n/es.ts";

export interface StepperProps extends Omit<HTMLAttributes<HTMLOListElement>, "children"> {
  steps: readonly { key: string; label: string }[];
  /** Zero-based current step. Display only: it never advances by itself. */
  current: number;
}

const stateLabel = {
  done: es["step.done.label"],
  current: es["step.current.label"],
  pending: es["step.pending.label"],
} as const;

export function Stepper({ steps, current, className, ...rest }: StepperProps) {
  const active = Math.min(Math.max(current, 0), steps.length - 1);
  return (
    <ol {...rest} role="list" className={["cs-stepper", className].filter(Boolean).join(" ")}>
      {steps.map((step, index) => {
        const state = index < active ? "done" : index === active ? "current" : "pending";
        return (
          <li
            key={step.key}
            aria-current={state === "current" ? "step" : undefined}
            className={`cs-stepper__step cs-stepper__step--${state}`}
          >
            <span className="cs-stepper__number" aria-hidden="true">
              {index + 1}
            </span>
            <span className="cs-stepper__label">{step.label}</span>
            <span className="cs-stepper__state">{stateLabel[state]}</span>
          </li>
        );
      })}
    </ol>
  );
}
