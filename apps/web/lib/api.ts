// Default "" = same-origin: every request becomes a relative /api/... path that
// next.config.js proxies to the FastAPI service (keeps the session cookie
// same-site). Set NEXT_PUBLIC_API_URL only to point the browser at a different
// API host directly (cross-origin).
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

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
  thumbnailUrl?: string | null;
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
  outputUnavailable?: boolean;
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

export function formatRelativeTime(iso?: string | null) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const diffMin = Math.round((Date.now() - date.getTime()) / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(date);
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

import { MOCK_PROJECTS, MOCK_VIDEOS } from "./mockData";

export function isDemoMode() {
  return typeof window !== "undefined" && localStorage.getItem("eren_demo_mode") === "true";
}

function handleMockApi<T>(path: string, init: RequestInit = {}): T | null {
  if (!isDemoMode()) return null;
  if (path === "/api/auth/me") {
    return { id: "demo-1", email: "creator@eren.ai", name: "Eren Creator", driveConnected: true } as T;
  }
  if (path === "/api/auth/logout") {
    localStorage.removeItem("eren_demo_mode");
    return {} as T;
  }
  if (path === "/api/projects" && (!init.method || init.method === "GET")) {
    return MOCK_PROJECTS as T;
  }
  if (path.startsWith("/api/projects/") && path.endsWith("/progress")) {
    return { ...MOCK_PROJECTS[0], videos: MOCK_VIDEOS } as T;
  }
  if (path.startsWith("/api/projects/") && (!init.method || init.method === "GET")) {
    return { ...MOCK_PROJECTS[0], videos: MOCK_VIDEOS } as T;
  }
  if (path.startsWith("/api/videos/")) {
    return MOCK_VIDEOS[0] as T;
  }
  if (path === "/api/settings") {
    return { googleConnected: true, youtubeConnected: false, youtubeAutoUpload: false } as T;
  }
  if (path === "/api/system") {
    return { healthy: true, latencyMs: 8, version: "0.1.0" } as T;
  }
  if (path === "/api/assets") {
    return [
      { id: "asset-1", name: "Upbeat Lo-fi Groove", assetType: "music", url: "" },
      { id: "asset-2", name: "Whoosh Accent", assetType: "sfx", url: "" },
    ] as T;
  }
  if (path === "/api/style") {
    return {
      preset: "classic",
      font: "sans",
      size: 28,
      position: "lower",
    } as T;
  }
  return {} as T;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const mock = handleMockApi<T>(path, init);
  if (mock !== null) return mock;

  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
      credentials: "include",
    });
  } catch (err) {
    if (isDemoMode()) {
      return (handleMockApi<T>(path, init) ?? ({} as T));
    }
    throw err;
  }
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
