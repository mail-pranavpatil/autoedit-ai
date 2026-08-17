"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Video } from "@/lib/api";

export const PROCESS_STEPS = [
  { status: "QUEUED", title: "Queued", line: "Starting a new edit job…" },
  { status: "DOWNLOADING", title: "Download", line: "Pulling the original clip from Google Drive…" },
  { status: "DOWNLOADED", title: "Downloaded", line: "Got the source file." },
  { status: "PROBING", title: "Inspect", line: "Extracting duration, resolution, and audio…" },
  { status: "TRANSCRIBING", title: "Transcribe", line: "Listening to the talking-head audio and writing a timestamped transcript…" },
  { status: "TRANSCRIBED", title: "Transcript", line: "Transcript is ready." },
  { status: "PLANNING", title: "Thinking", line: "Thinking through B-roll, zooms, music, and sound design…" },
  { status: "PLAN_READY", title: "Edit plan", line: "Locked in a structured edit plan." },
  { status: "SEARCHING_BROLL", title: "Stock search", line: "Searching stock photos and clips that match the script…" },
  { status: "BROLL_READY", title: "Assets", line: "B-roll downloaded and ready to overlay." },
  { status: "RENDERING", title: "Render", line: "Compositing the 9:16 reel — overlays, captions, music, and SFX…" },
  { status: "RENDERED", title: "Written", line: "Finished writing the MP4." },
  { status: "VALIDATING", title: "Validate", line: "Checking resolution, codec, and audio…" },
  { status: "READY", title: "Done", line: "Your reel is ready to preview and download." },
] as const;

const ORDER = PROCESS_STEPS.map((s) => s.status);

export function isProcessingStatus(status: string) {
  return !["READY", "FAILED", "DISCOVERED"].includes(status);
}

function resolveStepIndex(status: string, failedStage?: string | null) {
  if (status === "FAILED") {
    const direct = ORDER.indexOf((failedStage || "") as (typeof ORDER)[number]);
    if (direct >= 0) return direct;
    const lower = (failedStage || "").toLowerCase();
    const found = PROCESS_STEPS.findIndex((s) => lower.includes(s.title.toLowerCase()) || lower.includes(s.status.toLowerCase()));
    if (found >= 0) return found;
    if (lower.includes("render")) return ORDER.indexOf("RENDERING");
    return 0;
  }
  const i = ORDER.indexOf(status as (typeof ORDER)[number]);
  return i >= 0 ? i : 0;
}

export function ProcessingConsole({ video }: { video: Video }) {
  const idx = resolveStepIndex(video.status, video.failedStage);
  const failed = video.status === "FAILED";
  const ready = video.status === "READY";
  const logRef = useRef<HTMLDivElement>(null);
  const [visibleCount, setVisibleCount] = useState(1);

  const lines = useMemo(() => {
    if (failed) {
      const failAt = Math.max(idx, 0);
      const done = PROCESS_STEPS.slice(0, failAt + 1).map((s) => ({
        ...s,
        kind: "done" as const,
      }));
      return [
        ...done,
        {
          status: "FAILED",
          title: "Failed",
          line: video.errorMessage || video.currentStage || "Something went wrong.",
          kind: "error" as const,
        },
      ];
    }
    const current = ready ? PROCESS_STEPS.length : Math.max(idx, 0);
    return PROCESS_STEPS.map((s, i) => ({
      ...s,
      kind: i < current ? ("done" as const) : i === current ? ("active" as const) : ("pending" as const),
    })).filter((s) => s.kind !== "pending");
  }, [failed, idx, ready, video.currentStage, video.errorMessage, video.failedStage, video.status]);

  useEffect(() => {
    setVisibleCount((n) => Math.max(n, Math.min(lines.length, n + 1)));
  }, [lines.length, video.status]);

  useEffect(() => {
    if (lines.length > visibleCount) {
      const t = window.setTimeout(() => setVisibleCount(lines.length), 180);
      return () => clearTimeout(t);
    }
  }, [lines.length, visibleCount]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [visibleCount, video.progress, video.currentStage]);

  const shown = lines.slice(0, Math.max(visibleCount, 1));
  const pct = failed ? video.progress || 0 : video.status === "READY" ? 100 : Math.max(video.progress || 0, 3);

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-[#0b0d12]">
      <div className="border-b border-line px-4 py-3">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">{failed ? "Stopped" : video.status === "READY" ? "Finished" : "Working on your reel"}</span>
          <span className="tabular-nums text-muted">{pct}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
          <div
            className={`h-full rounded-full transition-all duration-700 ${failed ? "bg-red-400" : "bg-accent"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        {video.currentStage && video.status !== "READY" && !failed && (
          <p className="mt-2 text-xs text-muted">{video.currentStage}</p>
        )}
      </div>
      <div ref={logRef} className="max-h-[420px] overflow-y-auto px-4 py-4 font-mono text-[13px] leading-6">
        {shown.map((line, i) => (
          <div key={`${line.status}-${i}`} className="flex gap-3">
            <span className="w-4 shrink-0 text-center">
              {line.kind === "done" && <span className="text-accent">✓</span>}
              {line.kind === "active" && <span className="inline-block h-2 w-2 translate-y-[-1px] rounded-full bg-accent animate-pulse" />}
              {line.kind === "error" && <span className="text-red-400">✕</span>}
              {line.kind === "pending" && <span className="text-white/20">·</span>}
            </span>
            <p className={line.kind === "active" ? "text-white" : line.kind === "error" ? "text-red-300" : line.kind === "pending" ? "text-white/30" : "text-white/70"}>
              <span className="mr-2 text-[11px] uppercase tracking-wide text-muted">{line.title}</span>
              {line.line}
              {line.kind === "active" && <span className="ml-1 animate-pulse text-accent">▍</span>}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
