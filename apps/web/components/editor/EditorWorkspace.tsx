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
import { normalizeCaptionStyle } from "./captionStyle";

export function EditorWorkspace({ projectId, videoId }: { projectId: string; videoId: string }) {
  const [data, setData] = useState<EditorPayload | null>(null);
  const [plan, setPlan] = useState<EditPlan | null>(null);
  const [phrases, setPhrases] = useState<CaptionPhrase[]>([]);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [exporting, setExporting] = useState(false);
  const mediaRef = useRef<HTMLVideoElement | null>(null);

  const load = useCallback(async () => {
    const next = await api<EditorPayload>(`/api/videos/${videoId}/editor`);
    setData(next);
    if (next.editPlan) {
      setPlan({
        ...next.editPlan,
        captions_enabled: next.editPlan.captions_enabled !== false,
        caption_phrases: next.captionPhrases,
        caption_style: normalizeCaptionStyle(next.editPlan.caption_style),
      });
    }
    setPhrases(next.captionPhrases || []);
    return next;
  }, [videoId]);

  useEffect(() => {
    load().catch((e) => toast((e as Error).message, "err"));
  }, [load]);

  const processing = data && !["READY", "FAILED", "DISCOVERED"].includes(data.status);

  useEffect(() => {
    if (!processing) return;
    const t = window.setInterval(() => {
      load().catch(() => undefined);
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

  async function savePlan(nextPlan: EditPlan) {
    const withCaptions = {
      ...nextPlan,
      caption_phrases: phrases,
      captions_enabled: nextPlan.captions_enabled !== false,
      caption_style: normalizeCaptionStyle(nextPlan.caption_style),
    };
    await api(`/api/videos/${videoId}/edit-plan`, { method: "PUT", body: JSON.stringify({ plan: withCaptions }) });
    setPlan(withCaptions);
  }

  async function exportVideo() {
    if (!plan) return;
    setExporting(true);
    try {
      await savePlan(plan);
      const next = await api<Video>(`/api/videos/${videoId}/render`, { method: "POST" });
      setData((d) => (d ? { ...d, ...next } : d));
      toast("Export started");
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
    <div className="flex h-screen flex-col bg-[#0e1014] text-white">
      <header className="flex h-12 items-center justify-between border-b border-white/10 px-3">
        <div className="flex items-center gap-3">
          <Link href={`/projects/${projectId}/videos/${videoId}`} className="text-sm text-white/60 hover:text-white">
            Back
          </Link>
          <div className="text-sm font-medium">{data.filename}</div>
          {processing && <span className="text-xs text-accent">{data.currentStage || "Exporting…"} {data.progress}%</span>}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={() => setPlaying((p) => !p)}>
            {playing ? "Pause" : "Play"}
          </Button>
          <Button disabled={exporting || !!processing} onClick={exportVideo}>
            {exporting ? "Saving…" : "Export / save"}
          </Button>
          {data.status === "READY" && (
            <a href={`${API_URL}/api/videos/${videoId}/download`}>
              <Button variant="secondary">Download video</Button>
            </a>
          )}
        </div>
      </header>
      <div className="grid min-h-0 flex-1 grid-cols-[220px_minmax(0,1fr)_300px]">
        <MediaBin filename={data.filename} sourceUrl={data.sourceUrl} assets={data.brollAssets || []} musicUrl={data.musicUrl} />
        <div className="flex min-h-0 items-center justify-center bg-[#0a0c10] p-4">
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
        <Inspector
          selection={selection}
          plan={plan}
          phrases={phrases}
          duration={duration}
          onPlan={setPlan}
          onPhrases={setPhrases}
        />
      </div>
      <div className="h-48 border-t border-white/10">
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
