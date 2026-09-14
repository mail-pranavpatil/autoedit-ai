import { clsx } from "clsx";

const colors: Record<string, string> = {
  READY: "bg-emerald-500/20 text-emerald-300",
  FAILED: "bg-red-500/20 text-red-300",
  QUEUED: "bg-sky-500/20 text-sky-300",
  DISCOVERED: "bg-white/10 text-muted",
  DOWNLOADED: "bg-white/10 text-muted",
  RENDERING: "bg-amber-500/20 text-amber-300",
  TRANSCRIBING: "bg-amber-500/20 text-amber-300",
  PLANNING: "bg-amber-500/20 text-amber-300",
  SEARCHING_BROLL: "bg-amber-500/20 text-amber-300",
  SCHEDULED: "bg-emerald-500/20 text-emerald-300",
  PENDING: "bg-sky-500/20 text-sky-300",
  UPLOADING: "bg-amber-500/20 text-amber-300",
  PROCESSING: "bg-amber-500/20 text-amber-300",
  DRAFT: "bg-white/10 text-muted",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx("rounded-full px-2.5 py-0.5 text-xs font-medium", colors[status] || "bg-amber-500/20 text-amber-200")}>
      {status.replaceAll("_", " ")}
    </span>
  );
}
