"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Button,
  Dialog,
  StateScreen,
  StatusBanner,
  StopUndoBar,
  TextField,
} from "@coalsense/ui/components";
import { stitchTheme, es, highContrast, toCssVariables } from "@coalsense/ui";

type Stage = "email" | "code" | "session";
type Failure = { code: string; message_es: string };

export function AuthApp() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>("email");
  const [email, setEmail] = useState("");
  const [device, setDevice] = useState<string>(es["auth.device.default"]);
  const [code, setCode] = useState("");
  const [pairCode, setPairCode] = useState("");
  const [paired, setPaired] = useState(false);
  const [busy, setBusy] = useState(true);
  const [offline, setOffline] = useState(false);
  const [error, setError] = useState<Failure | null>(null);
  const [notice, setNotice] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [help, setHelp] = useState(false);
  const [contrast, setContrast] = useState(false);
  const pending = useRef<AbortController | null>(null);
  const title = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    addEventListener("online", update);
    addEventListener("offline", update);
    const controller = new AbortController();
    pending.current = controller;
    void fetch("/api/auth/session", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (controller.signal.aborted) return;
        if (response.ok) setStage("session");
        else if (response.status !== 401) {
          const result: Failure = await response.json();
          if (!controller.signal.aborted) setError(result);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError({ code: "auth.unavailable", message_es: es["auth.unavailable.message"] });
      })
      .finally(() => {
        if (pending.current === controller) {
          pending.current = null;
          setBusy(false);
        }
      });
    return () => {
      controller.abort();
      pending.current?.abort();
      removeEventListener("online", update);
      removeEventListener("offline", update);
    };
  }, []);

  useEffect(() => {
    const style = document.querySelector<HTMLStyleElement>("style[data-cs-theme]");
    if (style) style.textContent = toCssVariables(contrast ? highContrast : stitchTheme);
  }, [contrast]);

  useEffect(() => {
    title.current?.focus();
  }, [stage, paired]);

  const stop = () => {
    pending.current?.abort();
    pending.current = null;
    setBusy(false);
    setNotice(es["auth.stopped.message"]);
  };

  async function send(action: string, body: Record<string, string>, success: () => void) {
    if (pending.current) return;
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true);
    setError(null);
    setNotice("");
    setFieldError("");
    try {
      const response = await fetch(`/api/auth/${action}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      if (!response.ok) {
        const result: Failure = await response.json();
        if (controller.signal.aborted) return;
        setError(result);
        if (response.status === 401) {
          setStage("email");
          setCode("");
          setPairCode("");
          setPaired(false);
        }
        return;
      }
      success();
    } catch {
      if (!controller.signal.aborted)
        setError({ code: "auth.unavailable", message_es: es["auth.unavailable.message"] });
    } finally {
      if (pending.current === controller) {
        pending.current = null;
        setBusy(false);
      }
    }
  }

  function requestCode() {
    if (!email.includes("@") || !email.trim() || !device.trim()) {
      setFieldError(es["auth.field.emailError"]);
      return;
    }
    void send("request-code", { email: email.trim() }, () => {
      setStage("code");
      setCode("");
      setNotice(es["auth.code.sent"]);
    });
  }

  function verifyCode() {
    if (!code.trim()) {
      setFieldError(es["auth.field.required"]);
      return;
    }
    void send(
      "verify-code",
      { email: email.trim(), code: code.trim(), device_label: device.trim() },
      () => {
        setStage("session");
        setCode("");
        setEmail("");
        setPaired(false);
      },
    );
  }

  function pair() {
    if (!pairCode.trim()) {
      setFieldError(es["auth.field.required"]);
      return;
    }
    void send("pair", { code: pairCode.trim() }, () => {
      setPaired(true);
      setPairCode("");
    });
  }

  const retry = () => {
    if (stage === "email") requestCode();
    else if (stage === "code") verifyCode();
    else pair();
  };
  const heading = paired
    ? es["auth.pair.pending.title"]
    : stage === "email"
      ? es["auth.signIn.title"]
      : stage === "code"
        ? es["auth.code.title"]
        : es["auth.signedIn.title"];

  return (
    <>
      <header className="app-header">
        <p>{es["catalog.product"]}</p>
        <Button id="auth-onboarding" onClick={() => router.push("/bienvenida")}>
          {es["workspace.onboarding.open"]}
        </Button>
        <Button
          id="auth-contrast"
          onClick={() => setContrast((value) => !value)}
          aria-pressed={contrast}
        >
          {es["auth.theme.label"]}
        </Button>
      </header>
      <main className="auth-main">
        <div className="auth-intro">
          <h1>{es["auth.app.title"]}</h1>
          <p>{es["auth.app.intro"]}</p>
        </div>
        <section className="auth-panel" aria-labelledby="auth-heading">
          <h2 id="auth-heading" ref={title} tabIndex={-1}>
            {heading}
          </h2>
          {notice && (
            <StatusBanner key={notice} variant="info">
              {notice}
            </StatusBanner>
          )}
          {offline && (
            <StateScreen
              state="offline"
              whatHappened={es["auth.offline.message"]}
              actions={[{ label: es["auth.retry.label"], onAction: retry }]}
            />
          )}
          {error && (
            <StatusBanner key={error.code + error.message_es} variant="error" dismissible={false}>
              {error.message_es}
            </StatusBanner>
          )}
          {busy && <p role="status">{es["auth.loading.message"]}</p>}
          {stage === "email" && (
            <form
              noValidate
              onSubmit={(event) => {
                event.preventDefault();
                requestCode();
              }}
            >
              <TextField
                id="auth-email"
                label={es["auth.email.label"]}
                hint={es["auth.email.hint"]}
                type="email"
                autoComplete="email"
                autoCapitalize="none"
                maxLength={254}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                error={fieldError || undefined}
              />
              <TextField
                id="auth-device"
                label={es["auth.device.label"]}
                maxLength={80}
                value={device}
                onChange={(event) => setDevice(event.target.value)}
              />
              <Button id="auth-request" type="submit" variant="primary" loading={busy}>
                {es["auth.request.label"]}
              </Button>
            </form>
          )}
          {stage === "code" && (
            <form
              noValidate
              onSubmit={(event) => {
                event.preventDefault();
                verifyCode();
              }}
            >
              <TextField
                id="auth-code"
                label={es["auth.code.label"]}
                hint={es["auth.code.hint"]}
                autoComplete="one-time-code"
                autoCapitalize="none"
                maxLength={32}
                value={code}
                onChange={(event) => setCode(event.target.value)}
                error={fieldError || undefined}
              />
              <div className="auth-actions">
                <Button id="auth-verify" type="submit" variant="primary" loading={busy}>
                  {es["auth.verify.label"]}
                </Button>
                <Button id="auth-resend" disabled={busy} onClick={requestCode}>
                  {es["auth.newCode.label"]}
                </Button>
                <Button
                  id="auth-other-email"
                  disabled={busy}
                  onClick={() => {
                    setStage("email");
                    setCode("");
                    setNotice("");
                    setFieldError("");
                    setError(null);
                  }}
                >
                  {es["auth.otherEmail.label"]}
                </Button>
              </div>
            </form>
          )}
          {stage === "session" && (
            <>
              <p>{paired ? es["auth.pair.pending.body"] : es["auth.signedIn.body"]}</p>
              {!paired ? (
                <form
                  noValidate
                  onSubmit={(event) => {
                    event.preventDefault();
                    pair();
                  }}
                >
                  <h3>{es["auth.pair.title"]}</h3>
                  <TextField
                    id="auth-pair-code"
                    label={es["auth.pair.code.label"]}
                    hint={es["auth.pair.hint"]}
                    autoComplete="off"
                    autoCapitalize="none"
                    maxLength={32}
                    value={pairCode}
                    onChange={(event) => setPairCode(event.target.value)}
                    error={fieldError || undefined}
                  />
                  <Button id="auth-pair" type="submit" variant="primary" loading={busy}>
                    {es["auth.pair.label"]}
                  </Button>
                </form>
              ) : (
                <Button id="auth-pair-another" onClick={() => setPaired(false)}>
                  {es["auth.pair.another.label"]}
                </Button>
              )}
              <div className="auth-actions">
                <Button
                  id="auth-sign-out"
                  disabled={busy}
                  onClick={() => {
                    void send("sign-out", {}, () => {
                      setStage("email");
                      setPaired(false);
                      setPairCode("");
                    });
                  }}
                >
                  {es["auth.signOut.label"]}
                </Button>
                <Button
                  id="auth-workspace"
                  variant="primary"
                  onClick={() => router.push("/inicio")}
                >
                  {es["workspace.account.enter"]}
                </Button>
              </div>
            </>
          )}
          <p className="auth-privacy">{es["auth.privacy.note"]}</p>
        </section>
      </main>
      <StopUndoBar
        onStop={stop}
        onUndo={() => {}}
        onHelp={() => setHelp(true)}
        undoAvailable={false}
      />
      <Dialog
        open={help}
        title={es["help.label"]}
        actions={
          <Button id="auth-help-close" onClick={() => setHelp(false)}>
            {es["auth.help.close"]}
          </Button>
        }
      >
        <p>{es["auth.help.notConfigured"]}</p>
      </Dialog>
    </>
  );
}
