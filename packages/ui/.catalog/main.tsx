import { useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ApprovalCard,
  Button,
  Dialog,
  Link,
  NumberedList,
  Progress,
  StateScreen,
  StatusBanner,
  Stepper,
  StopUndoBar,
  TextField,
} from "../src/components/index.ts";
import { defaultTheme, es, highContrast, toCssVariables } from "../src/index.ts";
import { cases } from "./cases.ts";
import type { StateScreenProps } from "../src/components/StateScreen.tsx";
import "../src/fonts/fonts.css";
import "../src/components/components.css";
import "./styles.css";

const params = new URLSearchParams(location.search);
const selected = params.get("case") ?? cases[0];
const theme = params.get("theme") === "contrast" ? highContrast : defaultTheme;
const themeStyle = document.createElement("style");
themeStyle.textContent = toCssVariables(theme);
document.head.append(themeStyle);
if (params.get("mode") === "head") document.documentElement.dataset.inputMode = "head";

function Catalog() {
  const [open, setOpen] = useState(selected === "dialog-open");
  const [feedback, setFeedback] = useState("");
  const report = () => setFeedback(es["catalog.actionDone"]);
  const label = es["catalog.continue"];
  let example;
  if (selected.startsWith("button-")) {
    example = (
      <Button
        variant={selected === "button-primary" ? "primary" : "secondary"}
        disabled={selected === "button-disabled"}
        disabledReason="catalog.disabledReason"
        loading={selected === "button-loading"}
        onClick={report}
      >
        {label}
      </Button>
    );
  } else if (selected.startsWith("link-")) {
    example = (
      <Link
        href="?case=button-normal"
        disabled={selected === "link-disabled"}
        disabledReason="catalog.disabledReason"
      >
        {es["catalog.back"]}
      </Link>
    );
  } else if (selected.startsWith("field-")) {
    example = (
      <TextField
        label={es["catalog.field"]}
        hint={es["catalog.fieldHint"]}
        disabled={selected === "field-disabled"}
        disabledReason="catalog.disabledReason"
        error={selected === "field-error" ? es["catalog.fieldError"] : undefined}
      />
    );
  } else if (selected.startsWith("dialog-")) {
    example = (
      <>
        <Button onClick={() => setOpen(true)}>{es["catalog.openDialog"]}</Button>
        <Dialog
          open={open}
          title={es["catalog.dialogTitle"]}
          actions={<Button onClick={() => setOpen(false)}>{es["catalog.closeDialog"]}</Button>}
        >
          <p>{es["catalog.dialogBody"]}</p>
        </Dialog>
      </>
    );
  } else if (selected === "list") {
    example = (
      <NumberedList
        items={[
          { key: "draft", content: es["catalog.draft"] },
          { key: "review", content: es["catalog.review"] },
        ]}
      />
    );
  } else if (selected.startsWith("progress-")) {
    example = (
      <Progress
        label={es["catalog.progress"]}
        value={selected === "progress-known" ? 40 : undefined}
      />
    );
  } else if (selected.startsWith("banner-")) {
    const variant = selected.slice(7) as "info" | "success" | "warning" | "error";
    example = <StatusBanner variant={variant}>{es["catalog.bannerBody"]}</StatusBanner>;
  } else if (selected === "stepper") {
    example = (
      <Stepper
        current={1}
        steps={[
          { key: "draft", label: es["catalog.draft"] },
          { key: "review", label: es["catalog.review"] },
          { key: "deliver", label: es["catalog.deliver"] },
        ]}
      />
    );
  } else if (selected === "approval") {
    example = (
      <ApprovalCard
        what={es["catalog.draft"]}
        recipient={es["catalog.recipient"]}
        effect={es["catalog.effect"]}
        onApprove={report}
        onReject={report}
        onDecideLater={report}
      />
    );
  } else if (selected.startsWith("state-")) {
    example = (
      <StateScreen
        state={selected.slice(6) as StateScreenProps["state"]}
        actions={[{ label: es["catalog.retry"], onAction: report }]}
      />
    );
  } else if (!cases.includes(selected as (typeof cases)[number])) {
    example = (
      <StateScreen
        state="error"
        actions={[
          { label: es["catalog.back"], onAction: () => location.assign("?case=button-normal") },
        ]}
      />
    );
  }
  return (
    <>
      <header>
        <p>{es["catalog.product"]}</p>
        <h1>{es["catalog.title"]}</h1>
        <p>{es["catalog.description"]}</p>
      </header>
      <nav aria-label={es["catalog.navigation"]}>
        {cases.map((item) => (
          <Link
            key={item}
            href={`?case=${item}&theme=${params.get("theme") ?? "default"}`}
            aria-current={item === selected ? "page" : undefined}
          >
            {es[`catalog.case.${item}`]}
          </Link>
        ))}
      </nav>
      <main id="example">
        <h2>{es[`catalog.case.${selected}` as keyof typeof es] ?? es["state.error.label"]}</h2>
        {example}
        <p role="status">{feedback}</p>
      </main>
      <StopUndoBar
        onStop={report}
        onUndo={report}
        onHelp={report}
        undoAvailable={selected !== "stopbar-empty"}
      />
    </>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("Catalog root is missing");
createRoot(root).render(<Catalog />);
