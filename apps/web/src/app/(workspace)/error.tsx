"use client";

import { RecoveryScreen } from "../../features/workspace/Recovery.tsx";

export default function ErrorScreen({ retry }: { error: unknown; retry: () => void }) {
  return <RecoveryScreen state="error" retry={retry} />;
}
