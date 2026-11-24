import { SettingsScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.nav.autonomy");

export default function Page() {
  return <SettingsScreen variant="autonomy" />;
}
