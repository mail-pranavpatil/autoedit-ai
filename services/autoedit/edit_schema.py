from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Effect = Literal[
    "none",
    "slow_zoom_in",
    "slow_zoom_out",
    "pan_left",
    "pan_right",
    "pan_up",
    "pan_down",
    "fade_in",
    "fade_out",
]

SfxName = Literal[
    "whoosh",
    "pop",
    "click",
    "camera_shutter",
    "notification",
    "ding",
    "swipe",
    "impact",
    "bubble",
    "cartoon",
]

MusicCategory = Literal["energetic", "technology", "cinematic", "motivational", "chill"]
Visual = Literal["talking_head", "broll"]
BrollType = Literal["video", "image"]

ALLOWED_EFFECTS = set(Effect.__args__)  # type: ignore[attr-defined]
ALLOWED_SFX = set(SfxName.__args__)  # type: ignore[attr-defined]
ALLOWED_MUSIC = set(MusicCategory.__args__)  # type: ignore[attr-defined]


class EditSegment(BaseModel):
    start: float
    end: float
    visual: Visual
    broll_query: str | None = None
    broll_type: BrollType | None = None
    effect: Effect = "none"
    sfx: SfxName | None = None

    @field_validator("broll_query", "broll_type", "sfx", mode="before")
    @classmethod
    def nullish_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip().lower() in {"null", "none", "nil", ""}:
            return None
        return v

    @field_validator("effect", mode="before")
    @classmethod
    def coerce_effect(cls, v):
        if v is None or (isinstance(v, str) and v.strip().lower() in {"null", "none", ""}):
            return "none"
        return v

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: float, info):
        start = info.data.get("start")
        if start is not None and v <= start:
            raise ValueError("segment end must be after start")
        return v

    @model_validator(mode="after")
    def normalize_visual(self):
        if self.visual == "broll":
            if not self.broll_query:
                object.__setattr__(self, "broll_query", "vertical lifestyle b-roll")
            if not self.broll_type:
                object.__setattr__(self, "broll_type", "video")
        else:
            object.__setattr__(self, "broll_query", None)
            object.__setattr__(self, "broll_type", None)
        return self


class CaptionWord(BaseModel):
    text: str
    start: float
    end: float


class CaptionPhrase(BaseModel):
    start: float
    end: float
    words: list[CaptionWord] = Field(min_length=1)


CaptionPreset = Literal["classic", "hormozi", "bold", "minimal", "neon", "subtitle"]
CaptionFont = Literal["serif", "sans", "mono"]
CaptionBackground = Literal["none", "pill", "box"]
CaptionPosition = Literal["top", "center", "lower", "bottom"]
CaptionHighlight = Literal["word", "none"]
CaptionAlign = Literal["left", "center", "right"]


def _hex_color(v: str) -> str:
    text = (v or "").strip()
    if len(text) == 4 and text.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in text[1:]):
        return f"#{text[1]*2}{text[2]*2}{text[3]*2}".upper()
    if len(text) == 7 and text.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in text[1:]):
        return text.upper()
    raise ValueError("color must be #RGB or #RRGGBB")


CAPTION_PRESETS: dict[str, dict] = {
    "classic": {
        "font": "serif",
        "size": 54,
        "position": "lower",
        "active_color": "#FFFFFF",
        "muted_color": "#B8B8B8",
        "background": "pill",
        "background_color": "#000000",
        "background_opacity": 0.95,
        "stroke_width": 0,
        "stroke_color": "#000000",
        "uppercase": False,
        "words_per_line": 5,
        "highlight": "word",
        "shadow": False,
        "align": "center",
    },
    "hormozi": {
        "font": "sans",
        "size": 64,
        "position": "lower",
        "active_color": "#FFE500",
        "muted_color": "#FFFFFF",
        "background": "box",
        "background_color": "#000000",
        "background_opacity": 0.92,
        "stroke_width": 0,
        "stroke_color": "#000000",
        "uppercase": True,
        "words_per_line": 4,
        "highlight": "word",
        "shadow": False,
        "align": "center",
    },
    "bold": {
        "font": "sans",
        "size": 72,
        "position": "lower",
        "active_color": "#FFFFFF",
        "muted_color": "#D1D5DB",
        "background": "none",
        "background_color": "#000000",
        "background_opacity": 0.0,
        "stroke_width": 6,
        "stroke_color": "#000000",
        "uppercase": True,
        "words_per_line": 4,
        "highlight": "word",
        "shadow": True,
        "align": "center",
    },
    "minimal": {
        "font": "serif",
        "size": 40,
        "position": "bottom",
        "active_color": "#FFFFFF",
        "muted_color": "#FFFFFF",
        "background": "none",
        "background_color": "#000000",
        "background_opacity": 0.0,
        "stroke_width": 3,
        "stroke_color": "#000000",
        "uppercase": False,
        "words_per_line": 6,
        "highlight": "none",
        "shadow": False,
        "align": "center",
    },
    "neon": {
        "font": "sans",
        "size": 56,
        "position": "lower",
        "active_color": "#5CFF9F",
        "muted_color": "#9CA3AF",
        "background": "pill",
        "background_color": "#111827",
        "background_opacity": 0.9,
        "stroke_width": 0,
        "stroke_color": "#000000",
        "uppercase": False,
        "words_per_line": 5,
        "highlight": "word",
        "shadow": True,
        "align": "center",
    },
    "subtitle": {
        "font": "sans",
        "size": 32,
        "position": "bottom",
        "active_color": "#FFFFFF",
        "muted_color": "#E5E7EB",
        "background": "none",
        "background_color": "#000000",
        "background_opacity": 0.0,
        "stroke_width": 2,
        "stroke_color": "#000000",
        "uppercase": False,
        "words_per_line": 8,
        "highlight": "none",
        "shadow": False,
        "align": "center",
    },
}


class CaptionStyle(BaseModel):
    preset: CaptionPreset = "classic"
    font: CaptionFont = "serif"
    size: int = Field(default=54, ge=24, le=96)
    position: CaptionPosition = "lower"
    y_percent: float | None = Field(default=None, ge=5, le=92)
    active_color: str = "#FFFFFF"
    muted_color: str = "#B8B8B8"
    background: CaptionBackground = "pill"
    background_color: str = "#000000"
    background_opacity: float = Field(default=0.95, ge=0, le=1)
    stroke_width: int = Field(default=0, ge=0, le=12)
    stroke_color: str = "#000000"
    uppercase: bool = False
    words_per_line: int = Field(default=5, ge=2, le=8)
    highlight: CaptionHighlight = "word"
    shadow: bool = False
    align: CaptionAlign = "center"

    @field_validator("active_color", "muted_color", "background_color", "stroke_color")
    @classmethod
    def valid_hex(cls, v: str) -> str:
        return _hex_color(v)


def caption_style_from_preset(name: str) -> CaptionStyle:
    key = name if name in CAPTION_PRESETS else "classic"
    return CaptionStyle(preset=key, **CAPTION_PRESETS[key])  # type: ignore[arg-type]


POSITION_Y = {"top": 12.0, "center": 46.0, "lower": 62.0, "bottom": 82.0}


class EditPlan(BaseModel):
    video_summary: str
    tone: str
    music_category: MusicCategory
    segments: list[EditSegment] = Field(min_length=1)
    captions_enabled: bool = True
    music_volume: float | None = None
    caption_phrases: list[CaptionPhrase] | None = None
    caption_style: CaptionStyle = Field(default_factory=CaptionStyle)

    @field_validator("segments")
    @classmethod
    def no_shell_or_paths(cls, segments: list[EditSegment]):
        for seg in segments:
            if seg.broll_query:
                lowered = seg.broll_query.lower()
                if any(tok in lowered for tok in [";", "&&", "|", "`", "$(", "../"]):
                    raise ValueError("broll_query contains disallowed characters")
        return segments


def plan_is_weak(plan: EditPlan) -> bool:
    broll = sum(1 for s in plan.segments if s.visual == "broll")
    return broll < 2


DEFAULT_STYLE_PROFILE = {
    "aspect_ratio": "9:16",
    "resolution": "1080x1920",
    "fps": 30,
    "broll_frequency": "medium",
    "broll_type": "both",
    "effects": {
        "zoom": True,
        "pan": True,
        "fade": True,
    },
    "sfx_enabled": ["whoosh", "pop", "click", "camera_shutter"],
    "music_categories": ["energetic", "technology", "cinematic", "motivational", "chill"],
    "music_volume": 0.18,
    "sfx_volume": 0.28,
    "voice_volume": 1.0,
    "captions_enabled": True,
}


STAGE_PROGRESS = {
    "DOWNLOADING": 10,
    "DOWNLOADED": 10,
    "PROBING": 15,
    "TRANSCRIBING": 30,
    "TRANSCRIBED": 30,
    "PLANNING": 40,
    "PLAN_READY": 40,
    "SEARCHING_BROLL": 55,
    "BROLL_READY": 55,
    "RENDERING": 95,
    "RENDERED": 95,
    "VALIDATING": 98,
    "READY": 100,
    "FAILED": 0,
    "QUEUED": 1,
    "DISCOVERED": 0,
}

PIPELINE_ORDER = [
    "DISCOVERED",
    "QUEUED",
    "DOWNLOADING",
    "DOWNLOADED",
    "PROBING",
    "TRANSCRIBING",
    "TRANSCRIBED",
    "PLANNING",
    "PLAN_READY",
    "SEARCHING_BROLL",
    "BROLL_READY",
    "RENDERING",
    "RENDERED",
    "VALIDATING",
    "READY",
]
