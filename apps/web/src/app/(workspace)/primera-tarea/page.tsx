import { PracticeScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.practice.title");

export default function Page() {
  return <PracticeScreen />;
}
