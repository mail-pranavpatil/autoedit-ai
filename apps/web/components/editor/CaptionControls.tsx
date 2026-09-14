"use client";

import type { CaptionPhrase, EditPlan } from "@/lib/api";
import { applyCaptionPreset, normalizeCaptionStyle, type CaptionStyle } from "./captionStyle";
import { CaptionPresetPicker, CaptionStyleFields } from "./CaptionStyleFields";

export function CaptionControls({
  plan,
  phrases,
  onPlan,
  onPhrases,
}: {
  plan: EditPlan;
  phrases: CaptionPhrase[];
  onPlan: (p: EditPlan) => void;
  onPhrases: (p: CaptionPhrase[]) => void;
}) {
  const style = normalizeCaptionStyle(plan.caption_style);

  function patch(partial: Partial<CaptionStyle>) {
    onPlan({ ...plan, caption_style: { ...style, ...partial } });
  }

  function regroup(n: number, nextStyle?: CaptionStyle) {
    const words = phrases.flatMap((p) => p.words);
    const grouped: CaptionPhrase[] = [];
    for (let i = 0; i < words.length; i += n) {
      const chunk = words.slice(i, i + n);
      if (!chunk.length) continue;
      grouped.push({ start: chunk[0].start, end: chunk[chunk.length - 1].end, words: chunk });
    }
    if (grouped.length) onPhrases(grouped);
    if (nextStyle) onPlan({ ...plan, caption_style: nextStyle, captions_enabled: true });
    else patch({ words_per_line: n });
  }

  return (
    <div className="mt-6 space-y-3 border-t border-white/10 pt-4">
      <div className="text-xs uppercase tracking-wide text-white/40">Captions</div>
      <label className="flex items-center gap-2 text-white/80">
        <input
          type="checkbox"
          checked={plan.captions_enabled !== false}
          onChange={(e) => onPlan({ ...plan, captions_enabled: e.target.checked })}
        />
        Show captions
      </label>
      <CaptionPresetPicker
        style={style}
        onSelect={(id) => {
          const next = applyCaptionPreset(id);
          regroup(next.words_per_line, next);
        }}
      />
      <CaptionStyleFields style={style} onChange={patch} onWordsPerLine={(n) => regroup(n)} />
    </div>
  );
}
