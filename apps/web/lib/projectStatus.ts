import type { Project } from "./api";

export type ProjectStatus = "READY" | "PROCESSING" | "FAILED" | "DRAFT";

/** One representative status for a project's video mix, for the shared StatusBadge. */
export function projectStatus(p: Pick<Project, "totalVideos" | "readyVideos" | "processingVideos" | "failedVideos">): ProjectStatus {
  if (p.failedVideos > 0) return "FAILED";
  if (p.processingVideos > 0) return "PROCESSING";
  if (p.totalVideos > 0 && p.readyVideos === p.totalVideos) return "READY";
  return "DRAFT";
}
