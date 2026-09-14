"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Project, type Video } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";
import { DrivePicker } from "@/components/create/DrivePicker";
import { hasNativePicker, pickNativeVideo } from "@/lib/nativeBridge";
import { Card } from "@/components/common/Card";

type Step = "footage" | "review";

/** Add footage -> Review & start. Replaces CreateProjectModal + the standalone
 * /import page + a manual "Process All" click with one guided flow. A draft
 * project is created immediately so footage can be added right away; if the
 * user never adds anything it just sits as an empty "Draft" in Projects. */
export default function CreatePage() {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [step, setStep] = useState<Step>("footage");
  const [videos, setVideos] = useState<Video[]>([]);
  const [starting, setStarting] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name: `New reel — ${new Date().toLocaleDateString()}` }),
    })
      .then(setProject)
      .catch((e) => toast((e as Error).message, "err"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshVideos(id: string) {
    const full = await api<Project & { videos: Video[] }>(`/api/projects/${id}`);
    setVideos(full.videos || []);
  }

  useEffect(() => {
    if (project) refreshVideos(project.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project?.id]);

  async function pickNative(source: "photos" | "files") {
    if (!project) return;
    setUploading(true);
    try {
      const result = await pickNativeVideo(project.id, source);
      if (result && "error" in result) {
        toast(result.error, "err");
      } else if (result) {
        toast(`Added ${result.filename}`);
        await refreshVideos(project.id);
      }
    } finally {
      setUploading(false);
    }
  }

  async function startProcessing() {
    if (!project) return;
    setStarting(true);
    try {
      await api(`/api/projects/${project.id}/process`, { method: "POST" });
      toast("Let's go — Eren is on it");
      router.push(`/projects/${project.id}/queue`);
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setStarting(false);
    }
  }

  if (!project) return <p className="text-muted">Setting up your project…</p>;

  return (
    <div className="max-w-2xl pb-16">
      <h1 className="text-2xl font-semibold">Create a video</h1>
      <p className="mt-1 text-sm text-muted">{step === "footage" ? "Add your videos" : "Review and start"}</p>

      {step === "footage" && (
        <div className="mt-6">
          {videos.length > 0 && (
            <Card className="mb-6 p-4">
              <div className="mb-2 text-sm text-muted">{videos.length} clip{videos.length === 1 ? "" : "s"} added</div>
              <div className="space-y-2">
                {videos.map((v) => (
                  <div key={v.id} className="rounded-xl bg-ink px-3 py-2 text-sm">
                    {v.filename}
                  </div>
                ))}
              </div>
              <Button className="mt-4 w-full" onClick={() => setStep("review")}>
                Next: Review & start
              </Button>
            </Card>
          )}

          {hasNativePicker() && (
            <div className="mb-6 flex gap-2">
              <Button variant="secondary" disabled={uploading} onClick={() => pickNative("photos")}>
                {uploading ? "Adding…" : "Choose from Photos"}
              </Button>
              <Button variant="secondary" disabled={uploading} onClick={() => pickNative("files")}>
                Choose from Files
              </Button>
            </div>
          )}

          <DrivePicker projectId={project.id} onImported={() => refreshVideos(project.id)} />
        </div>
      )}

      {step === "review" && (
        <div className="mt-6 space-y-4">
          <Card className="p-5">
            <div className="font-medium">{project.name}</div>
            <div className="mt-2 text-sm text-muted">
              {videos.length} clip{videos.length === 1 ? "" : "s"} · Vertical reel · 9:16
            </div>
            <p className="mt-3 text-xs text-muted">
              Want a different look?{" "}
              <a className="underline" href="/style">
                Customize your style defaults
              </a>{" "}
              before starting — every new edit uses whatever is saved there.
            </p>
          </Card>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep("footage")}>
              Back
            </Button>
            <Button disabled={starting} onClick={startProcessing}>
              {starting ? "Starting…" : "Let Eren edit"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
