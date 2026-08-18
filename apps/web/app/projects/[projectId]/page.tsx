"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useState } from "react";
import { api, formatDuration, isProcessingStatus, mediaUrl, type Project, type Video } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { Button } from "@/components/common/Button";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/EmptyState";
import { toast } from "@/components/common/Toast";

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("all");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const p = await api<Project>(`/api/projects/${params.projectId}`);
    setProject(p);
    setError(null);
  }, [params.projectId]);

  const polling =
    !project || (project.videos || []).some((v) => isProcessingStatus(v.status)) || project.processingVideos > 0;
  usePolling(polling, load, 2000);

  if (!project && error) return <ErrorState message={error} onRetry={() => load().catch((e) => setError((e as Error).message))} />;
  if (!project) return <LoadingSkeleton />;

  const videos = (project.videos || []).filter((v) => filter === "all" || v.status === filter);
  const canProcess = (project.videos || []).length > 0;

  async function processAll() {
    setBusy(true);
    try {
      const r = await api<{ queued: number }>(`/api/projects/${params.projectId}/process`, { method: "POST" });
      toast(`Queued ${r.queued} videos`);
      window.location.href = `/projects/${params.projectId}/queue`;
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs text-muted">
            <Link href="/projects">Projects</Link> / {project.name}
          </div>
          <h1 className="text-2xl font-semibold">{project.name}</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href={`/projects/${project.id}/import`}>
            <Button variant="secondary">Import from Drive</Button>
          </Link>
          <Link href={`/projects/${project.id}/queue`}>
            <Button variant="ghost">Queue</Button>
          </Link>
          <Link href={`/projects/${project.id}/results`}>
            <Button variant="ghost">Results</Button>
          </Link>
          <Button disabled={!canProcess || busy} onClick={processAll}>
            Process All
          </Button>
        </div>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-4">
        {[
          ["Total", project.totalVideos],
          ["Ready", project.readyVideos],
          ["Processing", project.processingVideos],
          ["Failed", project.failedVideos],
        ].map(([l, v]) => (
          <div key={String(l)} className="rounded-xl border border-line bg-panel p-4">
            <div className="text-xs text-muted">{l}</div>
            <div className="text-xl font-semibold">{v}</div>
          </div>
        ))}
      </div>
      {project.processingVideos > 0 && (
        <Link href={`/projects/${project.id}/queue`} className="mt-4 block rounded-xl border border-accent/30 bg-accent/10 p-4 text-sm">
          Processing in progress — open the queue
        </Link>
      )}
      <div className="mt-6 flex gap-2 text-sm">
        {["all", "READY", "FAILED", "QUEUED"].map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={`rounded-full px-3 py-1 ${filter === f ? "bg-white/10" : "text-muted"}`}>
            {f}
          </button>
        ))}
      </div>
      {(project.videos || []).length === 0 ? (
        <div className="mt-6">
          <EmptyState
            title="No videos yet"
            body="Import a Google Drive folder of talking-head clips."
            action={
              <Link href={`/projects/${project.id}/import`}>
                <Button>Import from Drive</Button>
              </Link>
            }
          />
        </div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {videos.map((v) => (
            <VideoCard key={v.id} video={v} projectId={project.id} />
          ))}
        </div>
      )}
    </div>
  );
}

function VideoCard({ video, projectId }: { video: Video; projectId: string }) {
  return (
    <Link href={`/projects/${projectId}/videos/${video.id}`} className="overflow-hidden rounded-2xl border border-line bg-panel">
      <div className="aspect-[9/16] max-h-64 bg-black">
        {video.thumbnailUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={mediaUrl(video.thumbnailUrl)} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-muted">No thumbnail yet</div>
        )}
      </div>
      <div className="p-3">
        <div className="truncate text-sm font-medium">{video.filename}</div>
        <div className="mt-2 flex items-center justify-between text-xs text-muted">
          <StatusBadge status={video.status} />
          <span>{formatDuration(video.duration)}</span>
        </div>
      </div>
    </Link>
  );
}
