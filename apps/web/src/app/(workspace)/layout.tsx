import type { ReactNode } from "react";
import { WorkspaceProvider } from "../../features/workspace/state.tsx";
import { WorkspaceShell } from "../../features/workspace/Shell.tsx";
import "../../features/workspace/workspace.css";

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <WorkspaceProvider>
      <WorkspaceShell>{children}</WorkspaceShell>
    </WorkspaceProvider>
  );
}
