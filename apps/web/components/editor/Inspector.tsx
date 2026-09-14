"use client";

import type { CaptionPhrase, EditPlan, EditSegment } from "@/lib/api";
import type { Selection } from "./EditorTimeline";
import { CaptionControls } from "./CaptionControls";

export function Inspector({
  selection,
  plan,
  phrases,
  duration,
  onPlan,
  onPhrases,
}: {
  selection: Selection | null;
  plan: EditPlan;
  phrases: CaptionPhrase[];
  duration: number;
  onPlan: (p: EditPlan) => void;
  onPhrases: (p: CaptionPhrase[]) => void;
}) {
  const seg: EditSegment | null = selection?.type === "broll" ? plan.segments[selection.index] : null;
  const phrase = selection?.type === "caption" ? phrases[selection.index] : null;

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden border-l border-line bg-panel text-sm">
      <div className="shrink-0 border-b border-line px-4 py-3 text-xs uppercase tracking-wide text-white/40">Inspector</div>
      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-contain p-4">
      {!selection && <p className="mt-4 text-white/50">Select a clip on the timeline.</p>}
      {selection?.type === "aroll" && (
        <p className="mt-4 text-white/70">Talking-head A-roll spans the full {duration.toFixed(1)}s clip. Trim B-roll overlays to reveal more of this track.</p>
      )}
      {selection?.type === "music" && (
        <label className="mt-4 block">
          <div className="text-white/60">Music volume</div>
          <input
            type="range"
            min={0}
            max={40}
            value={Math.round((plan.music_volume ?? 0.18) * 100)}
            className="mt-2 w-full"
            onChange={(e) => onPlan({ ...plan, music_volume: Number(e.target.value) / 100 })}
          />
          <div className="mt-1 text-xs text-white/40">{Math.round((plan.music_volume ?? 0.18) * 100)}%</div>
        </label>
      )}
      {seg && selection?.type === "broll" && (
        <div className="mt-4 space-y-3">
          <div>
            <div className="text-white/60">B-roll</div>
            <div className="mt-1 font-medium">{seg.broll_query}</div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <label>
              In
              <input
                type="number"
                step="0.1"
                className="mt-1 w-full rounded-lg border border-line bg-ink px-2 py-1 text-white"
                value={seg.start.toFixed(2)}
                onChange={(e) => {
                  const start = Number(e.target.value);
                  const next = plan.segments.map((s, i) => (i === selection.index ? { ...s, start } : s));
                  onPlan({ ...plan, segments: next });
                }}
              />
            </label>
            <label>
              Out
              <input
                type="number"
                step="0.1"
                className="mt-1 w-full rounded-lg border border-line bg-ink px-2 py-1 text-white"
                value={seg.end.toFixed(2)}
                onChange={(e) => {
                  const end = Number(e.target.value);
                  const next = plan.segments.map((s, i) => (i === selection.index ? { ...s, end } : s));
                  onPlan({ ...plan, segments: next });
                }}
              />
            </label>
          </div>
          <button
            className="rounded-lg bg-red-500/20 px-3 py-2 text-red-200"
            onClick={() => {
              const next = plan.segments.map((s, i) =>
                i === selection.index ? { ...s, visual: "talking_head" as const, broll_query: null, broll_type: null } : s
              );
              onPlan({ ...plan, segments: next });
            }}
          >
            Delete overlay
          </button>
        </div>
      )}
      <CaptionControls plan={plan} phrases={phrases} onPlan={onPlan} onPhrases={onPhrases} />
      {phrase && selection?.type === "caption" && (
        <label className="mt-4 block">
          <div className="text-white/60">Caption text</div>
          <textarea
            className="mt-1 h-24 w-full rounded-lg border border-line bg-ink p-2 text-white"
            value={phrase.words.map((w) => w.text).join(" ")}
            onChange={(e) => {
              const parts = e.target.value.trim().split(/\s+/).filter(Boolean);
            if (!parts.length) return;
              const span = Math.max(phrase.end - phrase.start, 0.2);
              const step = span / Math.max(parts.length, 1);
              const words = parts.map((text, i) => ({
                text,
                start: phrase.start + i * step,
                end: phrase.start + (i + 1) * step,
              }));
              onPhrases(phrases.map((p, i) => (i === selection.index ? { ...p, words } : p)));
            }}
          />
        </label>
      )}
      </div>
    </aside>
  );
}
