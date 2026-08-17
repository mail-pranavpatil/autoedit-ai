"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

export default function SystemPage() {
  const [health, setHealth] = useState<Record<string, boolean> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold">System status</h1>
      {error && <p className="mt-4 text-red-300">{error}</p>}
      <div className="mt-6 space-y-2">
        {health &&
          Object.entries(health).map(([k, v]) => (
            <div key={k} className="flex justify-between rounded-xl border border-line bg-panel px-4 py-3">
              <span className="capitalize">{k}</span>
              <span className={v ? "text-accent" : "text-red-300"}>{v ? "ok" : "down"}</span>
            </div>
          ))}
      </div>
    </div>
  );
}
