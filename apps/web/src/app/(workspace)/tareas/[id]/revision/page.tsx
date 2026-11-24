import { ReviewScreen } from "../../../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.review.title");

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ReviewScreen id={id} />;
}
