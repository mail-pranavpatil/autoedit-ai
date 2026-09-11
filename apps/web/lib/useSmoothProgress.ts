"use client";

import { useEffect, useRef, useState } from "react";
import { isProcessingStatus } from "@/lib/api";

/** How far the bar may creep while a stage has not reported the next milestone. */
const STAGE_CEILING: Record<string, number> = {
  QUEUED: 9,
  DOWNLOADING: 28,
  DOWNLOADED: 28,
  PROBING: 27,
  TRANSCRIBING: 42,   // Whisper can take 30-90s; give the bar room to creep visibly
  TRANSCRIBED: 42,
  PLANNING: 54,
  PLAN_READY: 54,
  SEARCHING_BROLL: 90,
  BROLL_READY: 91,
  RENDERING: 97,
  RENDERED: 97,
  VALIDATING: 99,
  READY: 100,
};

function ceilingFor(status: string, server: number) {
  if (status === "FAILED") return Math.max(0, server);
  if (status === "READY") return 100;
  const mapped = STAGE_CEILING[status];
  if (mapped != null) return Math.max(mapped, server);
  return Math.min(99, Math.max(server + 8, server));
}

export function useSmoothProgress(serverProgress: number, status?: string | null) {
  const server = Math.max(0, Math.min(100, serverProgress || 0));
  const [displayed, setDisplayed] = useState(() => (status === "READY" ? 100 : Math.max(server, 1)));
  const valueRef = useRef(displayed);
  const serverRef = useRef(server);
  const statusRef = useRef(status || "");

  serverRef.current = server;
  statusRef.current = status || "";

  useEffect(() => {
    let frame = 0;
    let last = performance.now();

    const tick = (now: number) => {
      const dt = Math.min(0.12, (now - last) / 1000);
      last = now;
      const st = statusRef.current;
      const floor = Math.max(0, serverRef.current);
      let x = valueRef.current;

      if (st === "FAILED" || (!isProcessingStatus(st) && st !== "READY")) {
        valueRef.current = floor;
        setDisplayed(floor);
        return;
      }

      if (st === "READY") {
        x += (100 - x) * (1 - Math.exp(-dt / 0.32));
        if (x >= 99.5) x = 100;
      } else {
        const cap = ceilingFor(st, floor);
        if (floor > x + 0.2) {
          x += (floor - x) * (1 - Math.exp(-dt / 0.6));
          if (floor - x < 0.2) x = floor;
        } else if (x < cap) {
          x += (cap - x) * (1 - Math.exp(-dt / 12));
          x = Math.min(x, cap - 0.08);
        }
      }

      valueRef.current = x;
      setDisplayed(x);
      if (st === "READY" && x >= 100) return;
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [status]);

  useEffect(() => {
    if (status === "READY") return;
    if (status === "FAILED") {
      valueRef.current = server;
      setDisplayed(server);
    }
  }, [server, status]);

  return displayed;
}

export function formatProgressPct(value: number) {
  return `${Math.round(value)}%`;
}

export function SmoothPercent({ progress, status }: { progress: number; status?: string | null }) {
  const pct = useSmoothProgress(progress, status);
  const value = status === "FAILED" ? progress : pct;
  return formatProgressPct(value);
}
