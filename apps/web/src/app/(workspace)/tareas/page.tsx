import { TaskListScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.task.list.title");

export default function Page() {
  return <TaskListScreen />;
}
