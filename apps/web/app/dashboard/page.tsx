"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/EmptyState";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { toast } from "@/components/common/Toast";

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [stopping, setStopping] = useState(false);

  async function load() {
    try {
      setProjects(await api<Project[]>("/api/projects"));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    load();
  }, []);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!projects) return <LoadingSkeleton className="h-48" />;

  const totals = projects.reduce(
    (a, p) => ({
      total: a.total + p.totalVideos,
      ready: a.ready + p.readyVideos,
      processing: a.processing + p.processingVideos,
      failed: a.failed + p.failedVideos,
    }),
    { total: 0, ready: 0, processing: 0, failed: 0 }
  );
  const active = projects.filter((p) => p.processingVideos > 0);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted">Import videos. Process. Download finished reels.</p>
        </div>
        <div className="flex gap-2">
          {totals.processing > 0 && (
            <Button
              variant="danger"
              disabled={stopping}
              onClick={async () => {
                setStopping(true);
                try {
                  const r = await api<{ cancelled: number }>("/api/videos/cancel-all", { method: "POST" });
                  toast(`Stopped ${r.cancelled} processing video${r.cancelled === 1 ? "" : "s"}`);
                  load();
                } catch (e) {
                  toast((e as Error).message, "err");
                } finally {
                  setStopping(false);
                }
              }}
            >
              {stopping ? "Stopping…" : "Stop all processing"}
            </Button>
          )}
          <Button onClick={() => setOpen(true)}>New Project</Button>
        </div>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-4">
        {[
          ["Videos", totals.total],
          ["Ready", totals.ready],
          ["Processing", totals.processing],
          ["Failed", totals.failed],
        ].map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-line bg-panel p-4">
            <div className="text-xs text-muted">{label}</div>
            <div className="mt-1 text-2xl font-semibold">{value}</div>
          </div>
        ))}
      </div>
      {active.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 font-medium">Active processing</h2>
          <div className="space-y-2">
            {active.map((p) => (
              <Link key={p.id} href={`/projects/${p.id}/queue`} className="block rounded-xl border border-line bg-panel p-4">
                {p.name} — {p.processingVideos} in progress
              </Link>
            ))}
          </div>
        </section>
      )}
      <section className="mt-8">
        <h2 className="mb-3 font-medium">Recent projects</h2>
        {projects.length === 0 ? (
          <EmptyState
            title="No projects yet"
            body="Create a project, connect Drive, and import a folder of talking-head clips."
            action={<Button onClick={() => setOpen(true)}>New Project</Button>}
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {projects.map((p) => (
              <Link key={p.id} href={`/projects/${p.id}`} className="rounded-2xl border border-line bg-panel p-5 hover:border-accent/40">
                <div className="font-medium">{p.name}</div>
                <div className="mt-2 text-sm text-muted">
                  {p.totalVideos} videos · {p.readyVideos} ready · {p.failedVideos} failed
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
      <CreateProjectModal open={open} onClose={() => setOpen(false)} onCreated={load} />
    </div>
  );
}
