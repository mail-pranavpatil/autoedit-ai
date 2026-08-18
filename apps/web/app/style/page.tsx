"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";
import {
  applyCaptionPreset,
  normalizeCaptionStyle,
  toColorInput,
  type CaptionStyle,
} from "@/components/editor/captionStyle";

const PRESETS: { id: CaptionStyle["preset"]; label: string; active: string; rest: string; bg: string }[] = [
  { id: "classic", label: "Classic pill", active: "#FFFFFF", rest: "#B8B8B8", bg: "#000000" },
  { id: "hormozi", label: "Hormozi", active: "#FFE500", rest: "#FFFFFF", bg: "#000000" },
  { id: "bold", label: "Bold outline", active: "#FFFFFF", rest: "#D1D5DB", bg: "transparent" },
  { id: "minimal", label: "Minimal", active: "#FFFFFF", rest: "#FFFFFF", bg: "transparent" },
  { id: "neon", label: "Neon", active: "#5CFF9F", rest: "#9CA3AF", bg: "#111827" },
  { id: "subtitle", label: "Subtitles", active: "#FFFFFF", rest: "#E5E7EB", bg: "transparent" },
];

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
  const yValue = cap.y_percent ?? { top: 12, center: 46, lower: 62, bottom: 82 }[cap.position];

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
      <section className="mt-8 space-y-4 rounded-2xl border border-line bg-panel p-5">
        <h2 className="font-medium">Output</h2>
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
      <section className="mt-4 space-y-4 rounded-2xl border border-line bg-panel p-5">
        <h2 className="font-medium">Captions</h2>
        <p className="text-sm text-muted">Applied to every new auto-edit (preset, words per line, colors, position).</p>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={style.captions_enabled !== false}
            onChange={(e) => setStyle({ ...style, captions_enabled: e.target.checked })}
          />
          Burn captions into new edits
        </label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {PRESETS.map((p) => {
            const selected = cap.preset === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setStyle({ ...style, caption_style: applyCaptionPreset(p.id) })}
                className={`rounded-xl border px-2 py-2 text-left ${selected ? "border-accent bg-accent/15" : "border-line bg-ink hover:bg-white/5"}`}
              >
                <div
                  className="mb-1.5 flex h-6 items-center justify-center rounded-full px-2"
                  style={{ background: p.bg === "transparent" ? "#1a1d24" : p.bg }}
                >
                  <span className="text-[10px] font-semibold" style={{ color: p.active }}>
                    Aa
                  </span>
                  <span className="ml-0.5 text-[10px]" style={{ color: p.rest }}>
                    bb
                  </span>
                </div>
                <div className={`text-[11px] ${selected ? "text-accent" : "text-muted"}`}>{p.label}</div>
              </button>
            );
          })}
        </div>
        <label className="block text-sm">
          Words per line {cap.words_per_line}
          <input
            type="range"
            min={2}
            max={8}
            value={cap.words_per_line}
            className="mt-1 w-full"
            onChange={(e) => patchCaption({ words_per_line: Number(e.target.value) })}
          />
        </label>
        <label className="block text-sm">
          Size {cap.size}px
          <input type="range" min={24} max={96} value={cap.size} className="mt-1 w-full" onChange={(e) => patchCaption({ size: Number(e.target.value) })} />
        </label>
        <label className="block text-sm">
          Position
          <select
            className={field}
            value={cap.position}
            onChange={(e) => patchCaption({ position: e.target.value as CaptionStyle["position"], y_percent: null })}
          >
            <option value="top">Top</option>
            <option value="center">Center</option>
            <option value="lower">Lower middle</option>
            <option value="bottom">Bottom</option>
          </select>
        </label>
        <label className="block text-sm">
          Fine-tune Y {Math.round(yValue)}%
          <input type="range" min={8} max={88} value={yValue} className="mt-1 w-full" onChange={(e) => patchCaption({ y_percent: Number(e.target.value) })} />
        </label>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <label>
            Font
            <select className={field} value={cap.font} onChange={(e) => patchCaption({ font: e.target.value as CaptionStyle["font"] })}>
              <option value="serif">Serif</option>
              <option value="sans">Sans</option>
              <option value="mono">Mono</option>
            </select>
          </label>
          <label>
            Align
            <select className={field} value={cap.align} onChange={(e) => patchCaption({ align: e.target.value as CaptionStyle["align"] })}>
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
          </label>
          <label>
            Active color
            <input
              type="color"
              className="mt-1 h-9 w-full cursor-pointer rounded-xl border border-line bg-ink"
              value={toColorInput(cap.active_color)}
              onChange={(e) => patchCaption({ active_color: e.target.value.toUpperCase() })}
            />
          </label>
          <label>
            Rest color
            <input
              type="color"
              className="mt-1 h-9 w-full cursor-pointer rounded-xl border border-line bg-ink"
              value={toColorInput(cap.muted_color)}
              onChange={(e) => patchCaption({ muted_color: e.target.value.toUpperCase() })}
            />
          </label>
          <label>
            Background
            <select className={field} value={cap.background} onChange={(e) => patchCaption({ background: e.target.value as CaptionStyle["background"] })}>
              <option value="pill">Pill</option>
              <option value="box">Box</option>
              <option value="none">None</option>
            </select>
          </label>
          <label>
            BG color
            <input
              type="color"
              className="mt-1 h-9 w-full cursor-pointer rounded-xl border border-line bg-ink"
              value={toColorInput(cap.background_color, "#000000")}
              onChange={(e) => patchCaption({ background_color: e.target.value.toUpperCase() })}
            />
          </label>
        </div>
        <label className="block text-sm">
          Background opacity {Math.round(cap.background_opacity * 100)}%
          <input
            type="range"
            min={0}
            max={100}
            value={Math.round(cap.background_opacity * 100)}
            className="mt-1 w-full"
            onChange={(e) => patchCaption({ background_opacity: Number(e.target.value) / 100 })}
          />
        </label>
        <label className="block text-sm">
          Outline {cap.stroke_width}px
          <input type="range" min={0} max={12} value={cap.stroke_width} className="mt-1 w-full" onChange={(e) => patchCaption({ stroke_width: Number(e.target.value) })} />
        </label>
        <div className="flex flex-col gap-2 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={cap.uppercase} onChange={(e) => patchCaption({ uppercase: e.target.checked })} />
            Uppercase
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={cap.highlight === "word"}
              onChange={(e) => patchCaption({ highlight: e.target.checked ? "word" : "none" })}
            />
            Highlight spoken word
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={cap.shadow} onChange={(e) => patchCaption({ shadow: e.target.checked })} />
            Shadow
          </label>
        </div>
      </section>
      <section className="mt-4 space-y-3 rounded-2xl border border-line bg-panel p-5">
        <h2 className="font-medium">Audio</h2>
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
      </section>
      <Button className="mt-6" disabled={saving} onClick={save}>
        Save style
      </Button>
    </div>
  );
}
