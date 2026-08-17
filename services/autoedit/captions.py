from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from autoedit.edit_schema import POSITION_Y, CaptionStyle
from autoedit.media import run_ffmpeg

logger = logging.getLogger("autoedit")

CANVAS_W = 1080
CANVAS_H = 1920
WORDS_PER_PHRASE = 5

FONT_CANDIDATES = {
    "serif": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
        Path("/Library/Fonts/Georgia.ttf"),
        Path("/System/Library/Fonts/Supplemental/Georgia.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ],
    "sans": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ],
    "mono": [
        Path("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
        Path("/System/Library/Fonts/Menlo.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ],
}


def _parse_word(item: object) -> dict | None:
    if isinstance(item, dict):
        text = str(item.get("word") or item.get("text") or "").strip()
        if not text:
            return None
        return {
            "text": text,
            "start": float(item.get("start") or 0),
            "end": float(item.get("end") or item.get("start") or 0),
        }
    text = str(getattr(item, "word", None) or getattr(item, "text", "") or "").strip()
    if not text:
        return None
    return {
        "text": text,
        "start": float(getattr(item, "start", 0) or 0),
        "end": float(getattr(item, "end", 0) or getattr(item, "start", 0) or 0),
    }


def words_from_segments(segments: list | None) -> list[dict]:
    words: list[dict] = []
    for seg in segments or []:
        if not isinstance(seg, dict):
            continue
        raw_words = seg.get("words") or []
        parsed = [w for w in (_parse_word(item) for item in raw_words) if w]
        if parsed:
            words.extend(parsed)
            continue
        text = str(seg.get("text") or "").strip()
        parts = text.split()
        if not parts:
            continue
        start = float(seg.get("start") or 0)
        end = float(seg.get("end") or start)
        step = max((end - start) / len(parts), 0.04)
        for i, part in enumerate(parts):
            words.append(
                {
                    "text": part,
                    "start": start + i * step,
                    "end": start + (i + 1) * step,
                }
            )
    return words


def group_phrases(words: list[dict], size: int = WORDS_PER_PHRASE) -> list[dict]:
    phrases: list[dict] = []
    chunk_size = max(2, min(8, size))
    for i in range(0, len(words), chunk_size):
        chunk = words[i : i + chunk_size]
        if not chunk:
            continue
        phrases.append(
            {
                "start": float(chunk[0]["start"]),
                "end": float(chunk[-1]["end"]),
                "words": chunk,
            }
        )
    return phrases


def phrases_from_plan_or_transcript(
    plan_phrases: list | None,
    segments: list | None,
    words_per_line: int | None = None,
) -> list[dict]:
    if plan_phrases:
        out = []
        for ph in plan_phrases:
            if isinstance(ph, dict):
                words = ph.get("words") or []
                parsed = [w for w in (_parse_word(item) for item in words) if w]
            else:
                parsed = [w for w in (_parse_word(item) for item in getattr(ph, "words", []) or []) if w]
            if not parsed:
                continue
            out.append(
                {
                    "start": float(ph["start"] if isinstance(ph, dict) else ph.start),
                    "end": float(ph["end"] if isinstance(ph, dict) else ph.end),
                    "words": parsed,
                }
            )
        if out:
            return out
    return group_phrases(words_from_segments(segments), size=words_per_line or WORDS_PER_PHRASE)


def caption_states(phrases: list[dict]) -> list[dict]:
    states: list[dict] = []
    for ph in phrases:
        words = ph.get("words") or []
        if not words:
            continue
        for i, word in enumerate(words):
            end = float(word["end"])
            if i == len(words) - 1:
                end = float(ph["end"])
            states.append(
                {
                    "start": float(word["start"]),
                    "end": max(end, float(word["start"]) + 0.05),
                    "texts": [str(w["text"]) for w in words],
                    "active": i,
                }
            )
    return states


def resolve_style(style: CaptionStyle | dict | None) -> CaptionStyle:
    if isinstance(style, CaptionStyle):
        return style
    if isinstance(style, dict):
        return CaptionStyle.model_validate(style)
    return CaptionStyle()


def hex_to_rgba(color: str, alpha: float = 1.0) -> tuple[int, int, int, int]:
    c = color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (r, g, b, max(0, min(255, int(alpha * 255))))


def find_font(family: str = "serif", size: int = 54) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES.get(family, FONT_CANDIDATES["serif"]):
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    for group in FONT_CANDIDATES.values():
        for path in group:
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size=size)
                except OSError:
                    continue
    logger.warning("No caption TTF found; using Pillow default")
    return ImageFont.load_default()


def find_serif_font(size: int = 54) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return find_font("serif", size)


def _text_width(font: ImageFont.ImageFont, text: str) -> int:
    if hasattr(font, "getlength"):
        return int(font.getlength(text))
    bbox = font.getbbox(text)
    return int(bbox[2] - bbox[0])


def style_y_percent(style: CaptionStyle) -> float:
    if style.y_percent is not None:
        return float(style.y_percent)
    return POSITION_Y.get(style.position, 62.0)


def render_pill_png(
    path: Path,
    texts: list[str],
    active: int,
    font: ImageFont.ImageFont | None = None,
    style: CaptionStyle | dict | None = None,
) -> None:
    st = resolve_style(style)
    display = [t.upper() if st.uppercase else t for t in texts]
    font = font or find_font(st.font, st.size)
    gap = max(8, int(st.size * 0.28))
    pad_x = max(16, int(st.size * 0.55))
    pad_y = max(8, int(st.size * 0.28))
    widths = [_text_width(font, t) for t in display]
    content_w = sum(widths) + gap * max(0, len(display) - 1)
    sample_h = font.getbbox("Hg")[3] - font.getbbox("Hg")[1] if hasattr(font, "getbbox") else int(st.size * 0.8)
    box_w = content_w + pad_x * 2
    box_h = sample_h + pad_y * 2
    radius = box_h // 2 if st.background == "pill" else max(8, box_h // 6)
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    y0 = int(CANVAS_H * (style_y_percent(st) / 100.0))
    if st.align == "left":
        x0 = 48
    elif st.align == "right":
        x0 = max(24, CANVAS_W - box_w - 48)
    else:
        x0 = max(24, (CANVAS_W - box_w) // 2)
    x1 = min(CANVAS_W - 24, x0 + box_w)
    y1 = min(CANVAS_H - 24, y0 + box_h)
    if st.background != "none" and st.background_opacity > 0:
        fill = hex_to_rgba(st.background_color, st.background_opacity)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=fill)
    cursor = x0 + pad_x
    baseline = y0 + pad_y - (font.getbbox("A")[1] if hasattr(font, "getbbox") else 0)
    active_rgba = hex_to_rgba(st.active_color)
    muted_rgba = hex_to_rgba(st.muted_color)
    stroke = hex_to_rgba(st.stroke_color)
    for i, text in enumerate(display):
        color = active_rgba if (st.highlight == "none" or i == active) else muted_rgba
        kwargs: dict = {"font": font, "fill": color}
        if st.stroke_width:
            kwargs["stroke_width"] = st.stroke_width
            kwargs["stroke_fill"] = stroke
        draw.text((cursor, baseline), text, **kwargs)
        cursor += widths[i] + gap
    if st.shadow:
        shadow = layer.filter(ImageFilter.GaussianBlur(radius=4))
        canvas.alpha_composite(shadow)
    canvas.alpha_composite(layer)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, "PNG")


def render_blank_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0)).save(path, "PNG")


def build_caption_overlay_video(
    phrases: list[dict],
    out_dir: Path,
    duration: float,
    enabled: bool = True,
    style: CaptionStyle | dict | None = None,
) -> str | None:
    if not enabled:
        return None
    st = resolve_style(style)
    states = caption_states(phrases)
    if not states:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    font = find_font(st.font, st.size)
    blank = out_dir / "blank.png"
    render_blank_png(blank)
    files: list[tuple[float, Path]] = []
    t = 0.0
    duration = max(duration, 0.5)
    for i, state in enumerate(states):
        start = max(0.0, float(state["start"]))
        end = min(duration, float(state["end"]))
        if start > t + 0.02:
            files.append((start - t, blank))
        png = out_dir / f"cap_{i:04d}.png"
        render_pill_png(png, state["texts"], int(state["active"]), font, st)
        files.append((max(end - start, 0.05), png))
        t = end
    if t < duration - 0.02:
        files.append((duration - t, blank))
    if not files:
        return None
    concat = out_dir / "concat.txt"
    lines = []
    for dur, png in files:
        escaped = str(png.resolve()).replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"file '{escaped}'")
        lines.append(f"duration {dur:.4f}")
    last = files[-1][1]
    escaped = str(last.resolve()).replace("\\", "\\\\").replace("'", "\\'")
    lines.append(f"file '{escaped}'")
    concat.write_text("\n".join(lines) + "\n")
    overlay = out_dir / "captions.mov"
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-vsync",
            "vfr",
            "-c:v",
            "png",
            "-pix_fmt",
            "rgba",
            "-an",
            str(overlay),
        ],
        timeout=300,
    )
    return str(overlay)
