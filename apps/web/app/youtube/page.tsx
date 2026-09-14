"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { api, formatIst, mediaUrl, type YoutubeUpload } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/EmptyState";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Card } from "@/components/common/Card";

export default function YoutubePage() {
  const [rows, setRows] = useState<YoutubeUpload[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const next = await api<YoutubeUpload[]>("/api/youtube/uploads");
      setRows(next);
      setError(null);
      return next;
    } catch (e) {
      setError((e as Error).message);
      return [];
    }
  }, []);

  const pending = (rows || []).some((row) => row.status === "PENDING" || row.status === "UPLOADING");
  usePolling(!rows || pending, load, 2500);

  if (error && !rows) return <ErrorState message={error} onRetry={load} />;
  if (!rows) return <LoadingSkeleton />;

  const scheduled = rows.filter((row) => row.status === "SCHEDULED").length;

  return (
    <div>
      <h1 className="text-2xl font-semibold">YouTube</h1>
      <p className="mt-2 text-sm text-muted">
        Scheduled publishes in IST (7:00, 14:00, 18:00, 21:00). Titles match the source file name.
      </p>
      {rows.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title="No YouTube uploads yet"
            body="When an AI edit finishes, it is uploaded and given the next free slot. Reconnect Google with YouTube access in Settings if this stays empty."
          />
        </div>
      ) : (
        <>
          <p className="mt-4 text-sm text-muted">
            {scheduled} scheduled · {rows.length} total
          </p>
          <div className="mt-4 space-y-3">
            {rows.map((row) => (
              <PublishCard key={row.id} row={row} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function PublishCard({ row }: { row: YoutubeUpload }) {
  return (
    <Card className="flex gap-3 p-4">
      <div className="h-20 w-12 shrink-0 overflow-hidden rounded-lg bg-black">
        {row.thumbnailUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={mediaUrl(row.thumbnailUrl)} alt="" className="h-full w-full object-cover" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 truncate font-medium">{row.title || row.filename || "Untitled"}</div>
          <StatusBadge status={row.status} />
        </div>
        <div className="mt-1 text-sm text-muted">
          {row.scheduledAt ? `${formatIst(row.scheduledAt)} IST` : "Not scheduled yet"}
          {row.projectId && (
            <>
              {" · "}
              <Link href={`/projects/${row.projectId}`} className="underline">
                {row.projectName || "Project"}
              </Link>
            </>
          )}
        </div>
        {row.status === "FAILED" && (
          <div className="mt-1">
            <p className="text-sm text-red-200/80">Upload didn&apos;t go through.</p>
            {row.error && (
              <details className="mt-1 text-xs text-muted">
                <summary className="cursor-pointer">View technical details</summary>
                <p className="mt-1 whitespace-pre-wrap">{row.error}</p>
              </details>
            )}
          </div>
        )}
        <div className="mt-2 flex gap-3 text-sm">
          {row.projectId && row.videoId && (
            <Link href={`/projects/${row.projectId}/videos/${row.videoId}`} className="text-accent">
              Open video
            </Link>
          )}
          {row.url && (
            <a href={row.url} target="_blank" rel="noreferrer" className="text-accent">
              View on YouTube
            </a>
          )}
        </div>
      </div>
    </Card>
  );
}
