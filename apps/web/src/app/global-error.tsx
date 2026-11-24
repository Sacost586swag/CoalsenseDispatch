"use client";

import { EmergencyScreen } from "../features/workspace/Emergency.tsx";
import "@coalsense/ui/fonts.css";
import "@coalsense/ui/components.css";
import "./globals.css";
import "../features/workspace/workspace.css";

export default function GlobalError({ retry }: { error: unknown; retry: () => void }) {
  return (
    <html lang="es-EC">
      <body>
        <EmergencyScreen retry={retry} />
      </body>
    </html>
  );
}
