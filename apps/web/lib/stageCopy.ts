export const PROCESS_STEPS = [
  { status: "QUEUED", title: "Queued", line: "Starting a new edit job…" },
  { status: "DOWNLOADING", title: "Download", line: "Pulling the original clip from Google Drive…" },
  { status: "DOWNLOADED", title: "Downloaded", line: "Got the source file." },
  { status: "PROBING", title: "Inspect", line: "Extracting duration, resolution, and audio…" },
  { status: "TRANSCRIBING", title: "Transcribe", line: "Listening to the talking-head audio and writing a timestamped transcript…" },
  { status: "TRANSCRIBED", title: "Transcript", line: "Transcript is ready." },
  { status: "PLANNING", title: "Thinking", line: "Thinking through B-roll, zooms, music, and sound design…" },
  { status: "PLAN_READY", title: "Edit plan", line: "Locked in a structured edit plan." },
  { status: "SEARCHING_BROLL", title: "Stock search", line: "Searching stock photos and clips that match the script…" },
  { status: "BROLL_READY", title: "Assets", line: "B-roll downloaded and ready to overlay." },
  { status: "RENDERING", title: "Render", line: "Compositing the 9:16 reel — overlays, captions, music, and SFX…" },
  { status: "RENDERED", title: "Written", line: "Finished writing the MP4." },
  { status: "VALIDATING", title: "Validate", line: "Checking resolution, codec, and audio…" },
  { status: "READY", title: "Done", line: "Your reel is ready to preview and download." },
] as const;

export const PROCESS_STEP_ORDER = PROCESS_STEPS.map((s) => s.status);

const STAGE_TITLE: Record<string, string> = Object.fromEntries(PROCESS_STEPS.map((s) => [s.status, s.title]));

/** Friendly title for a raw backend stage/status string (e.g. "SEARCHING_BROLL" -> "Stock search"). */
export function stageTitle(stage?: string | null): string {
  if (!stage) return "";
  return STAGE_TITLE[stage] || stage;
}
