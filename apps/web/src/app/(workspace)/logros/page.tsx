import { AchievementsScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.achievements.title");

export default function Page() {
  return <AchievementsScreen />;
}
