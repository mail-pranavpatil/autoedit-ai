export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Project = {
  id: string;
  name: string;
  totalVideos: number;
  readyVideos: number;
  processingVideos: number;
  failedVideos: number;
  queuedVideos: number;
  createdAt: string;
  updatedAt: string;
  videos?: Video[];
  active?: boolean;
};

export const TERMINAL_VIDEO_STATUSES = ["READY", "FAILED", "DISCOVERED"] as const;

export function isProcessingStatus(status?: string | null) {
  return Boolean(status) && !TERMINAL_VIDEO_STATUSES.includes(status as (typeof TERMINAL_VIDEO_STATUSES)[number]);
}

export function isYoutubePending(video?: Video | null) {
  const status = video?.youtube?.status;
  return status === "PENDING" || status === "UPLOADING";
}

export type YoutubeUpload = {
  id?: string;
  status: string;
  scheduledAt?: string | null;
  url?: string | null;
  error?: string | null;
  title?: string | null;
  filename?: string | null;
  videoId?: string | null;
  projectId?: string | null;
  projectName?: string | null;
};

export type Video = {
  id: string;
  filename: string;
  duration: number | null;
  width: number | null;
  height: number | null;
  status: string;
  progress: number;
  currentStage?: string | null;
  thumbnailUrl?: string | null;
  outputUrl?: string | null;
  errorMessage?: string | null;
  failedStage?: string | null;
  retryCount?: number;
  projectId?: string;
  transcript?: { language?: string; fullText?: string; segments?: unknown } | null;
  editPlan?: EditPlan | Record<string, unknown> | null;
  youtube?: YoutubeUpload | null;
};

export function formatIst(iso?: string | null) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export type CaptionWord = { text: string; start: number; end: number };
export type CaptionPhrase = { start: number; end: number; words: CaptionWord[] };

export type CaptionStyle = {
  preset: "classic" | "hormozi" | "bold" | "minimal" | "neon" | "subtitle";
  font: "serif" | "sans" | "mono";
  size: number;
  position: "top" | "center" | "lower" | "bottom";
  y_percent?: number | null;
  active_color: string;
  muted_color: string;
  background: "none" | "pill" | "box";
  background_color: string;
  background_opacity: number;
  stroke_width: number;
  stroke_color: string;
  uppercase: boolean;
  words_per_line: number;
  highlight: "word" | "none";
  shadow: boolean;
  align: "left" | "center" | "right";
};

export type EditSegment = {
  start: number;
  end: number;
  visual: "talking_head" | "broll";
  broll_query: string | null;
  broll_type: "video" | "image" | null;
  effect: string;
  sfx: string | null;
};

export type SfxEvent = {
  sfx_id: string;
  start: number;
  volume: number;
  kind: string;
  reason: string;
  confidence: number;
  duck_music: boolean;
};

export type EditPlan = {
  video_summary: string;
  tone: string;
  music_category: string;
  segments: EditSegment[];
  captions_enabled?: boolean;
  music_volume?: number | null;
  caption_phrases?: CaptionPhrase[] | null;
  caption_style?: CaptionStyle | null;
  sfx_events?: SfxEvent[];
};

export type BrollAsset = {
  id: string;
  query: string;
  assetType: string;
  url: string;
};

export type EditorPayload = Video & {
  projectId: string;
  captionPhrases: CaptionPhrase[];
  sourceUrl: string;
  musicUrl: string | null;
  outputReady: boolean;
  brollAssets: BrollAsset[];
  editPlan: EditPlan | null;
};

export type User = {
  id: string;
  email: string;
  name?: string | null;
  pictureUrl?: string | null;
  driveConnected: boolean;
};

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (res.status === 401 && typeof window !== "undefined" && !path.includes("/auth/me")) {
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      detail = await res.text();
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return undefined as T;
}

export function mediaUrl(path?: string | null) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_URL}${path}`;
}

export function formatDuration(seconds?: number | null) {
  if (!seconds) return "—";
  const s = Math.round(seconds);
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, "0")}`;
}
