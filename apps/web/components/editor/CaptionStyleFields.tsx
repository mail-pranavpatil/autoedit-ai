"use client";

import { toColorInput, type CaptionStyle } from "./captionStyle";

export const CAPTION_PRESET_SWATCHES: { id: CaptionStyle["preset"]; label: string; active: string; rest: string; bg: string }[] = [
  { id: "classic", label: "Classic pill", active: "#FFFFFF", rest: "#B8B8B8", bg: "#000000" },
  { id: "hormozi", label: "Hormozi", active: "#FFE500", rest: "#FFFFFF", bg: "#000000" },
  { id: "bold", label: "Bold outline", active: "#FFFFFF", rest: "#D1D5DB", bg: "transparent" },
  { id: "minimal", label: "Minimal", active: "#FFFFFF", rest: "#FFFFFF", bg: "transparent" },
  { id: "neon", label: "Neon", active: "#5CFF9F", rest: "#9CA3AF", bg: "#111827" },
  { id: "subtitle", label: "Subtitles", active: "#FFFFFF", rest: "#E5E7EB", bg: "transparent" },
];

const field = "mt-1 w-full rounded-lg border border-line bg-ink px-2 py-1.5 text-sm text-white outline-none";

/** Preset swatch grid, split out from CaptionStyleFields so a caller (the
 * Style Profile page) can show it as the simple default choice and put the
 * rest of the controls behind a "Customize" disclosure. */
export function CaptionPresetPicker({ style, onSelect }: { style: CaptionStyle; onSelect: (id: CaptionStyle["preset"]) => void }) {
  return (
    <div className="grid grid-cols-2 gap-1.5">
      {CAPTION_PRESET_SWATCHES.map((p) => {
        const selected = style.preset === p.id;
        return (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelect(p.id)}
            className={`rounded-lg border px-2 py-2 text-left ${
              selected ? "border-accent bg-accent/15" : "border-white/10 bg-white/5 hover:bg-white/10"
            }`}
          >
            <div className="mb-1.5 flex h-6 items-center justify-center rounded-full px-2" style={{ background: p.bg === "transparent" ? "#1a1d24" : p.bg }}>
              <span className="text-[10px] font-semibold" style={{ color: p.active }}>
                Aa
              </span>
              <span className="ml-0.5 text-[10px]" style={{ color: p.rest }}>
                bb
              </span>
            </div>
            <div className={`text-[11px] ${selected ? "text-accent" : "text-white/80"}`}>{p.label}</div>
          </button>
        );
      })}
    </div>
  );
}

/**
 * Every other caption control, used by both the editor's Inspector (per-video,
 * live phrases) and the global Style Profile page (defaults only).
 * Words-per-line changes are handed back un-applied so each context can
 * decide whether to also regroup live caption phrases (editor) or just patch
 * the stored default (style profile).
 */
export function CaptionStyleFields({
  style,
  onChange,
  onWordsPerLine,
}: {
  style: CaptionStyle;
  onChange: (patch: Partial<CaptionStyle>) => void;
  onWordsPerLine: (n: number) => void;
}) {
  const yValue = style.y_percent ?? { top: 12, center: 46, lower: 62, bottom: 82 }[style.position];

  return (
    <>
      <label className="block text-xs text-white/60">
        Size {style.size}px
        <input type="range" min={24} max={96} value={style.size} className="mt-1 w-full" onChange={(e) => onChange({ size: Number(e.target.value) })} />
      </label>
      <label className="block text-xs text-white/60">
        Position
        <select className={field} value={style.position} onChange={(e) => onChange({ position: e.target.value as CaptionStyle["position"], y_percent: null })}>
          <option value="top">Top</option>
          <option value="center">Center</option>
          <option value="lower">Lower middle</option>
          <option value="bottom">Bottom</option>
        </select>
      </label>
      <label className="block text-xs text-white/60">
        Fine-tune Y {Math.round(yValue)}%
        <input type="range" min={8} max={88} value={yValue} className="mt-1 w-full" onChange={(e) => onChange({ y_percent: Number(e.target.value) })} />
      </label>
      <div className="grid grid-cols-2 gap-2 text-xs text-white/60">
        <label>
          Font
          <select className={field} value={style.font} onChange={(e) => onChange({ font: e.target.value as CaptionStyle["font"] })}>
            <option value="serif">Serif</option>
            <option value="sans">Sans</option>
            <option value="mono">Mono</option>
          </select>
        </label>
        <label>
          Align
          <select className={field} value={style.align} onChange={(e) => onChange({ align: e.target.value as CaptionStyle["align"] })}>
            <option value="left">Left</option>
            <option value="center">Center</option>
            <option value="right">Right</option>
          </select>
        </label>
        <label>
          Active
          <input type="color" className="mt-1 h-8 w-full cursor-pointer rounded border border-line bg-ink" value={toColorInput(style.active_color)} onChange={(e) => onChange({ active_color: e.target.value.toUpperCase() })} />
        </label>
        <label>
          Rest
          <input type="color" className="mt-1 h-8 w-full cursor-pointer rounded border border-line bg-ink" value={toColorInput(style.muted_color)} onChange={(e) => onChange({ muted_color: e.target.value.toUpperCase() })} />
        </label>
        <label>
          Background
          <select className={field} value={style.background} onChange={(e) => onChange({ background: e.target.value as CaptionStyle["background"] })}>
            <option value="pill">Pill</option>
            <option value="box">Box</option>
            <option value="none">None</option>
          </select>
        </label>
        <label>
          BG color
          <input type="color" className="mt-1 h-8 w-full cursor-pointer rounded border border-line bg-ink" value={toColorInput(style.background_color, "#000000")} onChange={(e) => onChange({ background_color: e.target.value.toUpperCase() })} />
        </label>
      </div>
      <label className="block text-xs text-white/60">
        Background opacity {Math.round(style.background_opacity * 100)}%
        <input type="range" min={0} max={100} value={Math.round(style.background_opacity * 100)} className="mt-1 w-full" onChange={(e) => onChange({ background_opacity: Number(e.target.value) / 100 })} />
      </label>
      <label className="block text-xs text-white/60">
        Outline {style.stroke_width}px
        <input type="range" min={0} max={12} value={style.stroke_width} className="mt-1 w-full" onChange={(e) => onChange({ stroke_width: Number(e.target.value) })} />
      </label>
      <label className="block text-xs text-white/60">
        Words per line {style.words_per_line}
        <input type="range" min={2} max={8} value={style.words_per_line} className="mt-1 w-full" onChange={(e) => onWordsPerLine(Number(e.target.value))} />
      </label>
      <div className="flex flex-col gap-2 text-xs text-white/80">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={style.uppercase} onChange={(e) => onChange({ uppercase: e.target.checked })} />
          Uppercase
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={style.highlight === "word"} onChange={(e) => onChange({ highlight: e.target.checked ? "word" : "none" })} />
          Highlight spoken word
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={style.shadow} onChange={(e) => onChange({ shadow: e.target.checked })} />
          Shadow
        </label>
      </div>
    </>
  );
}
