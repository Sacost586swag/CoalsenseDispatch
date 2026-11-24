"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { es } from "@coalsense/ui";
import { Button } from "@coalsense/ui/components";
import { useWorkspace } from "./state.tsx";
import { Icon } from "./ui.tsx";
import { SpeechOwners } from "./speech-owner.ts";

const NO_VOICE = "workspace.audio.unavailable";
const PAUSED_REASON = "workspace.paused.reason";
const owners = new SpeechOwners();

export function useLocalSpeech(registerStop: (signal: () => void) => () => void) {
  const owner = useRef(Symbol("local-speech"));
  const [voiceURI, setVoiceURI] = useState("");
  const cancel = useCallback(() => {
    return owners.cancel(owner.current);
  }, []);
  useEffect(() => {
    if (typeof speechSynthesis === "undefined") return;
    const update = () => {
      try {
        setVoiceURI(
          speechSynthesis
            .getVoices()
            .find((voice) => voice.localService && /^es(?:-|$)/i.test(voice.lang))?.voiceURI ?? "",
        );
      } catch {
        setVoiceURI("");
      }
    };
    update();
    speechSynthesis.addEventListener("voiceschanged", update);
    return () => {
      speechSynthesis.removeEventListener("voiceschanged", update);
      cancel();
    };
  }, [cancel]);
  useEffect(
    () =>
      registerStop(() => {
        if (!cancel()) throw new Error("Local speech cancellation failed");
      }),
    [registerStop, cancel],
  );
  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      try {
        if (
          typeof speechSynthesis === "undefined" ||
          typeof SpeechSynthesisUtterance === "undefined"
        )
          return false;
        const voice = speechSynthesis
          .getVoices()
          .find(
            (item) =>
              item.voiceURI === voiceURI && item.localService && /^es(?:-|$)/i.test(item.lang),
          );
        if (!voice) return false; // Never let the browser pick a remote fallback voice.
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.voice = voice;
        utterance.lang = voice.lang;
        return owners.start(
          owner.current,
          (ended) => {
            utterance.onend = ended;
            utterance.onerror = ended;
            speechSynthesis.speak(utterance);
          },
          () => speechSynthesis.cancel(),
          () => onEnd?.(),
        );
      } catch {
        onEnd?.();
        return false;
      }
    },
    [voiceURI],
  );
  const pause = useCallback(() => owners.control(owner.current, () => speechSynthesis.pause()), []);
  const resume = useCallback(
    () => owners.control(owner.current, () => speechSynthesis.resume()),
    [],
  );
  return { ready: Boolean(voiceURI), speak, cancel, pause, resume };
}

export function ReadAloud({ text }: { text: string }) {
  const workspace = useWorkspace();
  const speech = useLocalSpeech(workspace.registerStop);
  const [reading, setReading] = useState(false);
  const [paused, setPaused] = useState(false);
  const [failed, setFailed] = useState(false);
  const previousText = useRef(text);
  const readControl = useRef<HTMLButtonElement>(null);
  const pauseControl = useRef<HTMLButtonElement>(null);
  const finish = useCallback(() => {
    if (document.activeElement === pauseControl.current) readControl.current?.focus();
    setReading(false);
    setPaused(false);
  }, []);
  useEffect(
    () =>
      workspace.registerStop(() => {
        setReading(false);
        setPaused(false);
      }),
    [workspace.registerStop],
  );
  useEffect(() => {
    if (previousText.current !== text) {
      if (!speech.cancel()) setFailed(true);
      else {
        setReading(false);
        setPaused(false);
      }
      previousText.current = text;
    }
  }, [text, speech.cancel]);
  return (
    <div className="read-aloud">
      <Button
        ref={readControl}
        disabled={workspace.paused || (!speech.ready && !reading)}
        disabledReason={workspace.paused ? PAUSED_REASON : NO_VOICE}
        aria-pressed={reading}
        onClick={() => {
          if (reading) {
            if (!speech.cancel()) {
              setFailed(true);
              return;
            }
            setReading(false);
            setPaused(false);
            setFailed(false);
            return;
          }
          setFailed(false);
          const started = speech.speak(text, finish);
          setReading(started);
          if (!started) setFailed(true);
        }}
      >
        <Icon variant="voice" />
        {es[reading ? "workspace.audio.stop" : "workspace.audio.read"]}
      </Button>
      {reading && (
        <Button
          ref={pauseControl}
          aria-pressed={paused}
          onClick={() => {
            const changed = paused ? speech.resume() : speech.pause();
            if (!changed) {
              setFailed(true);
              return;
            }
            setPaused(!paused);
            setFailed(false);
          }}
        >
          {es[paused ? "workspace.audio.resume" : "workspace.audio.pause"]}
        </Button>
      )}
      <p role="status" className={failed ? "muted-copy" : "cs-visually-hidden"}>
        {failed ? es["workspace.audio.control.failed"] : ""}
      </p>
    </div>
  );
}
