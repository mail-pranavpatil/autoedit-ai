"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/EmptyState";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { toast } from "@/components/common/Toast";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [del, setDel] = useState<Project | null>(null);

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
  if (!projects) return <LoadingSkeleton />;

  const filtered = projects.filter((p) => p.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <Button onClick={() => setOpen(true)}>New Project</Button>
      </div>
      <input
        className="mt-4 w-full max-w-md rounded-xl border border-line bg-panel px-3 py-2 text-sm"
        placeholder="Search projects"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {filtered.length === 0 ? (
        <div className="mt-8">
          <EmptyState title="No projects" body="Create a project to import a Drive folder." action={<Button onClick={() => setOpen(true)}>New Project</Button>} />
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {filtered.map((p) => (
            <div key={p.id} className="flex items-center justify-between rounded-2xl border border-line bg-panel p-5">
              <Link href={`/projects/${p.id}`} className="flex-1">
                <div className="font-medium">{p.name}</div>
                <div className="text-sm text-muted">
                  {p.totalVideos} videos · {p.readyVideos} ready
                </div>
              </Link>
              <Button variant="ghost" onClick={() => setDel(p)}>
                Delete
              </Button>
            </div>
          ))}
        </div>
      )}
      <CreateProjectModal open={open} onClose={() => setOpen(false)} onCreated={load} />
      <ConfirmDialog
        open={!!del}
        title="Delete project?"
        body="This removes the project record. Rendered files on disk are not published anywhere else."
        danger
        confirmLabel="Delete"
        onClose={() => setDel(null)}
        onConfirm={async () => {
          if (!del) return;
          try {
            await api(`/api/projects/${del.id}`, { method: "DELETE" });
            toast("Deleted");
            setDel(null);
            load();
          } catch (e) {
            toast((e as Error).message, "err");
          }
        }}
      />
    </div>
  );
}
