"use client";

import { useParams } from "next/navigation";
import { EditorWorkspace } from "@/components/editor/EditorWorkspace";

export default function EditorPage() {
  const { projectId, videoId } = useParams<{ projectId: string; videoId: string }>();
  return <EditorWorkspace projectId={projectId} videoId={videoId} />;
}
