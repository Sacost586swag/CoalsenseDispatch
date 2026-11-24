import { HomeScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.nav.home");

export default function Page() {
  return <HomeScreen />;
}
