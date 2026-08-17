"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { API_URL, api, mediaUrl, type Project, type Video } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { StatusBadge } from "@/components/common/StatusBadge";
import { toast } from "@/components/common/Toast";

export default function ResultsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    api<Project>(`/api/projects/${projectId}`).then(setProject).catch((e) => toast(e.message, "err"));
  }, [projectId]);

  if (!project) return <p className="text-muted">Loading results…</p>;
  const videos = project.videos || [];
  const ready = videos.filter((v) => v.status === "READY");
  const failed = videos.filter((v) => v.status === "FAILED");

  return (
    <div>
      <div className="text-xs text-muted">
        <Link href={`/projects/${projectId}`}>{project.name}</Link> / Results
      </div>
      <h1 className="text-2xl font-semibold">Batch results</h1>
      <p className="mt-2 text-sm text-muted">
        {ready.length} completed · {failed.length} failed · {videos.length} total
      </p>
      {ready.length > 0 && (
        <Button
          className="mt-4"
          onClick={() => {
            ready.forEach((v) => {
              const a = document.createElement("a");
              a.href = `${API_URL}/api/videos/${v.id}/download`;
              a.click();
            });
          }}
        >
          Download all ready videos
        </Button>
      )}
      <h2 className="mt-8 font-medium">Completed</h2>
      <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ready.map((v) => (
          <ResultCard key={v.id} video={v} projectId={projectId} />
        ))}
      </div>
      {failed.length > 0 && (
        <>
          <div className="mt-10 flex items-center justify-between">
            <h2 className="font-medium">Failed</h2>
            <Button
              variant="secondary"
              onClick={async () => {
                const r = await api<{ queued: number }>(`/api/projects/${projectId}/retry-failed`, { method: "POST" });
                toast(`Queued ${r.queued}`);
              }}
            >
              Retry failed
            </Button>
          </div>
          <div className="mt-3 space-y-2">
            {failed.map((v) => (
              <Link key={v.id} href={`/projects/${projectId}/videos/${v.id}`} className="block rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                <div className="flex items-center justify-between">
                  <span>{v.filename}</span>
                  <StatusBadge status="FAILED" />
                </div>
                <p className="mt-1 text-sm text-red-200/80">{v.errorMessage}</p>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function ResultCard({ video, projectId }: { video: Video; projectId: string }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-panel">
      <Link href={`/projects/${projectId}/videos/${video.id}`}>
        {video.thumbnailUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={mediaUrl(video.thumbnailUrl)} alt="" className="aspect-[9/16] max-h-56 w-full object-cover" />
        ) : (
          <div className="aspect-video bg-black" />
        )}
        <div className="p-3 text-sm">{video.filename}</div>
      </Link>
      {video.outputUrl && (
        <a className="block border-t border-line p-3 text-sm text-accent" href={`${API_URL}${video.outputUrl}`}>
          Download
        </a>
      )}
    </div>
  );
}
