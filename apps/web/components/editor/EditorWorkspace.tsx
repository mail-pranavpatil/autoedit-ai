"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { clsx } from "clsx";
import { API_URL, api, type CaptionPhrase, type EditPlan, type EditorPayload, type Video } from "@/lib/api";
import { Button } from "@/components/common/Button";
import { toast } from "@/components/common/Toast";
import { Image, Type, Music2 } from "lucide-react";
import { Inspector } from "./Inspector";
import { MediaBin } from "./MediaBin";
import { EditorTimeline, activeBrollAt, type Selection } from "./EditorTimeline";
import { PreviewStage } from "./PreviewStage";
import { normalizeCaptionStyle, serializeCaptionStyle } from "./captionStyle";
import { SmoothPercent } from "@/lib/useSmoothProgress";
import { stageTitle } from "@/lib/stageCopy";

/** Below `lg` (phone width, where this runs full-time inside the Eren iOS
 * shell) MediaBin/Inspector don't fit as permanent side columns, so they
 * become bottom sheets opened from this tool strip instead. The compact
 * timeline stays visible always (it's already the secondary, below-the-fold
 * element the guide asks for) — no separate "Timeline" sheet needed. */
type MobilePanel = "media" | "inspector" | null;

export function EditorWorkspace({ projectId, videoId }: { projectId: string; videoId: string }) {
  const [data, setData] = useState<EditorPayload | null>(null);
  const [plan, setPlan] = useState<EditPlan | null>(null);
  const [phrases, setPhrases] = useState<CaptionPhrase[]>([]);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [exporting, setExporting] = useState(false);
  const [mobilePanel, setMobilePanel] = useState<MobilePanel>(null);
  const mediaRef = useRef<HTMLVideoElement | null>(null);

  function openVisuals() {
    setMobilePanel("media");
  }
  function openCaptions() {
    setSelection(null);
    setMobilePanel("inspector");
  }
  function openMusic() {
    setSelection({ type: "music" });
    setMobilePanel("inspector");
  }

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
    return <div className="flex h-screen items-center justify-center bg-ink text-white/50">Loading editor…</div>;
  }
  if (!plan) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-ink text-white/70">
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
    <div className="flex h-screen min-h-0 flex-col overflow-hidden bg-ink text-white">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-2">
        <div className="flex min-w-0 items-center gap-3">
          <Link href={`/projects/${projectId}/videos/${videoId}`} className="shrink-0 text-sm text-white/60 hover:text-white">
            Back
          </Link>
          <div className="truncate text-sm font-medium">{data.filename}</div>
          {processing && (
            <span className="shrink-0 text-xs text-accent">
              {stageTitle(data.currentStage) || "Exporting…"} <SmoothPercent progress={data.progress || 0} status={data.status} />
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

      <div className="grid min-h-0 flex-1 grid-cols-1 overflow-hidden lg:grid-cols-[220px_minmax(0,1fr)_300px]">
        <div
          className={clsx(
            "min-h-0 overflow-hidden lg:static lg:z-auto lg:block lg:h-auto lg:rounded-none lg:border-t-0",
            mobilePanel === "media"
              ? "fixed inset-x-0 bottom-0 z-40 h-[70vh] rounded-t-2xl border-t border-line"
              : "hidden"
          )}
        >
          <MediaBin filename={data.filename} sourceUrl={data.sourceUrl} assets={data.brollAssets || []} musicUrl={data.musicUrl} />
        </div>
        <div className="flex min-h-0 items-center justify-center overflow-hidden bg-ink p-4">
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
        <div
          className={clsx(
            "min-h-0 overflow-hidden lg:static lg:z-auto lg:block lg:h-auto lg:rounded-none lg:border-t-0",
            mobilePanel === "inspector"
              ? "fixed inset-x-0 bottom-0 z-40 h-[70vh] rounded-t-2xl border-t border-white/10"
              : "hidden"
          )}
        >
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

      {mobilePanel && (
        <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={() => setMobilePanel(null)} />
      )}

      <div className="flex shrink-0 border-t border-line lg:hidden">
        <ToolStripButton label="Visuals" icon={Image} active={mobilePanel === "media"} onClick={openVisuals} />
        <ToolStripButton label="Captions" icon={Type} active={mobilePanel === "inspector" && selection?.type !== "music"} onClick={openCaptions} />
        <ToolStripButton label="Music" icon={Music2} active={mobilePanel === "inspector" && selection?.type === "music"} onClick={openMusic} />
      </div>

      <div className="relative z-10 h-40 shrink-0 border-t border-line lg:h-48">
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
          onSelect={(s) => {
            setSelection(s);
            setMobilePanel("inspector");
          }}
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

function ToolStripButton({ label, icon: Icon, active, onClick }: { label: string; icon: React.ComponentType<{ className?: string }>; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-xs font-medium transition-colors duration-150",
        active ? "border-t-2 border-accent text-white" : "border-t-2 border-transparent text-white/50 hover:text-white/80"
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}
