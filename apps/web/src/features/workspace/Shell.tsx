"use client";

import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { defineTheme, es, highContrast, stitchTheme, toCssVariables } from "@coalsense/ui";
import { Button, Dialog, StopUndoBar } from "@coalsense/ui/components";
import { useWorkspace } from "./state.tsx";
import { useLocalSpeech } from "./speech.tsx";
import { Icon, revealFocus, RouteButton } from "./ui.tsx";

const navigation = [
  ["/inicio", "workspace.nav.home"],
  ["/tareas", "workspace.nav.tasks"],
  ["/autonomia", "workspace.nav.autonomy"],
  ["/logros", "workspace.nav.achievements"],
  ["/cuidador", "workspace.nav.caregiver"],
  ["/ajustes", "workspace.nav.settings"],
] as const;

export function WorkspaceShell({ children }: { children: ReactNode }) {
  const workspace = useWorkspace();
  const speech = useLocalSpeech(workspace.registerStop);
  useEffect(() => {
    if (workspace.audioAlerts && workspace.notice) speech.speak(workspace.notice);
  }, [workspace.audioAlerts, workspace.notice, speech.speak]);
  const path = usePathname();
  const strip = useRef<HTMLDivElement>(null);
  const [help, setHelp] = useState(false);
  const [offline, setOffline] = useState(false);
  const theme = defineTheme({
    ...stitchTheme,
    color: workspace.contrast ? highContrast.color : stitchTheme.color,
    textScale: workspace.largeText ? 1.25 : 1,
    target: { ...stitchTheme.target, min: workspace.data.mode === "head" ? 64 : 44 },
  });
  useLayoutEffect(() => {
    const element = strip.current;
    if (!element) return;
    const root = document.documentElement;
    const publish = () =>
      root.style.setProperty("--workspace-input-height", `${element.offsetHeight}px`);
    root.classList.add("workspace-active");
    publish();
    const observer = new ResizeObserver(publish);
    observer.observe(element);
    return () => {
      observer.disconnect();
      root.classList.remove("workspace-active");
      root.style.removeProperty("--workspace-input-height");
    };
  }, []);
  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    addEventListener("online", update);
    addEventListener("offline", update);
    return () => {
      removeEventListener("online", update);
      removeEventListener("offline", update);
    };
  }, []);
  return (
    <div className="workspace" data-contrast={workspace.contrast} data-input={workspace.data.mode}>
      <style data-workspace-theme>{toCssVariables(theme)}</style>
      <header className="workspace-header">
        <div className="workspace-brand">
          <strong>{es["catalog.product"]}</strong>
          <span>{es["workspace.brand.subtitle"]}</span>
        </div>
        <nav aria-label={es["workspace.nav.label"]}>
          {navigation.map(([href, label]) => (
            <RouteButton
              key={href}
              href={href}
              current={path.startsWith(href)}
              className={path.startsWith(href) ? "nav-item is-current" : "nav-item"}
            >
              {es[label]}
            </RouteButton>
          ))}
        </nav>
        <div className="workspace-tools">
          <span className="language-tag">{es["workspace.language"]}</span>
          <Button
            id="workspace-contrast"
            aria-pressed={workspace.contrast}
            onClick={() => workspace.setContrast(!workspace.contrast)}
          >
            <Icon variant="contrast" />
            {es["workspace.contrast"]}
          </Button>
          <Button id="workspace-help" onClick={() => setHelp(true)}>
            <Icon variant="help" />
            {es["workspace.help"]}
          </Button>
          <RouteButton href="/" className="account-button">
            <Icon variant="user" />
            {es["workspace.nav.account"]}
          </RouteButton>
        </div>
      </header>
      <main className="workspace-main" onFocusCapture={revealFocus}>
        <p
          role="status"
          className={
            workspace.navigating ? "workspace-notice navigation-notice" : "cs-visually-hidden"
          }
        >
          {workspace.navigating ? es["workspace.recovery.loading.body"] : ""}
        </p>
        {offline && (
          <div className="workspace-notice" role="status">
            <p>{es["workspace.offline"]}</p>
            <Button onClick={() => setOffline(!navigator.onLine)}>
              {es["workspace.connection.check"]}
            </Button>
          </div>
        )}
        {workspace.notice && (
          <p className="workspace-notice" role="status">
            {workspace.notice}
          </p>
        )}
        {workspace.paused && (
          <div className="pause-panel">
            <Icon variant="pause" />
            <strong>{es["workspace.pause.label"]}</strong>
            <Button id="workspace-resume" variant="primary" onClick={workspace.resume}>
              {es["workspace.resume"]}
            </Button>
          </div>
        )}
        {children}
      </main>
      <div className="workspace-input-strip" ref={strip}>
        <Icon variant="keyboard" />
        <div>
          <strong>{es["workspace.keyboard"]}</strong>
          <span>{es["workspace.input.manual"]}</span>
        </div>
        <span className="input-status">
          {es[workspace.data.mode === "keyboard" ? "workspace.local" : "workspace.not.connected"]}
        </span>
        <RouteButton href="/bienvenida">{es["workspace.input.change"]}</RouteButton>
      </div>
      <StopUndoBar
        onStop={workspace.stop}
        onUndo={workspace.undo}
        onHelp={() => setHelp(true)}
        undoAvailable={workspace.canUndo}
      />
      <Dialog
        open={help}
        title={es["help.label"]}
        actions={
          <Button id="workspace-help-close" onClick={() => setHelp(false)}>
            {es["workspace.close"]}
          </Button>
        }
      >
        <p>{es["workspace.help.body"]}</p>
      </Dialog>
    </div>
  );
}
