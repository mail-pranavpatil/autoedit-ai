"use client";

import type { CaptionPhrase } from "@/lib/api";
import { captionY, normalizeCaptionStyle, type CaptionStyle } from "./captionStyle";

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
  const radius = st.background === "pill" ? 999 : st.background === "box" ? 10 : 0;
  const bg =
    st.background === "none"
      ? "transparent"
      : hexAlpha(st.background_color, st.background_opacity);
  const align = st.align === "left" ? "flex-start" : st.align === "right" ? "flex-end" : "center";
  const x = st.align === "left" ? "8%" : st.align === "right" ? "92%" : "50%";
  const tx = st.align === "left" ? "0" : st.align === "right" ? "-100%" : "-50%";

  return (
    <div
      className="pointer-events-none absolute z-10 flex max-w-[92%] px-[0.85em] py-[0.38em] leading-none"
      style={{
        top: `${captionY(st)}%`,
        left: x,
        transform: `translate(${tx}, 0)`,
        justifyContent: align,
        fontFamily: FONTS[st.font],
        fontSize: `${(st.size / 1080) * 100}cqw`,
        background: bg,
        borderRadius: radius,
        boxShadow: st.shadow ? "0 6px 18px rgba(0,0,0,0.45)" : "none",
        WebkitTextStroke: st.stroke_width ? `${st.stroke_width * 0.35}px ${st.stroke_color}` : "0",
        paintOrder: "stroke fill",
      }}
    >
      {phrase.words.map((w, i) => {
        const on = st.highlight === "none" || i === active;
        const text = st.uppercase ? w.text.toUpperCase() : w.text;
        return (
          <span
            key={`${w.start}-${i}`}
            style={{
              color: on ? st.active_color : st.muted_color,
              marginRight: i === phrase.words.length - 1 ? 0 : "0.28em",
              fontWeight: on && st.highlight === "word" ? 700 : 600,
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
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${a})`;
}
