"use client";

import { EmergencyScreen } from "../features/workspace/Emergency.tsx";
import "../features/workspace/workspace.css";

export default function ErrorScreen({ retry }: { error: unknown; retry: () => void }) {
  return <EmergencyScreen retry={retry} />;
}
