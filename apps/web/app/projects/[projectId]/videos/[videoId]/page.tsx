"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { API_URL, api, formatDuration, type Video } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { StatusBadge } from "@/components/common/StatusBadge";
import { toast } from "@/components/common/Toast";
import { ProcessingConsole, isProcessingStatus } from "@/components/video/ProcessingConsole";

export default function VideoDetailPage() {
  const { projectId, videoId } = useParams<{ projectId: string; videoId: string }>();
  const [video, setVideo] = useState<Video | null>(null);
  const [starting, setStarting] = useState(false);

  async function load() {
    const next = await api<Video>(`/api/videos/${videoId}`);
    setVideo(next);
    return next;
  }

  const polling = !video || isProcessingStatus(video.status) || starting;

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let cancelled = false;

    async function tick() {
      try {
        const next = await load();
        if (cancelled) return;
        if (isProcessingStatus(next.status)) {
          timer = setTimeout(tick, 2000);
        }
      } catch (e) {
        if (!cancelled) toast((e as Error).message, "err");
      }
    }

    tick();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [videoId, polling]);

  if (!video) return <p className="text-muted">Loading video…</p>;
  const plan = video.editPlan as { video_summary?: string; tone?: string; music_category?: string; segments?: unknown[] } | null;
  const processing = isProcessingStatus(video.status);
  const showConsole = processing || video.status === "READY" || video.status === "FAILED";

  async function startProcess() {
    setStarting(true);
    try {
      const next = await api<Video>(`/api/videos/${video.id}/process`, { method: "POST" });
      setVideo(next);
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
      <div>
        <div className="text-xs text-muted">
          <Link href={`/projects/${projectId}`}>Project</Link> / {video.filename}
        </div>
        <div className="mt-2 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{video.filename}</h1>
          <StatusBadge status={video.status} />
        </div>
        {showConsole && (
          <div className="mt-4">
            <ProcessingConsole video={video} />
          </div>
        )}
        {video.status === "READY" ? (
          <video className="mt-4 w-full max-w-sm rounded-2xl bg-black" controls src={`${API_URL}/api/videos/${video.id}/stream`} />
        ) : !processing ? (
          <div className="mt-4 rounded-2xl border border-line bg-panel p-8 text-sm text-muted">
            Preview appears here after the reel is rendered.
          </div>
        ) : null}
      </div>
      <div className="space-y-4">
        <div className="rounded-2xl border border-line bg-panel p-5 text-sm">
          <div>Duration: {formatDuration(video.duration)}</div>
          <div>
            Size: {video.width}×{video.height}
          </div>
        </div>
        {video.status === "FAILED" && (
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-5">
            <p className="font-medium">Failed at {video.failedStage}</p>
            <p className="mt-2 text-sm text-red-200/80">{video.errorMessage}</p>
            <Button
              className="mt-4"
              onClick={async () => {
                const next = await api<Video>(`/api/videos/${video.id}/retry`, { method: "POST" });
                setVideo(next);
              }}
            >
              Retry
            </Button>
          </div>
        )}
        {plan && (
          <div className="rounded-2xl border border-line bg-panel p-5 text-sm">
            <h2 className="font-medium">AI edit summary</h2>
            <p className="mt-2 text-muted">{plan.video_summary}</p>
            <p className="mt-2 text-muted">
              Tone: {plan.tone} · Music: {plan.music_category} · {plan.segments?.length || 0} segments
            </p>
          </div>
        )}
        <div className="flex gap-2">
          {video.status !== "READY" && video.status !== "FAILED" && !processing && (
            <Button disabled={starting} onClick={startProcess}>
              {starting ? "Starting…" : "Process this video"}
            </Button>
          )}
          {processing && (
            <p className="text-sm text-muted">You can leave this page. Processing continues in the background.</p>
          )}
          {video.status === "READY" && (
            <a href={`${API_URL}/api/videos/${video.id}/download`}>
              <Button>Download MP4</Button>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
