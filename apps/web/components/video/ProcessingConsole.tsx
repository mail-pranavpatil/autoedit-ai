"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { type Video } from "@/lib/api";
import { formatProgressPct, useSmoothProgress } from "@/lib/useSmoothProgress";
import { PROCESS_STEPS, PROCESS_STEP_ORDER, stageTitle } from "@/lib/stageCopy";
import { Check, X, Loader } from "lucide-react";

const ORDER = PROCESS_STEP_ORDER;

export { isProcessingStatus } from "@/lib/api";

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
      const stage = stageTitle(video.failedStage || video.currentStage);
      return [
        ...done,
        {
          status: "FAILED",
          title: "Failed",
          line: stage ? `Something went wrong during "${stage}".` : "Something went wrong.",
          kind: "error" as const,
        },
      ];
    }
    const current = ready ? PROCESS_STEPS.length : Math.max(idx, 0);
    return PROCESS_STEPS.map((s, i) => ({
      ...s,
      kind: i < current ? ("done" as const) : i === current ? ("active" as const) : ("pending" as const),
    })).filter((s) => s.kind !== "pending");
  }, [failed, idx, ready, video.currentStage, video.failedStage, video.status]);

  useEffect(() => {
    setVisibleCount(lines.length);
  }, [lines.length, video.status]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [visibleCount, video.progress, video.currentStage]);

  const shown = lines.slice(0, Math.max(visibleCount, 1));
  const smooth = useSmoothProgress(video.progress || 0, video.status);
  const pct = failed ? video.progress || 0 : video.status === "READY" && smooth >= 99.5 ? 100 : Math.max(smooth, 1);

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-ink">
      <div className="border-b border-line px-4 py-3">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">{failed ? "Stopped" : video.status === "READY" ? "Finished" : "Working on your reel"}</span>
          <span className="tabular-nums text-muted">{formatProgressPct(pct)}</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
          <div
            className={`h-full rounded-full ${failed ? "bg-red-400" : "bg-accent"}`}
            style={{ width: `${Math.min(100, pct)}%` }}
          />
        </div>
        {video.currentStage && video.status !== "READY" && !failed && (
          <p className="mt-2 text-xs text-muted">{stageTitle(video.currentStage)}</p>
        )}
      </div>
      <div ref={logRef} className="max-h-[420px] overflow-y-auto px-4 py-4 font-mono text-[13px] leading-6">
        {shown.map((line, i) => (
          <div key={`${line.status}-${i}`} className="flex gap-3">
            <span className="w-4 shrink-0 text-center">
              {line.kind === "done" && <Check className="inline h-3.5 w-3.5 text-accent" />}
              {line.kind === "active" && <Loader className="inline h-3.5 w-3.5 animate-spin text-accent" />}
              {line.kind === "error" && <X className="inline h-3.5 w-3.5 text-red-400" />}
              {line.kind === "pending" && <span className="text-white/20">·</span>}
            </span>
            <p className={line.kind === "active" ? "text-white" : line.kind === "error" ? "text-red-300" : line.kind === "pending" ? "text-white/30" : "text-white/70"}>
              <span className="mr-2 text-[11px] uppercase tracking-wide text-muted">{line.title}</span>
              {line.line}
              {line.kind === "active" && <span className="ml-1 inline-block h-4 w-0.5 animate-pulse rounded-sm bg-accent" />}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
