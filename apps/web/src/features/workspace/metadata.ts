import type { Metadata } from "next";
import { es } from "../../../../../packages/ui/src/i18n/es.ts";

/** Static labels describe the page without putting private draft text in browser history. */
export function workspaceMetadata(title: keyof typeof es): Metadata {
  return {
    title: `${es[title]} · ${es["catalog.product"]}`,
    description: es["workspace.local.note"],
  };
}
