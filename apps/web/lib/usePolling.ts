"use client";

import { useEffect, useRef } from "react";

export function usePolling(enabled: boolean, fn: () => Promise<unknown>, intervalMs = 1500) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function tick() {
      try {
        await fnRef.current();
      } catch {
        // Keep polling through transient 429s / network blips.
      }
      if (!cancelled) timer = setTimeout(tick, intervalMs);
    }

    tick();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [enabled, intervalMs]);
}
