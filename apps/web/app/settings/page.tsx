"use client";

import { useEffect, useState } from "react";
import { API_URL, api } from "@/lib/api";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";

export default function SettingsPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [danger, setDanger] = useState(false);

  useEffect(() => {
    api("/api/settings").then(setData as never).catch((e) => toast(e.message, "err"));
  }, []);

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <section className="mt-6 rounded-2xl border border-line bg-panel p-5">
        <h2 className="font-medium">Integrations</h2>
        <p className="mt-2 text-sm text-muted">Google sign-in is also Drive access. Tokens stay on the server.</p>
        <p className="mt-3 text-sm">Drive connected: {data?.googleConnected ? "yes" : "no"}</p>
        <a className="mt-3 inline-block text-sm underline" href={`${API_URL}/api/auth/google`}>
          Reconnect Google
        </a>
      </section>
      <section className="mt-4 rounded-2xl border border-line bg-panel p-5 text-sm">
        <h2 className="font-medium">Rendering</h2>
        <p className="mt-2 text-muted">Worker concurrency: {String(data?.workerConcurrency ?? "—")}</p>
        <p className="text-muted">Transcription: {String(data?.transcriptionProvider)}</p>
        <p className="text-muted">LLM: {String(data?.llmProvider)}</p>
        <p className="text-muted">OpenAI key configured: {data?.hasOpenAIKey ? "yes" : "no"}</p>
        <p className="text-muted">Pexels key configured: {data?.hasPexelsKey ? "yes" : "no"}</p>
      </section>
      <section className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/5 p-5">
        <h2 className="font-medium">Danger zone</h2>
        <p className="mt-2 text-sm text-muted">Sign out of this browser session.</p>
        <Button className="mt-4" variant="danger" onClick={() => setDanger(true)}>
          Log out
        </Button>
      </section>
      <ConfirmDialog
        open={danger}
        title="Log out?"
        body="You will need Google again to access AutoEdit AI."
        danger
        confirmLabel="Log out"
        onClose={() => setDanger(false)}
        onConfirm={async () => {
          await api("/api/auth/logout", { method: "POST" });
          window.location.href = "/login";
        }}
      />
    </div>
  );
}
