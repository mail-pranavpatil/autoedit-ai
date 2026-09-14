"use client";

import { API_URL, type BrollAsset } from "@/lib/api";

export function MediaBin({
  filename,
  sourceUrl,
  assets,
  musicUrl,
}: {
  filename: string;
  sourceUrl: string;
  assets: BrollAsset[];
  musicUrl: string | null;
}) {
  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden border-r border-line bg-panel">
      <div className="border-b border-line px-3 py-2 text-xs uppercase tracking-wide text-white/40">Media</div>
      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        <div>
          <div className="mb-1 text-[11px] text-white/40">A-roll</div>
          <div className="overflow-hidden rounded-lg bg-black">
            <video src={`${API_URL}${sourceUrl}`} muted className="aspect-[9/16] max-h-36 w-full object-cover" />
            <div className="truncate px-2 py-1 text-[11px]">{filename}</div>
          </div>
        </div>
        <div>
          <div className="mb-1 text-[11px] text-white/40">B-roll</div>
          <div className="grid grid-cols-2 gap-2">
            {assets.map((a) => (
              <div key={a.id} className="overflow-hidden rounded-lg bg-black">
                {a.assetType === "image" ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={`${API_URL}${a.url}`} alt="" className="aspect-[9/16] max-h-28 w-full object-cover" />
                ) : (
                  <video src={`${API_URL}${a.url}`} muted className="aspect-[9/16] max-h-28 w-full object-cover" />
                )}
                <div className="truncate px-1.5 py-1 text-[10px] text-white/70">{a.query}</div>
              </div>
            ))}
            {assets.length === 0 && <p className="col-span-2 text-xs text-white/40">No B-roll yet</p>}
          </div>
        </div>
        {musicUrl && (
          <div>
            <div className="mb-1 text-[11px] text-white/40">Music</div>
            <audio controls src={`${API_URL}${musicUrl}`} className="w-full" />
          </div>
        )}
      </div>
    </aside>
  );
}
