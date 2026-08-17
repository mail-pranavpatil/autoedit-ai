"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";

export function CreateProjectModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  if (!open) return null;

  async function submit() {
    setBusy(true);
    try {
      const p = await api<{ id: string }>("/api/projects", { method: "POST", body: JSON.stringify({ name }) });
      toast("Project created");
      onCreated();
      onClose();
      router.push(`/projects/${p.id}`);
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-2xl border border-line bg-panel p-6">
        <h2 className="text-lg font-semibold">Create project</h2>
        <input
          className="mt-4 w-full rounded-xl border border-line bg-ink px-3 py-2"
          placeholder="August Reels"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!name.trim() || busy} onClick={submit}>
            Create
          </Button>
        </div>
      </div>
    </div>
  );
}
