"use client";

import { useEffect, useRef, type MutableRefObject } from "react";
import { API_URL, type BrollAsset, type CaptionPhrase, type EditSegment } from "@/lib/api";
import { CaptionPill } from "./CaptionPill";
import { pickCaptionPhrase, type CaptionStyle } from "./captionStyle";

export function PreviewStage({
  sourceUrl,
  musicUrl,
  time,
  playing,
  duration,
  captionsEnabled,
  phrases,
  captionStyle,
  musicVolume,
  activeBroll,
  onTime,
  onEnded,
  mediaRef,
}: {
  sourceUrl: string;
  musicUrl: string | null;
  time: number;
  playing: boolean;
  duration: number;
  captionsEnabled: boolean;
  phrases: CaptionPhrase[];
  captionStyle?: Partial<CaptionStyle> | null;
  musicVolume: number;
  activeBroll: { segment: EditSegment; asset: BrollAsset } | null;
  onTime: (t: number) => void;
  onEnded: () => void;
  mediaRef: MutableRefObject<HTMLVideoElement | null>;
}) {
  const overlayRef = useRef<HTMLVideoElement | null>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const musicRef = useRef<HTMLAudioElement | null>(null);
  const phrase = captionsEnabled ? pickCaptionPhrase(phrases, time) : null;

  useEffect(() => {
    const el = mediaRef.current;
    if (!el) return;
    if (playing) el.play().catch(() => undefined);
    else el.pause();
  }, [playing, mediaRef]);

  useEffect(() => {
    const music = musicRef.current;
    if (!music) return;
    music.volume = Math.max(0, Math.min(1, musicVolume));
    if (playing) music.play().catch(() => undefined);
    else music.pause();
  }, [playing, musicVolume]);

  useEffect(() => {
    const music = musicRef.current;
    if (!music || Math.abs(music.currentTime - time) < 0.5) return;
    music.currentTime = Math.min(time, music.duration || time);
  }, [time]);

  useEffect(() => {
    const ov = overlayRef.current;
    if (!ov || !activeBroll || activeBroll.asset.assetType === "image") return;
    const local = Math.max(0, time - activeBroll.segment.start);
    if (Math.abs(ov.currentTime - local) > 0.35) ov.currentTime = local;
    if (playing) ov.play().catch(() => undefined);
    else ov.pause();
  }, [activeBroll, playing, time]);

  return (
    <div className="relative mx-auto aspect-[9/16] h-full max-h-full w-auto overflow-hidden rounded-md bg-black shadow-[0_0_0_1px_rgba(255,255,255,0.08)] [container-type:inline-size]">
      <video
        ref={(n) => {
          mediaRef.current = n;
        }}
        className="h-full w-full object-cover"
        src={`${API_URL}${sourceUrl}`}
        playsInline
        onTimeUpdate={(e) => onTime(e.currentTarget.currentTime)}
        onEnded={onEnded}
      />
      {activeBroll && activeBroll.asset.assetType === "image" && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          ref={imgRef}
          src={`${API_URL}${activeBroll.asset.url}`}
          alt=""
          className="absolute inset-0 h-full w-full object-cover"
        />
      )}
      {activeBroll && activeBroll.asset.assetType !== "image" && (
        <video
          ref={overlayRef}
          key={activeBroll.asset.id}
          className="absolute inset-0 h-full w-full object-cover"
          src={`${API_URL}${activeBroll.asset.url}`}
          muted
          playsInline
          loop
        />
      )}
      <CaptionPill phrase={phrase} time={time} style={captionStyle} />
      {musicUrl && <audio ref={musicRef} src={`${API_URL}${musicUrl}`} loop />}
      <div className="pointer-events-none absolute bottom-2 right-2 rounded bg-black/60 px-1.5 py-0.5 text-[10px] tabular-nums text-white/80">
        {fmt(time)} / {fmt(duration)}
      </div>
    </div>
  );
}

function fmt(t: number) {
  const s = Math.max(0, t);
  const m = Math.floor(s / 60);
  const r = Math.floor(s % 60);
  const ms = Math.floor((s % 1) * 10);
  return `${m}:${r.toString().padStart(2, "0")}.${ms}`;
}
