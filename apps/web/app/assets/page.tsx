"use client";

import { useEffect, useState } from "react";
import { API_URL, api } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { EmptyState } from "@/components/common/EmptyState";
import { toast } from "@/components/common/Toast";

type Asset = {
  id: string;
  name: string;
  assetType: string;
  category?: string;
  enabled: boolean;
  isSystem: boolean;
  previewUrl: string;
};

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [tab, setTab] = useState<"music" | "sfx">("music");
  const [open, setOpen] = useState(false);

  async function load() {
    setAssets(await api<Asset[]>("/api/assets"));
  }
  useEffect(() => {
    load().catch((e) => toast(e.message, "err"));
  }, []);

  const list = assets.filter((a) => a.assetType === tab);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Asset library</h1>
        <Button onClick={() => setOpen(true)}>Upload</Button>
      </div>
      <div className="mt-4 flex gap-2">
        {(["music", "sfx"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`rounded-full px-4 py-1 ${tab === t ? "bg-white/10" : "text-muted"}`}>
            {t.toUpperCase()}
          </button>
        ))}
      </div>
      {list.length === 0 ? (
        <div className="mt-8">
          <EmptyState title={`No ${tab} yet`} body="Upload a track or keep the built-in system tones." />
        </div>
      ) : (
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {list.map((a) => (
            <div key={a.id} className="rounded-2xl border border-line bg-panel p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{a.name}</div>
                  <div className="text-xs text-muted">{a.category || a.assetType} {a.isSystem ? "· system" : ""}</div>
                </div>
                <label className="text-xs">
                  <input
                    type="checkbox"
                    checked={a.enabled}
                    onChange={async () => {
                      await api(`/api/assets/${a.id}/toggle`, { method: "POST" });
                      load();
                    }}
                  />{" "}
                  enabled
                </label>
              </div>
              <audio className="mt-3 w-full" controls src={`${API_URL}${a.previewUrl}`} />
              {!a.isSystem && (
                <button
                  className="mt-2 text-xs text-red-300"
                  onClick={async () => {
                    await api(`/api/assets/${a.id}`, { method: "DELETE" });
                    load();
                  }}
                >
                  Delete
                </button>
              )}
            </div>
          ))}
        </div>
      )}
      {open && <UploadModal tab={tab} onClose={() => setOpen(false)} onDone={load} />}
    </div>
  );
}

function UploadModal({ tab, onClose, onDone }: { tab: string; onClose: () => void; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!file) return;
    setBusy(true);
    const body = new FormData();
    body.append("file", file);
    body.append("assetType", tab);
    body.append("name", name || file.name);
    try {
      await api("/api/assets/upload", { method: "POST", body });
      toast("Uploaded");
      onDone();
      onClose();
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-2xl border border-line bg-panel p-6">
        <h2 className="text-lg font-semibold">Upload {tab}</h2>
        <input className="mt-4 w-full rounded-xl border border-line bg-ink px-3 py-2" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="mt-3 w-full text-sm" type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!file || busy} onClick={submit}>
            Upload
          </Button>
        </div>
      </div>
    </div>
  );
}
