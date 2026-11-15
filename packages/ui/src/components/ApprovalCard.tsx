import { useEffect, useId, useRef, type ReactNode } from "react";
import { es } from "../i18n/es.ts";
import { Button } from "./Button.tsx";

export interface ApprovalCardProps {
  /** Plain language: what is being approved. */
  what: string;
  /** Who receives it. */
  recipient: string;
  /** What happens once approved. */
  effect: string;
  /** The exact content to approve (the text, the draft), shown as is. */
  children?: ReactNode;
  onApprove: () => void;
  onReject: () => void;
  onDecideLater: () => void;
}

/**
 * No option is preselected and no action is the primary one: the three have the same weight
 * (reject as easy as approve). Focus starts on the title; nothing here has a timer, so an
 * approval never happens or expires by inaction (AX-03, AX-09).
 */
export function ApprovalCard({
  what,
  recipient,
  effect,
  children,
  onApprove,
  onReject,
  onDecideLater,
}: ApprovalCardProps) {
  const titleId = useId();
  const titleRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => titleRef.current?.focus(), []);
  return (
    <section aria-labelledby={titleId} className="cs-approval">
      <h2 id={titleId} ref={titleRef} tabIndex={-1} className="cs-approval__title">
        {es["approval.title"]}
      </h2>
      <p role="status" className="cs-approval__pending">
        <strong>{es["approval.pending.label"]}.</strong> {es["approval.noExpiry.message"]}
      </p>
      <dl className="cs-approval__facts">
        <dt>{es["approval.what.label"]}</dt>
        <dd>{what}</dd>
        <dt>{es["approval.recipient.label"]}</dt>
        <dd>{recipient}</dd>
        <dt>{es["approval.effect.label"]}</dt>
        <dd>{effect}</dd>
      </dl>
      {children && <div className="cs-approval__content">{children}</div>}
      <div className="cs-approval__actions">
        <Button onClick={onApprove}>{es["approval.approve.label"]}</Button>
        <Button onClick={onReject}>{es["approval.reject.label"]}</Button>
        <Button onClick={onDecideLater}>{es["approval.defer.label"]}</Button>
      </div>
    </section>
  );
}
