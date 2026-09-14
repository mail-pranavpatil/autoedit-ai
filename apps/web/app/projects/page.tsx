"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatRelativeTime, type Project } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/common/EmptyState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { StatusBadge } from "@/components/common/StatusBadge";
import { projectStatus } from "@/lib/projectStatus";
import { toast } from "@/components/common/Toast";
import { MoreVertical } from "lucide-react";
import { Card } from "@/components/common/Card";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [del, setDel] = useState<Project | null>(null);
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  const [renaming, setRenaming] = useState<{ id: string; name: string } | null>(null);

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

  async function saveRename() {
    if (!renaming) return;
    const name = renaming.name.trim();
    if (!name) return setRenaming(null);
    try {
      await api(`/api/projects/${renaming.id}`, { method: "PATCH", body: JSON.stringify({ name }) });
      setRenaming(null);
      load();
    } catch (e) {
      toast((e as Error).message, "err");
    }
  }

  async function duplicate(p: Project) {
    setMenuOpen(null);
    try {
      await api(`/api/projects/${p.id}/duplicate`, { method: "POST" });
      toast("Project duplicated");
      load();
    } catch (e) {
      toast((e as Error).message, "err");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <Button onClick={() => router.push("/create")}>New Project</Button>
      </div>
      <input
        className="mt-4 w-full max-w-md rounded-xl border border-line bg-panel px-3 py-2 text-sm"
        placeholder="Search projects"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {filtered.length === 0 ? (
        <div className="mt-8">
          <EmptyState title="No projects" body="Create a project to import a Drive folder." action={<Button onClick={() => router.push("/create")}>New Project</Button>} />
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {filtered.map((p) => (
            <Card key={p.id} className="relative flex items-center justify-between p-5">
              {renaming?.id === p.id ? (
                <input
                  autoFocus
                  className="flex-1 rounded-lg border border-accent/50 bg-ink px-2 py-1 text-sm"
                  value={renaming.name}
                  onChange={(e) => setRenaming({ id: p.id, name: e.target.value })}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") saveRename();
                    if (e.key === "Escape") setRenaming(null);
                  }}
                  onBlur={saveRename}
                />
              ) : (
                <Link href={`/projects/${p.id}`} className="flex-1">
                  <div className="flex items-center gap-2 font-medium">
                    {p.name}
                    <StatusBadge status={projectStatus(p)} />
                  </div>
                  <div className="text-sm text-muted">
                    {p.totalVideos} videos · {p.readyVideos} ready · edited {formatRelativeTime(p.updatedAt)}
                  </div>
                </Link>
              )}
              <button
                className="ml-3 flex h-11 w-11 items-center justify-center rounded-xl text-muted transition-colors duration-150 hover:bg-white/5 hover:text-white"
                aria-label="Project actions"
                onClick={() => setMenuOpen(menuOpen === p.id ? null : p.id)}
              >
                <MoreVertical className="h-5 w-5" />
              </button>
              {menuOpen === p.id && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(null)} />
                  <div className="absolute right-5 top-14 z-20 w-40 overflow-hidden rounded-xl border border-line bg-ink shadow-lg">
                    <button
                      className="block w-full px-3 py-2.5 text-left text-sm hover:bg-white/5"
                      onClick={() => {
                        setRenaming({ id: p.id, name: p.name });
                        setMenuOpen(null);
                      }}
                    >
                      Rename
                    </button>
                    <button className="block w-full px-3 py-2.5 text-left text-sm hover:bg-white/5" onClick={() => duplicate(p)}>
                      Duplicate
                    </button>
                    <button
                      className="block w-full px-3 py-2.5 text-left text-sm text-red-300 hover:bg-white/5"
                      onClick={() => {
                        setDel(p);
                        setMenuOpen(null);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </>
              )}
            </Card>
          ))}
        </div>
      )}
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
