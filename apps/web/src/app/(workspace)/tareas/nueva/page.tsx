import { NewTaskScreen } from "../../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.task.new.title");

export default function Page() {
  return <NewTaskScreen />;
}
