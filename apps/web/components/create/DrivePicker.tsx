"use client";

import { useEffect, useState } from "react";
import { api, API_URL } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";
import { useAuth } from "@/components/providers";
import { Folder as FolderIcon } from "lucide-react";

type Folder = { id: string; name: string };
type RemoteVideo = { id: string; name: string; size: number };

/** Google Drive folder browser + import, shared by the unified Create flow
 * and the standalone /projects/[id]/import route. */
export function DrivePicker({ projectId, onImported }: { projectId: string; onImported: (count: number) => void }) {
  const { user } = useAuth();
  const [parent, setParent] = useState<string | null>(null);
  const [stack, setStack] = useState<{ id: string | null; name: string }[]>([{ id: null, name: "My Drive" }]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [videos, setVideos] = useState<RemoteVideo[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [folder, setFolder] = useState<Folder | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadFolders(id: string | null) {
    setLoading(true);
    setError(null);
    try {
      const q = id ? `?parentId=${encodeURIComponent(id)}` : "";
      setFolders(await api<Folder[]>(`/api/drive/folders${q}`));
    } catch (e) {
      const message = (e as Error).message || "Could not load Drive folders";
      setError(message);
      toast(message, "err");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFolders(parent);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [parent]);

  async function openFolder(f: Folder) {
    setFolder(f);
    setParent(f.id);
    setStack((s) => [...s, { id: f.id, name: f.name }]);
    setLoading(true);
    try {
      const list = await api<RemoteVideo[]>(`/api/drive/folders/${f.id}/videos`);
      setVideos(list);
      setSelected(Object.fromEntries(list.map((v) => [v.id, true])));
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setLoading(false);
    }
  }

  function crumb(i: number) {
    const item = stack[i];
    setStack(stack.slice(0, i + 1));
    setParent(item.id);
    setFolder(item.id ? { id: item.id, name: item.name } : null);
    setVideos([]);
  }

  const chosen = videos.filter((v) => selected[v.id]);

  async function importSelected() {
    if (!folder) return;
    setBusy(true);
    try {
      const r = await api<{ imported: number }>("/api/drive/import", {
        method: "POST",
        body: JSON.stringify({
          projectId,
          folderId: folder.id,
          folderName: folder.name,
          fileIds: chosen.map((v) => v.id),
        }),
      });
      toast(`Imported ${r.imported} videos`);
      onImported(r.imported);
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="rounded-xl border border-line bg-panel p-4 text-sm">
        {user?.driveConnected ? (
          <span>Google Drive connected as {user.email}</span>
        ) : (
          <span>
            Drive is not connected.{" "}
            <a className="underline" href={`${API_URL}/api/auth/google`}>
              Sign in again
            </a>
          </span>
        )}
      </div>
      <div className="mt-4 flex flex-wrap gap-2 text-sm text-muted">
        {stack.map((s, i) => (
          <button key={s.name + i} onClick={() => crumb(i)} className="hover:text-white">
            {s.name} /
          </button>
        ))}
      </div>
      {error && (
        <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-500/10 p-5 text-sm">
          <p className="font-medium text-red-200">Could not load Drive</p>
          <p className="mt-2 text-red-200/80">{error}</p>
          <a
            className="mt-3 inline-block underline"
            href="https://console.cloud.google.com/apis/library/drive.googleapis.com"
            target="_blank"
            rel="noreferrer"
          >
            Enable Google Drive API
          </a>
          <button className="ml-4 underline" onClick={() => loadFolders(parent)}>
            Retry
          </button>
        </div>
      )}
      {loading ? (
        <p className="mt-6 text-muted">Loading Drive…</p>
      ) : !error && folders.length === 0 ? (
        <p className="mt-6 text-muted">No folders in this location. Open a folder that contains videos, or go up a level.</p>
      ) : (
        <div className="mt-4 grid gap-2">
          {folders.map((f) => (
            <button key={f.id} onClick={() => openFolder(f)} className="flex items-center gap-2 rounded-xl border border-line bg-panel px-4 py-3 text-left transition-colors duration-150 hover:border-accent/40">
              <FolderIcon className="h-4 w-4 text-muted" /> {f.name}
            </button>
          ))}
        </div>
      )}
      {videos.length > 0 && (
        <div className="mt-8">
          <h2 className="font-medium">{videos.length} videos in this folder</h2>
          <div className="mt-3 space-y-2">
            {videos.map((v) => (
              <label key={v.id} className="flex items-center gap-3 rounded-xl border border-line bg-panel px-4 py-3">
                <input type="checkbox" checked={!!selected[v.id]} onChange={(e) => setSelected((s) => ({ ...s, [v.id]: e.target.checked }))} />
                <span className="flex-1 truncate">{v.name}</span>
              </label>
            ))}
          </div>
        </div>
      )}
      <div className="sticky bottom-4 mt-8 flex items-center justify-between rounded-2xl border border-line bg-panel p-4">
        <span className="text-sm text-muted">{chosen.length} selected</span>
        <Button disabled={!chosen.length || busy} onClick={importSelected}>
          Import selected
        </Button>
      </div>
    </div>
  );
}
