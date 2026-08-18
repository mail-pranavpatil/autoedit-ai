"use client";

import type { CaptionPhrase } from "@/lib/api";
import { captionY, normalizeCaptionStyle, toColorInput, type CaptionStyle } from "./captionStyle";

const FONTS: Record<CaptionStyle["font"], string> = {
  serif: 'Georgia, "Liberation Serif", "Times New Roman", Times, serif',
  sans: 'Inter, "Liberation Sans", Arial, Helvetica, sans-serif',
  mono: '"Liberation Mono", Menlo, Monaco, monospace',
};

export function CaptionPill({
  phrase,
  time,
  style,
}: {
  phrase: CaptionPhrase | null;
  time: number;
  style?: Partial<CaptionStyle> | null;
}) {
  if (!phrase) return null;
  const st = normalizeCaptionStyle(style);
  let active = 0;
  phrase.words.forEach((w, i) => {
    if (time >= w.start) active = i;
  });
  if (time < phrase.words[0]?.start) active = 0;
  const radius = st.background === "pill" ? 999 : st.background === "box" ? 10 : 0;
  const bg = st.background === "none" ? "transparent" : hexAlpha(st.background_color, st.background_opacity);
  const x = st.align === "left" ? "8%" : st.align === "right" ? "92%" : "50%";
  const tx = st.align === "left" ? "0" : st.align === "right" ? "-100%" : "-50%";
  const stroke = st.stroke_width > 0 ? `${Math.max(0.4, st.stroke_width * 0.35)}px ${st.stroke_color}` : "0px transparent";

  return (
    <div
      className="pointer-events-none absolute z-20 max-w-[92%] px-[0.85em] py-[0.4em] leading-none"
      style={{
        top: `${captionY(st)}%`,
        left: x,
        transform: `translate(${tx}, 0)`,
        fontFamily: FONTS[st.font],
        fontSize: `max(12px, calc(${st.size} / 1080 * 100cqw))`,
        background: bg,
        borderRadius: radius,
        boxShadow: st.shadow ? "0 8px 20px rgba(0,0,0,0.45)" : "none",
        whiteSpace: "nowrap",
      }}
    >
      {phrase.words.map((w, i) => {
        const on = st.highlight === "none" || i === active;
        const fill = on ? st.active_color : st.muted_color;
        const text = st.uppercase ? w.text.toUpperCase() : w.text;
        return (
          <span
            key={`${w.start}-${i}`}
            style={{
              color: fill,
              WebkitTextFillColor: fill,
              WebkitTextStroke: stroke,
              paintOrder: "stroke fill",
              marginRight: i === phrase.words.length - 1 ? 0 : "0.28em",
              fontWeight: on && st.highlight === "word" ? 800 : 600,
            }}
          >
            {text}
          </span>
        );
      })}
    </div>
  );
}

function hexAlpha(hex: string, a: number) {
  const h = toColorInput(hex, "#000000").slice(1);
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${a})`;
}
