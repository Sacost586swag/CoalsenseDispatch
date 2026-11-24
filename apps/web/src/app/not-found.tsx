import { MissingScreen } from "../features/workspace/Recovery.tsx";
import { workspaceMetadata } from "../features/workspace/metadata.ts";
import "../features/workspace/workspace.css";

export const metadata = workspaceMetadata("workspace.recovery.missing.title");

export default function NotFound() {
  return <MissingScreen />;
}
