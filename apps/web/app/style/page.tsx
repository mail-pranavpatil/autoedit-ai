"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";

type Style = {
  aspect_ratio: string;
  resolution: string;
  broll_frequency: string;
  broll_type: string;
  effects: { zoom: boolean; pan: boolean; fade: boolean };
  sfx_enabled: string[];
  music_categories: string[];
  music_volume: number;
  sfx_volume: number;
};

export default function StylePage() {
  const [style, setStyle] = useState<Style | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api<Style>("/api/style").then(setStyle).catch((e) => toast(e.message, "err"));
  }, []);

  if (!style) return <p className="text-muted">Loading style profile…</p>;

  async function save() {
    setSaving(true);
    try {
      await api("/api/style", { method: "PUT", body: JSON.stringify({ profile: style }) });
      toast("Style saved");
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold">Style profile</h1>
      <p className="mt-1 text-sm text-muted">These settings are sent to the edit planner. Rendering stays deterministic.</p>
      <section className="mt-8 space-y-4 rounded-2xl border border-line bg-panel p-5">
        <h2 className="font-medium">Output</h2>
        <div className="text-sm text-muted">
          {style.aspect_ratio} · {style.resolution}
        </div>
        <label className="block text-sm">
          B-roll frequency
          <select
            className="mt-1 w-full rounded-xl border border-line bg-ink px-3 py-2"
            value={style.broll_frequency}
            onChange={(e) => setStyle({ ...style, broll_frequency: e.target.value })}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
        <label className="block text-sm">
          B-roll type
          <select
            className="mt-1 w-full rounded-xl border border-line bg-ink px-3 py-2"
            value={style.broll_type}
            onChange={(e) => setStyle({ ...style, broll_type: e.target.value })}
          >
            <option value="video">Video</option>
            <option value="images">Images</option>
            <option value="both">Both</option>
          </select>
        </label>
      </section>
      <section className="mt-4 space-y-3 rounded-2xl border border-line bg-panel p-5">
        <h2 className="font-medium">Animations</h2>
        {(["zoom", "pan", "fade"] as const).map((k) => (
          <label key={k} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={style.effects[k]}
              onChange={(e) => setStyle({ ...style, effects: { ...style.effects, [k]: e.target.checked } })}
            />
            {k}
          </label>
        ))}
      </section>
      <section className="mt-4 space-y-3 rounded-2xl border border-line bg-panel p-5">
        <h2 className="font-medium">Audio</h2>
        <label className="block text-sm">
          Music volume {Math.round(style.music_volume * 100)}%
          <input
            type="range"
            min={0}
            max={40}
            value={style.music_volume * 100}
            onChange={(e) => setStyle({ ...style, music_volume: Number(e.target.value) / 100 })}
            className="w-full"
          />
        </label>
        <label className="block text-sm">
          SFX volume {Math.round(style.sfx_volume * 100)}%
          <input
            type="range"
            min={0}
            max={50}
            value={style.sfx_volume * 100}
            onChange={(e) => setStyle({ ...style, sfx_volume: Number(e.target.value) / 100 })}
            className="w-full"
          />
        </label>
      </section>
      <Button className="mt-6" disabled={saving} onClick={save}>
        Save style
      </Button>
    </div>
  );
}
