"use client";

import type { CaptionPhrase, EditPlan } from "@/lib/api";
import { applyCaptionPreset, normalizeCaptionStyle, type CaptionStyle } from "./captionStyle";

const PRESETS: { id: CaptionStyle["preset"]; label: string }[] = [
  { id: "classic", label: "Classic pill" },
  { id: "hormozi", label: "Hormozi" },
  { id: "bold", label: "Bold outline" },
  { id: "minimal", label: "Minimal" },
  { id: "neon", label: "Neon" },
  { id: "subtitle", label: "Subtitles" },
];

export function CaptionControls({
  plan,
  phrases,
  onPlan,
  onPhrases,
}: {
  plan: EditPlan;
  phrases: CaptionPhrase[];
  onPlan: (p: EditPlan) => void;
  onPhrases: (p: CaptionPhrase[]) => void;
}) {
  const style = normalizeCaptionStyle(plan.caption_style);

  function patch(partial: Partial<CaptionStyle>) {
    onPlan({ ...plan, caption_style: { ...style, ...partial } });
  }

  function setWordsPerLine(n: number) {
    const words = phrases.flatMap((p) => p.words);
    const next: CaptionPhrase[] = [];
    for (let i = 0; i < words.length; i += n) {
      const chunk = words.slice(i, i + n);
      if (!chunk.length) continue;
      next.push({ start: chunk[0].start, end: chunk[chunk.length - 1].end, words: chunk });
    }
    onPhrases(next.length ? next : phrases);
    patch({ words_per_line: n });
  }

  return (
    <div className="mt-6 space-y-3 border-t border-white/10 pt-4">
      <div className="text-xs uppercase tracking-wide text-white/40">Captions</div>
      <label className="flex items-center gap-2 text-white/80">
        <input
          type="checkbox"
          checked={plan.captions_enabled !== false}
          onChange={(e) => onPlan({ ...plan, captions_enabled: e.target.checked })}
        />
        Show captions
      </label>
      <div className="grid grid-cols-2 gap-1.5">
        {PRESETS.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => {
              const next = applyCaptionPreset(p.id);
              const words = phrases.flatMap((ph) => ph.words);
              const grouped: CaptionPhrase[] = [];
              for (let i = 0; i < words.length; i += next.words_per_line) {
                const chunk = words.slice(i, i + next.words_per_line);
                if (!chunk.length) continue;
                grouped.push({ start: chunk[0].start, end: chunk[chunk.length - 1].end, words: chunk });
              }
              if (grouped.length) onPhrases(grouped);
              onPlan({ ...plan, caption_style: next, captions_enabled: true });
            }}
            className={`rounded-lg px-2 py-1.5 text-left text-[11px] ${
              style.preset === p.id ? "bg-accent text-ink" : "bg-white/5 text-white/80 hover:bg-white/10"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      <label className="block text-xs text-white/60">
        Size {style.size}px
        <input
          type="range"
          min={24}
          max={96}
          value={style.size}
          className="mt-1 w-full"
          onChange={(e) => patch({ size: Number(e.target.value) })}
        />
      </label>
      <label className="block text-xs text-white/60">
        Position
        <select
          className="mt-1 w-full rounded bg-white/5 px-2 py-1.5 text-sm text-white"
          value={style.position}
          onChange={(e) => patch({ position: e.target.value as CaptionStyle["position"], y_percent: null })}
        >
          <option value="top">Top</option>
          <option value="center">Center</option>
          <option value="lower">Lower middle</option>
          <option value="bottom">Bottom</option>
        </select>
      </label>
      <label className="block text-xs text-white/60">
        Fine-tune Y {Math.round(style.y_percent ?? { top: 12, center: 46, lower: 62, bottom: 82 }[style.position])}%
        <input
          type="range"
          min={8}
          max={88}
          value={style.y_percent ?? { top: 12, center: 46, lower: 62, bottom: 82 }[style.position]}
          className="mt-1 w-full"
          onChange={(e) => patch({ y_percent: Number(e.target.value) })}
        />
      </label>
      <div className="grid grid-cols-2 gap-2 text-xs text-white/60">
        <label>
          Font
          <select
            className="mt-1 w-full rounded bg-white/5 px-2 py-1.5 text-white"
            value={style.font}
            onChange={(e) => patch({ font: e.target.value as CaptionStyle["font"] })}
          >
            <option value="serif">Serif</option>
            <option value="sans">Sans</option>
            <option value="mono">Mono</option>
          </select>
        </label>
        <label>
          Align
          <select
            className="mt-1 w-full rounded bg-white/5 px-2 py-1.5 text-white"
            value={style.align}
            onChange={(e) => patch({ align: e.target.value as CaptionStyle["align"] })}
          >
            <option value="left">Left</option>
            <option value="center">Center</option>
            <option value="right">Right</option>
          </select>
        </label>
        <label>
          Active
          <input
            type="color"
            className="mt-1 h-8 w-full rounded bg-transparent"
            value={style.active_color}
            onChange={(e) => patch({ active_color: e.target.value.toUpperCase() })}
          />
        </label>
        <label>
          Rest
          <input
            type="color"
            className="mt-1 h-8 w-full rounded bg-transparent"
            value={style.muted_color}
            onChange={(e) => patch({ muted_color: e.target.value.toUpperCase() })}
          />
        </label>
        <label>
          Background
          <select
            className="mt-1 w-full rounded bg-white/5 px-2 py-1.5 text-white"
            value={style.background}
            onChange={(e) => patch({ background: e.target.value as CaptionStyle["background"] })}
          >
            <option value="pill">Pill</option>
            <option value="box">Box</option>
            <option value="none">None</option>
          </select>
        </label>
        <label>
          BG color
          <input
            type="color"
            className="mt-1 h-8 w-full rounded bg-transparent"
            value={style.background_color}
            onChange={(e) => patch({ background_color: e.target.value.toUpperCase() })}
          />
        </label>
      </div>
      <label className="block text-xs text-white/60">
        Background opacity {Math.round(style.background_opacity * 100)}%
        <input
          type="range"
          min={0}
          max={100}
          value={Math.round(style.background_opacity * 100)}
          className="mt-1 w-full"
          onChange={(e) => patch({ background_opacity: Number(e.target.value) / 100 })}
        />
      </label>
      <label className="block text-xs text-white/60">
        Outline {style.stroke_width}px
        <input
          type="range"
          min={0}
          max={12}
          value={style.stroke_width}
          className="mt-1 w-full"
          onChange={(e) => patch({ stroke_width: Number(e.target.value) })}
        />
      </label>
      <label className="block text-xs text-white/60">
        Words per line {style.words_per_line}
        <input
          type="range"
          min={2}
          max={8}
          value={style.words_per_line}
          className="mt-1 w-full"
          onChange={(e) => setWordsPerLine(Number(e.target.value))}
        />
      </label>
      <div className="flex flex-col gap-2 text-xs text-white/80">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={style.uppercase} onChange={(e) => patch({ uppercase: e.target.checked })} />
          Uppercase
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={style.highlight === "word"}
            onChange={(e) => patch({ highlight: e.target.checked ? "word" : "none" })}
          />
          Highlight spoken word
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={style.shadow} onChange={(e) => patch({ shadow: e.target.checked })} />
          Shadow
        </label>
      </div>
    </div>
  );
}
