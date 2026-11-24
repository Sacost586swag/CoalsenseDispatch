"use client";

import { useState, useTransition } from "react";
import { defineTheme, es, highContrast, stitchTheme, toCssVariables } from "@coalsense/ui";
import { Button, Dialog, Link, StopUndoBar } from "@coalsense/ui/components";
import { Icon, PageHeading, revealFocus } from "./ui.tsx";

const PAUSED_REASON = "workspace.paused.reason";

/** Independent of workspace state: a layout failure may have unmounted its provider. */
export function EmergencyScreen({ retry }: { retry: () => void }) {
  const [contrast, setContrast] = useState(false);
  const [help, setHelp] = useState(false);
  const [stopped, setStopped] = useState(false);
  const [notice, setNotice] = useState("");
  const [pending, startTransition] = useTransition();
  const theme = defineTheme({
    ...stitchTheme,
    color: contrast ? highContrast.color : stitchTheme.color,
    target: { ...stitchTheme.target, min: 64 },
  });
  return (
    <div className="workspace emergency-recovery" data-contrast={contrast}>
      <title>{`${es["workspace.recovery.root.title"]} · ${es["catalog.product"]}`}</title>
      <style data-emergency-theme>{toCssVariables(theme)}</style>
      <header className="workspace-header">
        <div className="workspace-brand">
          <strong>{es["catalog.product"]}</strong>
        </div>
        <Button
          id="recovery-contrast"
          aria-pressed={contrast}
          onClick={() => setContrast(!contrast)}
        >
          <Icon variant="contrast" />
          {es["workspace.contrast"]}
        </Button>
      </header>
      <main className="workspace-main emergency-main" onFocusCapture={revealFocus}>
        <PageHeading title={es["workspace.recovery.root.title"]} />
        <section className="recovery-panel">
          <p role="alert">{es["workspace.recovery.root.body"]}</p>
          <p>{es["workspace.recovery.safety"]}</p>
          <p role="status" className={notice ? "workspace-notice" : "cs-visually-hidden"}>
            {notice}
          </p>
          <div className="screen-actions">
            <Button
              variant="primary"
              disabled={stopped}
              disabledReason={PAUSED_REASON}
              loading={pending}
              onClick={() => startTransition(retry)}
            >
              {es["workspace.recovery.retry"]}
            </Button>
            {stopped && (
              <Button
                onClick={() => {
                  setStopped(false);
                  setNotice("");
                }}
              >
                {es["workspace.recovery.root.enable"]}
              </Button>
            )}
            <Link href="/inicio" className="cs-button cs-button--secondary">
              {es["workspace.recovery.home"]}
            </Link>
          </div>
        </section>
      </main>
      <StopUndoBar
        undoAvailable={false}
        onUndo={() => {}}
        onStop={() => {
          setStopped(true);
          try {
            if (typeof speechSynthesis !== "undefined") speechSynthesis.cancel();
            setNotice(es["workspace.recovery.root.stop"]);
          } catch {
            setNotice(es["workspace.recovery.root.stop.failed"]);
          }
        }}
        onHelp={() => setHelp(true)}
      />
      <Dialog
        open={help}
        title={es["help.label"]}
        actions={<Button onClick={() => setHelp(false)}>{es["workspace.close"]}</Button>}
      >
        <p>{es["workspace.help.body"]}</p>
      </Dialog>
    </div>
  );
}
