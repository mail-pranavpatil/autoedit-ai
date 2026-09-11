"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useState } from "react";
import { api, isProcessingStatus, type Project, type Video } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { Button } from "@/components/common/Button";
import { StatusBadge } from "@/components/common/StatusBadge";
import { toast } from "@/components/common/Toast";
import { SmoothPercent } from "@/lib/useSmoothProgress";

export default function QueuePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [data, setData] = useState<Project | null>(null);
  const [drawer, setDrawer] = useState<Video | null>(null);

  const load = useCallback(async () => {
    const p = await api<Project>(`/api/projects/${projectId}/progress`);
    setData(p);
    return p;
  }, [projectId]);

  const active =
    !data ||
    Boolean(data.active) ||
    (data.videos || []).some((v) => isProcessingStatus(v.status));
  usePolling(active, load, 1500);

  if (!data) return <p className="text-muted">Loading queue…</p>;
  const videos = data.videos || [];
  const pct = data.totalVideos ? Math.round((data.readyVideos / data.totalVideos) * 100) : 0;

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-muted">
            <Link href={`/projects/${projectId}`}>{data.name}</Link> / Queue
          </div>
          <h1 className="text-2xl font-semibold">Processing queue</h1>
        </div>
        <Button
          variant="secondary"
          onClick={async () => {
            const r = await api<{ queued: number }>(`/api/projects/${projectId}/retry-failed`, { method: "POST" });
            toast(`Retried ${r.queued}`);
            load();
          }}
        >
          Retry failed
        </Button>
      </div>
      <div className="mt-6 rounded-2xl border border-line bg-panel p-5">
        <div className="flex justify-between text-sm">
          <span>
            {data.readyVideos} ready · {data.failedVideos} failed · {data.processingVideos} processing
          </span>
          <span>{pct}%</span>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
          <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="mt-6 overflow-x-auto rounded-2xl border border-line">
        <table className="w-full text-left text-sm">
          <thead className="bg-panel text-muted">
            <tr>
              <th className="p-3">File</th>
              <th className="p-3">Status</th>
              <th className="p-3">Stage</th>
              <th className="p-3">Progress</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody>
            {videos.map((v) => (
              <tr key={v.id} className="border-t border-line">
                <td className="p-3">{v.filename}</td>
                <td className="p-3">
                  <StatusBadge status={v.status} />
                </td>
                <td className="p-3 text-muted">{v.currentStage || "—"}</td>
                <td className="p-3">
                  <SmoothPercent progress={v.progress || 0} status={v.status} />
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-3">
                    <button className="text-accent" onClick={() => setDrawer(v)}>
                      Details
                    </button>
                    {isProcessingStatus(v.status) && (
                      <button
                        className="text-red-300"
                        onClick={async () => {
                          try {
                            await api(`/api/videos/${v.id}/cancel`, { method: "POST" });
                            toast("Stopped");
                            load();
                          } catch (e) {
                            toast((e as Error).message, "err");
                          }
                        }}
                      >
                        Stop
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {drawer && (
        <div className="fixed inset-0 z-40 flex justify-end bg-black/50" onClick={() => setDrawer(null)}>
          <div className="h-full w-full max-w-md bg-panel p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-semibold">{drawer.filename}</h2>
            <p className="mt-2 text-sm text-muted">{drawer.currentStage}</p>
            {drawer.errorMessage && <p className="mt-4 text-sm text-red-300">{drawer.errorMessage}</p>}
            <div className="mt-6 flex gap-2">
              {drawer.status === "FAILED" && (
                <Button
                  onClick={async () => {
                    await api(`/api/videos/${drawer.id}/retry`, { method: "POST" });
                    toast("Retry queued");
                    setDrawer(null);
                    load();
                  }}
                >
                  Retry
                </Button>
              )}
              <Link href={`/projects/${projectId}/videos/${drawer.id}`}>
                <Button variant="secondary">Open video</Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
