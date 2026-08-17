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

export function applyCaptionPreset(name: CaptionStyle["preset"]): CaptionStyle {
  return { preset: name, ...CAPTION_PRESETS[name], y_percent: null };
}

export function normalizeCaptionStyle(raw?: Partial<CaptionStyle> | null): CaptionStyle {
  return { ...DEFAULT_CAPTION_STYLE, ...(raw || {}) };
}

export function captionY(style: CaptionStyle) {
  return style.y_percent ?? POSITION_Y[style.position] ?? 62;
}
