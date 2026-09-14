"use client";

import { useEffect, useState } from "react";
import { API_URL, api } from "@/lib/api";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";
import { Card } from "@/components/common/Card";

export default function SettingsPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [danger, setDanger] = useState(false);

  useEffect(() => {
    api("/api/settings").then(setData as never).catch((e) => toast(e.message, "err"));
  }, []);

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Card className="mt-6 p-5">
        <h2 className="font-medium">Integrations</h2>
        <p className="mt-2 text-sm text-muted">Google sign-in is also Drive and YouTube upload access. Tokens stay on the server.</p>
        <p className="mt-3 text-sm">Drive connected: {data?.googleConnected ? "yes" : "no"}</p>
        <p className="text-sm">YouTube connected: {data?.youtubeConnected ? "yes" : "no"}</p>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={Boolean(data?.youtubeAutoUpload)}
            onChange={async (e) => {
              const youtubeAutoUpload = e.target.checked;
              try {
                const next = await api<{ youtubeAutoUpload: boolean; youtubeConnected: boolean }>("/api/settings/youtube", {
                  method: "PUT",
                  body: JSON.stringify({ youtubeAutoUpload }),
                });
                setData((prev) => ({ ...(prev || {}), ...next }));
              } catch (err) {
                toast((err as Error).message, "err");
              }
            }}
          />
          Auto-upload finished edits to YouTube
        </label>
        <p className="mt-2 text-xs text-muted">
          Publishes publicly at the next free IST slot: 7:00, 14:00, 18:00, or 21:00. Enable YouTube Data API v3, then reconnect Google.
        </p>
        <a className="mt-3 inline-block text-sm underline" href={`${API_URL}/api/auth/google`}>
          Reconnect Google
        </a>
      </Card>
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
