import { SettingsScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.nav.settings");

export default function Page() {
  return <SettingsScreen />;
}
