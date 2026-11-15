import { useId } from "react";
import { es } from "../i18n/es.ts";
import { Button } from "./Button.tsx";
import { Progress } from "./Progress.tsx";

const states = {
  loading: { label: es["state.loading.label"], message: es["state.loading.message"] },
  empty: { label: es["state.empty.label"], message: es["state.empty.message"] },
  error: { label: es["state.error.label"], message: es["state.error.message"] },
  offline: { label: es["state.offline.label"], message: es["state.offline.message"] },
  calibration_failed: {
    label: es["state.calibrationFailed.label"],
    message: es["state.calibrationFailed.message"],
  },
  modality_missing: {
    label: es["state.modalityNotDetected.label"],
    message: es["state.modalityNotDetected.message"],
  },
} as const;

export interface StateAction {
  /** Visible text (the accessible name). The screen supplies it; it must work in any modality. */
  label: string;
  onAction: () => void;
}

export interface StateScreenProps {
  state: keyof typeof states;
  /** Plain language that never blames the person (AX-12); defaults to the catalog text. */
  whatHappened?: string;
  /** At least one operable action (AX-11); the first is the screen's one primary action. */
  actions: readonly [StateAction, ...StateAction[]];
  /** What keeps working meanwhile; when empty the catalog says Alto and Deshacer remain. */
  stillWorks?: readonly string[];
}

/** Every state is named in text (never color alone) and the live region stays mounted. */
export function StateScreen({ state, whatHappened, actions, stillWorks = [] }: StateScreenProps) {
  const titleId = useId();
  const { label, message } = states[state];
  return (
    <section
      aria-labelledby={titleId}
      aria-busy={state === "loading" || undefined}
      className="cs-state"
    >
      <h2 id={titleId} className="cs-state__title">
        {label}
      </h2>
      <div className="cs-state__block">
        <h3 className="cs-state__heading">{es["state.whatHappened.label"]}</h3>
        <p role="status" className="cs-state__what">
          {whatHappened ?? message}
        </p>
        {state === "loading" && <Progress label={label} />}
      </div>
      <div className="cs-state__block">
        <h3 className="cs-state__heading">{es["state.actions.label"]}</h3>
        <div className="cs-state__actions">
          {actions.map((action, index) => (
            <Button
              key={action.label}
              variant={index === 0 ? "primary" : "secondary"}
              onClick={action.onAction}
            >
              {action.label}
            </Button>
          ))}
        </div>
      </div>
      <div className="cs-state__block">
        <h3 className="cs-state__heading">{es["state.stillWorks.label"]}</h3>
        {stillWorks.length > 0 ? (
          <ul className="cs-state__list">
            {stillWorks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p>{es["state.stillWorks.default"]}</p>
        )}
      </div>
    </section>
  );
}
