"use client";

import { useParams, useRouter } from "next/navigation";
import { DrivePicker } from "@/components/create/DrivePicker";

export default function ImportPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const router = useRouter();

  return (
    <div>
      <h1 className="text-2xl font-semibold">Import from Google Drive</h1>
      <p className="mt-1 text-sm text-muted">Pick a folder. AutoEdit AI will only look at videos inside it.</p>
      <DrivePicker projectId={projectId} onImported={() => router.push(`/projects/${projectId}`)} />
    </div>
  );
}
