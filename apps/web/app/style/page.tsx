"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";
import {
  applyCaptionPreset,
  normalizeCaptionStyle,
  type CaptionStyle,
} from "@/components/editor/captionStyle";
import { CaptionPresetPicker, CaptionStyleFields } from "@/components/editor/CaptionStyleFields";
import { Card } from "@/components/common/Card";
import { Monitor, Sparkles, Type, Volume2 } from "lucide-react";

const field = "mt-1 w-full rounded-xl border border-line bg-ink px-3 py-2";

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
  sfx_debug?: boolean;
  captions_enabled?: boolean;
  preferred_music_category?: string | null;
  caption_style?: CaptionStyle | null;
};

export default function StylePage() {
  const [style, setStyle] = useState<Style | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api<Style>("/api/style")
      .then((s) =>
        setStyle({
          ...s,
          caption_style: normalizeCaptionStyle(s.caption_style),
        }),
      )
      .catch((e) => toast(e.message, "err"));
  }, []);

  if (!style) return <p className="text-muted">Loading style profile…</p>;

  const cap = normalizeCaptionStyle(style.caption_style);

  function patchCaption(partial: Partial<CaptionStyle>) {
    setStyle((prev) => (prev ? { ...prev, caption_style: { ...normalizeCaptionStyle(prev.caption_style), ...partial } } : prev));
  }

  async function save() {
    if (!style) return;
    setSaving(true);
    try {
      const saved = await api<Style>("/api/style", {
        method: "PUT",
        body: JSON.stringify({
          profile: {
            ...style,
            caption_style: normalizeCaptionStyle(style.caption_style),
          },
        }),
      });
      setStyle({ ...saved, caption_style: normalizeCaptionStyle(saved.caption_style) });
      toast("Style saved — re-process a video to apply it");
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl pb-16">
      <h1 className="text-2xl font-semibold">Style profile</h1>
      <p className="mt-1 text-sm text-muted">
        Defaults for every AI auto-edit. Save, then process (or re-process) a video — existing plans are restamped
        from this profile. Per-video editor export still uses whatever you set in the inspector.
      </p>
      <Card className="mt-8 space-y-4 p-5">
        <h2 className="flex items-center gap-2 font-medium"><Monitor className="h-4 w-4 text-muted" /> Output</h2>
        <div className="text-sm text-muted">
          {style.aspect_ratio} · {style.resolution}
        </div>
        <label className="block text-sm">
          B-roll frequency
          <select className={field} value={style.broll_frequency} onChange={(e) => setStyle({ ...style, broll_frequency: e.target.value })}>
            <option value="low">Low (~every 3.5s)</option>
            <option value="medium">Medium (~every 2–3s)</option>
            <option value="high">High (~every 2s)</option>
          </select>
        </label>
        <p className="text-xs text-muted">
          Medium keeps a full-screen B-roll cut about every 2–3 seconds.
        </p>
        <label className="block text-sm">
          B-roll type
          <select className={field} value={style.broll_type} onChange={(e) => setStyle({ ...style, broll_type: e.target.value })}>
            <option value="video">Video</option>
            <option value="images">Images</option>
            <option value="both">Both</option>
          </select>
        </label>
      </Card>
      <Card className="mt-4 space-y-3 p-5">
        <h2 className="flex items-center gap-2 font-medium"><Sparkles className="h-4 w-4 text-muted" /> Animations</h2>
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
      </Card>
      <Card className="mt-4 space-y-4 p-5">
        <h2 className="flex items-center gap-2 font-medium"><Type className="h-4 w-4 text-muted" /> Captions</h2>
        <p className="text-sm text-muted">Applied to every new auto-edit (preset, words per line, colors, position).</p>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={style.captions_enabled !== false}
            onChange={(e) => setStyle({ ...style, captions_enabled: e.target.checked })}
          />
          Burn captions into new edits
        </label>
        <CaptionPresetPicker style={cap} onSelect={(id) => setStyle({ ...style, caption_style: applyCaptionPreset(id) })} />
        <details className="text-sm">
          <summary className="cursor-pointer text-muted">Customize further</summary>
          <div className="mt-3 space-y-4">
            <CaptionStyleFields style={cap} onChange={patchCaption} onWordsPerLine={(n) => patchCaption({ words_per_line: n })} />
          </div>
        </details>
      </Card>
      <Card className="mt-4 space-y-3 p-5">
        <h2 className="flex items-center gap-2 font-medium"><Volume2 className="h-4 w-4 text-muted" /> Audio</h2>
        <label className="block text-sm">
          Preferred music
          <select
            className={field}
            value={style.preferred_music_category || "auto"}
            onChange={(e) =>
              setStyle({
                ...style,
                preferred_music_category: e.target.value === "auto" ? null : e.target.value,
              })
            }
          >
            <option value="auto">Auto (emotion + story arc)</option>
            {(
              style.music_categories || ["thank_you", "cornfield_chase", "feeling_blue"]
            ).map((c) => (
              <option key={c} value={c}>
                {
                  {
                    thank_you: "Thank You — warm / gratitude",
                    cornfield_chase: "Cornfield Chase — cinematic / high stakes",
                    feeling_blue: "Feeling Blue — calm / reflective",
                  }[c] || c
                }
              </option>
            ))}
          </select>
        </label>
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
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={Boolean(style.sfx_debug)} onChange={(e) => setStyle({ ...style, sfx_debug: e.target.checked })} />
          SFX decision debug log
        </label>
      </Card>
      <Button className="mt-6" disabled={saving} onClick={save}>
        Save style
      </Button>
    </div>
  );
}
