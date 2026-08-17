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
  editPlan?: Record<string, unknown> | null;
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
