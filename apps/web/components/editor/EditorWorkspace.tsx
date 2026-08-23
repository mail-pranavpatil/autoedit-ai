"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { API_URL, api, type CaptionPhrase, type EditPlan, type EditorPayload, type Video } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";
import { Inspector } from "./Inspector";
import { MediaBin } from "./MediaBin";
import { EditorTimeline, activeBrollAt, type Selection } from "./EditorTimeline";
import { PreviewStage } from "./PreviewStage";
import { normalizeCaptionStyle, serializeCaptionStyle } from "./captionStyle";
import { SmoothPercent } from "@/lib/useSmoothProgress";

export function EditorWorkspace({ projectId, videoId }: { projectId: string; videoId: string }) {
  const [data, setData] = useState<EditorPayload | null>(null);
  const [plan, setPlan] = useState<EditPlan | null>(null);
  const [phrases, setPhrases] = useState<CaptionPhrase[]>([]);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [exporting, setExporting] = useState(false);
  const mediaRef = useRef<HTMLVideoElement | null>(null);

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    const next = await api<EditorPayload>(`/api/videos/${videoId}/editor`);
    setData(next);
    const busy = !["READY", "FAILED", "DISCOVERED"].includes(next.status);
    if (!opts?.silent || !busy) {
      if (next.editPlan) {
        setPlan({
          ...next.editPlan,
          captions_enabled: next.editPlan.captions_enabled !== false,
          caption_phrases: next.captionPhrases,
          caption_style: normalizeCaptionStyle(next.editPlan.caption_style),
        });
      }
      setPhrases(next.captionPhrases || []);
    }
    return next;
  }, [videoId]);

  useEffect(() => {
    load().catch((e) => toast((e as Error).message, "err"));
  }, [load]);

  const processing = data && !["READY", "FAILED", "DISCOVERED"].includes(data.status);

  useEffect(() => {
    if (!processing) return;
    const t = window.setInterval(() => {
      load({ silent: true }).catch(() => undefined);
    }, 2000);
    return () => window.clearInterval(t);
  }, [processing, load]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code === "Space" && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault();
        setPlaying((p) => !p);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function exportVideo() {
    if (!plan) return;
    setExporting(true);
    try {
      const withCaptions = {
        ...plan,
        caption_phrases: phrases,
        captions_enabled: plan.captions_enabled !== false,
        caption_style: serializeCaptionStyle(plan.caption_style),
      };
      setPlan(withCaptions);
      await api(`/api/videos/${videoId}/edit-plan`, {
        method: "PUT",
        body: JSON.stringify({ plan: withCaptions }),
      });
      const next = await api<Video>(`/api/videos/${videoId}/render`, {
        method: "POST",
        body: JSON.stringify({ plan: withCaptions }),
      });
      setData((d) => (d ? { ...d, ...next, editPlan: (next.editPlan && 'video_summary' in next.editPlan) ? next.editPlan as EditPlan : null } : d));
      toast("Export started — captions will be burned into the MP4");
    } catch (e) {
      toast((e as Error).message, "err");
    } finally {
      setExporting(false);
    }
  }

  if (!data) {
    return <div className="flex h-screen items-center justify-center bg-[#0e1014] text-white/50">Loading editor…</div>;
  }
  if (!plan) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-[#0e1014] text-white/70">
        <p>Process this video first so the AI can assemble B-roll, music, and captions.</p>
        <Link href={`/projects/${projectId}/videos/${videoId}`} className="text-accent">
          Back to video
        </Link>
      </div>
    );
  }

  const duration = data.duration || 1;
  const active = activeBrollAt(plan, data.brollAssets || [], time);

  return (
    <div className="flex h-screen min-h-0 flex-col overflow-hidden bg-[#0e1014] text-white">
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-white/10 px-3">
        <div className="flex items-center gap-3">
          <Link href={`/projects/${projectId}/videos/${videoId}`} className="text-sm text-white/60 hover:text-white">
            Back
          </Link>
          <div className="text-sm font-medium">{data.filename}</div>
          {processing && (
            <span className="text-xs text-accent">
              {data.currentStage || "Exporting…"} <SmoothPercent progress={data.progress || 0} status={data.status} />
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={() => setPlaying((p) => !p)}>
            {playing ? "Pause" : "Play"}
          </Button>
          <Button disabled={exporting || !!processing} onClick={exportVideo}>
            {exporting ? "Saving…" : "Export / save"}
          </Button>
          {data.status === "READY" && (
            <a href={`${API_URL}/api/videos/${videoId}/download?t=${Date.now()}`}>
              <Button variant="secondary">Download video</Button>
            </a>
          )}
        </div>
      </header>
      <div className="grid min-h-0 flex-1 grid-cols-[220px_minmax(0,1fr)_300px] overflow-hidden">
        <div className="min-h-0 overflow-hidden">
          <MediaBin filename={data.filename} sourceUrl={data.sourceUrl} assets={data.brollAssets || []} musicUrl={data.musicUrl} />
        </div>
        <div className="flex min-h-0 items-center justify-center overflow-hidden bg-[#0a0c10] p-4">
          <PreviewStage
            sourceUrl={data.sourceUrl}
            musicUrl={data.musicUrl}
            time={time}
            playing={playing}
            duration={duration}
            captionsEnabled={plan.captions_enabled !== false}
            phrases={phrases}
            captionStyle={plan.caption_style}
            musicVolume={plan.music_volume ?? 0.18}
            activeBroll={active}
            onTime={setTime}
            onEnded={() => setPlaying(false)}
            mediaRef={mediaRef}
          />
        </div>
        <div className="min-h-0 overflow-hidden">
          <Inspector
            selection={selection}
            plan={plan}
            phrases={phrases}
            duration={duration}
            onPlan={setPlan}
            onPhrases={setPhrases}
          />
        </div>
      </div>
      <div className="relative z-10 h-48 shrink-0 border-t border-white/10">
        <EditorTimeline
          duration={duration}
          time={time}
          plan={plan}
          phrases={plan.captions_enabled === false ? [] : phrases}
          assets={data.brollAssets || []}
          selection={selection}
          onSeek={(t) => {
            setTime(t);
            if (mediaRef.current) mediaRef.current.currentTime = t;
          }}
          onSelect={setSelection}
          onMoveBroll={(index, start, end) => {
            setPlan({
              ...plan,
              segments: plan.segments.map((s, i) => (i === index ? { ...s, start, end } : s)),
            });
          }}
        />
      </div>
    </div>
  );
}
