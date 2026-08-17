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


class EditPlan(BaseModel):
    video_summary: str
    tone: str
    music_category: MusicCategory
    segments: list[EditSegment] = Field(min_length=1)

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
