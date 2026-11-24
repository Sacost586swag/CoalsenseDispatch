import { WelcomeScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.welcome.title");

export default function Page() {
  return <WelcomeScreen />;
}
