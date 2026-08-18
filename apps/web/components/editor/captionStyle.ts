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

export const POSITION_Y: Record<CaptionStyle["position"], number> = {
  top: 12,
  center: 46,
  lower: 62,
  bottom: 82,
};

export const CAPTION_PRESETS: Record<CaptionStyle["preset"], Omit<CaptionStyle, "preset" | "y_percent">> = {
  classic: {
    font: "serif",
    size: 54,
    position: "lower",
    active_color: "#FFFFFF",
    muted_color: "#B8B8B8",
    background: "pill",
    background_color: "#000000",
    background_opacity: 0.95,
    stroke_width: 0,
    stroke_color: "#000000",
    uppercase: false,
    words_per_line: 5,
    highlight: "word",
    shadow: false,
    align: "center",
  },
  hormozi: {
    font: "sans",
    size: 64,
    position: "lower",
    active_color: "#FFE500",
    muted_color: "#FFFFFF",
    background: "box",
    background_color: "#000000",
    background_opacity: 0.92,
    stroke_width: 0,
    stroke_color: "#000000",
    uppercase: true,
    words_per_line: 4,
    highlight: "word",
    shadow: false,
    align: "center",
  },
  bold: {
    font: "sans",
    size: 72,
    position: "lower",
    active_color: "#FFFFFF",
    muted_color: "#D1D5DB",
    background: "none",
    background_color: "#000000",
    background_opacity: 0,
    stroke_width: 6,
    stroke_color: "#000000",
    uppercase: true,
    words_per_line: 4,
    highlight: "word",
    shadow: true,
    align: "center",
  },
  minimal: {
    font: "serif",
    size: 40,
    position: "bottom",
    active_color: "#FFFFFF",
    muted_color: "#FFFFFF",
    background: "none",
    background_color: "#000000",
    background_opacity: 0,
    stroke_width: 3,
    stroke_color: "#000000",
    uppercase: false,
    words_per_line: 6,
    highlight: "none",
    shadow: false,
    align: "center",
  },
  neon: {
    font: "sans",
    size: 56,
    position: "lower",
    active_color: "#5CFF9F",
    muted_color: "#9CA3AF",
    background: "pill",
    background_color: "#111827",
    background_opacity: 0.9,
    stroke_width: 0,
    stroke_color: "#000000",
    uppercase: false,
    words_per_line: 5,
    highlight: "word",
    shadow: true,
    align: "center",
  },
  subtitle: {
    font: "sans",
    size: 32,
    position: "bottom",
    active_color: "#FFFFFF",
    muted_color: "#E5E7EB",
    background: "none",
    background_color: "#000000",
    background_opacity: 0,
    stroke_width: 2,
    stroke_color: "#000000",
    uppercase: false,
    words_per_line: 8,
    highlight: "none",
    shadow: false,
    align: "center",
  },
};

export const DEFAULT_CAPTION_STYLE: CaptionStyle = { preset: "classic", ...CAPTION_PRESETS.classic };

export function normalizeCaptionStyle(raw?: Partial<CaptionStyle> | null): CaptionStyle {
  return { ...DEFAULT_CAPTION_STYLE, ...(raw || {}) };
}

export function applyCaptionPreset(name: CaptionStyle["preset"]): CaptionStyle {
  return { preset: name, ...CAPTION_PRESETS[name], y_percent: null };
}

export function serializeCaptionStyle(raw?: Partial<CaptionStyle> | null): CaptionStyle {
  const style = normalizeCaptionStyle(raw);
  if (style.y_percent == null) {
    const { y_percent: _ignored, ...rest } = style;
    return rest as CaptionStyle;
  }
  return style;
}

export function captionY(style: CaptionStyle) {
  return style.y_percent ?? POSITION_Y[style.position] ?? 62;
}

export function toColorInput(hex: string | undefined, fallback = "#ffffff") {
  const v = (hex || fallback).trim();
  if (/^#[0-9a-fA-F]{6}$/.test(v)) return v.toLowerCase();
  if (/^#[0-9a-fA-F]{3}$/.test(v)) {
    return `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`.toLowerCase();
  }
  return fallback;
}

export function pickCaptionPhrase<T extends { start: number; end: number }>(phrases: T[], time: number): T | null {
  if (!phrases.length) return null;
  const current = phrases.find((p) => time >= p.start && time < p.end);
  if (current) return current;
  const upcoming = phrases.find((p) => p.start > time);
  return upcoming || phrases[phrases.length - 1];
}
