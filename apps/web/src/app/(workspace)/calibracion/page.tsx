import { CalibrationScreen } from "../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.calibration.title");

export default function Page() {
  return <CalibrationScreen />;
}
