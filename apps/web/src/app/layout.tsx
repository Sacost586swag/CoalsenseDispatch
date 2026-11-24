import type { Metadata } from "next";
import type { ReactNode } from "react";
import { stitchTheme } from "../../../../packages/ui/src/themes/stitch.ts";
import { toCssVariables } from "../../../../packages/ui/src/tokens/css.ts";
import { es } from "../../../../packages/ui/src/i18n/es.ts";
import "@coalsense/ui/fonts.css";
import "@coalsense/ui/components.css";
import "./globals.css";

export const metadata: Metadata = {
  title: es["catalog.product"],
  description: es["auth.app.intro"],
};
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es-EC">
      <head>
        <style data-cs-theme>{toCssVariables(stitchTheme)}</style>
      </head>
      <body>{children}</body>
    </html>
  );
}
