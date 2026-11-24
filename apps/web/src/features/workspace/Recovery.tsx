"use client";

import { useTransition } from "react";
import { es } from "@coalsense/ui";
import { Button } from "@coalsense/ui/components";
import { WorkspaceProvider } from "./state.tsx";
import { WorkspaceShell } from "./Shell.tsx";
import { Icon, PageHeading, RouteButton } from "./ui.tsx";

const copy = {
  loading: { title: "workspace.recovery.loading.title", body: "workspace.recovery.loading.body" },
  error: { title: "workspace.recovery.error.title", body: "workspace.recovery.error.body" },
  missing: { title: "workspace.recovery.missing.title", body: "workspace.recovery.missing.body" },
} as const;

/** Does not inspect, render or forward an exception that could contain private input. */
export function RecoveryScreen({ state, retry }: { state: keyof typeof copy; retry?: () => void }) {
  const [pending, startTransition] = useTransition();
  return (
    <div className="recovery-screen">
      <PageHeading title={es[copy[state].title]} />
      <section className="recovery-panel" aria-busy={state === "loading" || pending || undefined}>
        <span className="icon-tile">
          <Icon variant={state === "loading" ? "clock" : "document"} />
        </span>
        <p role={state === "error" ? "alert" : "status"}>{es[copy[state].body]}</p>
        <p className="muted-copy">{es["workspace.recovery.safety"]}</p>
        <div className="screen-actions">
          {retry && (
            <Button variant="primary" loading={pending} onClick={() => startTransition(retry)}>
              {es["workspace.recovery.retry"]}
            </Button>
          )}
          <RouteButton href="/inicio" primary={!retry}>
            {es["workspace.recovery.home"]}
          </RouteButton>
        </div>
      </section>
    </div>
  );
}

/** Unmatched URLs have no workspace layout. They still need the safety controls. */
export function MissingScreen() {
  return (
    <WorkspaceProvider>
      <WorkspaceShell>
        <RecoveryScreen state="missing" />
      </WorkspaceShell>
    </WorkspaceProvider>
  );
}
