import { TaskScreen } from "../../../../features/workspace/Screens.tsx";
import { workspaceMetadata } from "../../../../features/workspace/metadata.ts";

export const metadata = workspaceMetadata("workspace.task.progress.title");

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ editar?: string }>;
}) {
  const { id } = await params;
  const editing = (await searchParams).editar === "1";
  return <TaskScreen key={`${id}:${editing}`} id={id} initialEditing={editing} />;
}
