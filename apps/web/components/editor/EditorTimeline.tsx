"use client";

import type { ReactNode } from "react";
import type { BrollAsset, CaptionPhrase, EditPlan, EditSegment } from "@/lib/api";

export type Selection =
  | { type: "aroll" }
  | { type: "music" }
  | { type: "broll"; index: number }
  | { type: "caption"; index: number };

export function EditorTimeline({
  duration,
  time,
  plan,
  phrases,
  assets,
  selection,
  onSeek,
  onSelect,
  onMoveBroll,
}: {
  duration: number;
  time: number;
  plan: EditPlan;
  phrases: CaptionPhrase[];
  assets: BrollAsset[];
  selection: Selection | null;
  onSeek: (t: number) => void;
  onSelect: (s: Selection) => void;
  onMoveBroll: (index: number, start: number, end: number) => void;
}) {
  const dur = Math.max(duration, 0.5);
  const px = 100;

  function xToTime(clientX: number, el: HTMLElement) {
    const r = el.getBoundingClientRect();
    return Math.max(0, Math.min(dur, ((clientX - r.left) / r.width) * dur));
  }

  const unused = [...assets];
  const brollClips = plan.segments.map((seg, index) => {
    if (seg.visual !== "broll") return null;
    const i = unused.findIndex((a) => a.query === seg.broll_query);
    const asset = i >= 0 ? unused.splice(i, 1)[0] : unused.shift() || null;
    return { index, seg, asset };
  });

  return (
    <div className="flex h-full flex-col bg-[#12141a]">
      <div
        className="relative flex-1 overflow-x-auto overflow-y-hidden px-3 py-2"
        onClick={(e) => {
          const t = xToTime(e.clientX, e.currentTarget.querySelector("[data-ruler]") as HTMLElement);
          if (!Number.isNaN(t)) onSeek(t);
        }}
      >
        <div data-ruler className="relative" style={{ width: `${dur * px}px`, minWidth: "100%" }}>
          <div className="mb-1 flex h-6 text-[10px] text-white/40">
            {Array.from({ length: Math.ceil(dur) + 1 }, (_, i) => (
              <div key={i} className="shrink-0 border-l border-white/10 pl-1" style={{ width: px }}>
                {i}s
              </div>
            ))}
          </div>
          <Track label="A-roll" color="bg-sky-500/80" selected={selection?.type === "aroll"} onSelect={() => onSelect({ type: "aroll" })}>
            <Clip start={0} end={dur} duration={dur} color="bg-sky-600" label="Talking head" />
          </Track>
          <Track label="B-roll" color="bg-violet-500/80">
            {brollClips.map((clip) => {
              if (!clip) return null;
              const selected = selection?.type === "broll" && selection.index === clip.index;
              return (
                <DraggableClip
                  key={clip.index}
                  start={clip.seg.start}
                  end={clip.seg.end}
                  duration={dur}
                  color={selected ? "bg-violet-400" : "bg-violet-600"}
                  label={clip.seg.broll_query || "B-roll"}
                  selected={selected}
                  onSelect={() => onSelect({ type: "broll", index: clip.index })}
                  onChange={(s, e) => onMoveBroll(clip.index, s, e)}
                />
              );
            })}
          </Track>
          <Track label="Captions" color="bg-amber-500/80">
            {phrases.map((ph, i) => {
              const selected = selection?.type === "caption" && selection.index === i;
              return (
                <Clip
                  key={`${ph.start}-${i}`}
                  start={ph.start}
                  end={ph.end}
                  duration={dur}
                  color={selected ? "bg-amber-300" : "bg-amber-500"}
                  label={ph.words.map((w) => w.text).join(" ")}
                  onSelect={() => onSelect({ type: "caption", index: i })}
                />
              );
            })}
          </Track>
          <Track label="Music" color="bg-emerald-500/80" selected={selection?.type === "music"} onSelect={() => onSelect({ type: "music" })}>
            <Clip start={0} end={dur} duration={dur} color="bg-emerald-600" label="Music bed" />
          </Track>
          <div
            className="pointer-events-none absolute bottom-0 top-6 z-20 w-px bg-white"
            style={{ left: `${(time / dur) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function Track({
  label,
  children,
  color,
  selected,
  onSelect,
}: {
  label: string;
  children: ReactNode;
  color: string;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <div className="mb-1 flex items-stretch">
      <button
        type="button"
        onClick={onSelect}
        className={`w-20 shrink-0 truncate rounded-l px-2 text-left text-[10px] uppercase tracking-wide ${selected ? "bg-white/15 text-white" : "bg-white/5 text-white/50"}`}
      >
        <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${color}`} />
        {label}
      </button>
      <div className="relative h-9 flex-1 rounded-r bg-white/[0.04]">{children}</div>
    </div>
  );
}

function Clip({
  start,
  end,
  duration,
  color,
  label,
  onSelect,
}: {
  start: number;
  end: number;
  duration: number;
  color: string;
  label: string;
  onSelect?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onSelect?.();
      }}
      className={`absolute top-0.5 h-8 overflow-hidden rounded px-1.5 text-left text-[10px] font-medium text-white ${color}`}
      style={{ left: `${(start / duration) * 100}%`, width: `${((end - start) / duration) * 100}%` }}
    >
      <span className="block truncate">{label}</span>
    </button>
  );
}

function DraggableClip({
  start,
  end,
  duration,
  color,
  label,
  selected,
  onSelect,
  onChange,
}: {
  start: number;
  end: number;
  duration: number;
  color: string;
  label: string;
  selected: boolean;
  onSelect: () => void;
  onChange: (start: number, end: number) => void;
}) {
  function pointer(kind: "move" | "start" | "end", ev: React.PointerEvent<HTMLDivElement>) {
    ev.stopPropagation();
    ev.preventDefault();
    onSelect();
    const originX = ev.clientX;
    const origS = start;
    const origE = end;
    const parent = (ev.currentTarget.closest("[data-ruler]") as HTMLElement) || ev.currentTarget.parentElement;
    if (!parent) return;
    const width = parent.getBoundingClientRect().width;
    const move = (e: PointerEvent) => {
      const dt = ((e.clientX - originX) / width) * duration;
      if (kind === "move") {
        const len = origE - origS;
        let ns = origS + dt;
        ns = Math.max(0, Math.min(duration - len, ns));
        onChange(ns, ns + len);
      } else if (kind === "start") {
        onChange(Math.max(0, Math.min(origE - 0.2, origS + dt)), origE);
      } else {
        onChange(origS, Math.max(origS + 0.2, Math.min(duration, origE + dt)));
      }
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  return (
    <div
      className={`absolute top-0.5 h-8 overflow-hidden rounded text-left text-[10px] font-medium text-white ${color} ${selected ? "ring-1 ring-white" : ""}`}
      style={{ left: `${(start / duration) * 100}%`, width: `${((end - start) / duration) * 100}%` }}
      onPointerDown={(e) => pointer("move", e)}
    >
      <div className="absolute inset-y-0 left-0 w-1.5 cursor-ew-resize bg-white/30" onPointerDown={(e) => pointer("start", e)} />
      <span className="block truncate px-2 pt-2">{label}</span>
      <div className="absolute inset-y-0 right-0 w-1.5 cursor-ew-resize bg-white/30" onPointerDown={(e) => pointer("end", e)} />
    </div>
  );
}

export function activeBrollAt(plan: EditPlan, assets: BrollAsset[], time: number): { segment: EditSegment; asset: BrollAsset } | null {
  const unused = [...assets];
  for (const seg of plan.segments) {
    if (seg.visual !== "broll") continue;
    const i = unused.findIndex((a) => a.query === seg.broll_query);
    const asset = i >= 0 ? unused.splice(i, 1)[0] : unused.shift();
    if (asset && time >= seg.start && time < seg.end) return { segment: seg, asset };
  }
  return null;
}
