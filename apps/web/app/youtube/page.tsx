"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { api, formatIst, type YoutubeUpload } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/EmptyState";
import { StatusBadge } from "@/components/common/StatusBadge";

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
          <div className="mt-4 overflow-x-auto rounded-2xl border border-line">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel text-muted">
                <tr>
                  <th className="p-3">Title</th>
                  <th className="p-3">Publish time (IST)</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Project</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="border-t border-line">
                    <td className="p-3 font-medium">{row.title || row.filename || "Untitled"}</td>
                    <td className="p-3">{row.scheduledAt ? formatIst(row.scheduledAt) : "—"}</td>
                    <td className="p-3">
                      <StatusBadge status={row.status} />
                      {row.status === "FAILED" && row.error ? (
                        <div className="mt-1 max-w-xs text-xs text-red-200/80">{row.error}</div>
                      ) : null}
                    </td>
                    <td className="p-3 text-muted">
                      {row.projectId ? (
                        <Link href={`/projects/${row.projectId}`} className="underline">
                          {row.projectName || "Project"}
                        </Link>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      {row.projectId && row.videoId ? (
                        <Link href={`/projects/${row.projectId}/videos/${row.videoId}`} className="text-accent">
                          Video
                        </Link>
                      ) : null}
                      {row.url ? (
                        <>
                          {row.projectId && row.videoId ? <span className="text-muted"> · </span> : null}
                          <a href={row.url} target="_blank" rel="noreferrer" className="text-accent">
                            YouTube
                          </a>
                        </>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
