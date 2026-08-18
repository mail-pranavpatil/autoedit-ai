from __future__ import annotations

from dataclasses import dataclass, field

from autoedit.edit_schema import EditPlan

PAN_EFFECTS = {"pan_left", "pan_right", "pan_up", "pan_down"}
ZOOM_EFFECTS = {"slow_zoom_in", "slow_zoom_out"}
MIN_BOOKEND_DURATION = 0.5


@dataclass
class SfxCandidate:
    t: float
    event_type: str
    visual: float = 0.0
    narrative: float = 0.0
    transition: float = 0.0
    emotion: float = 0.0
    motion: float = 0.0
    text: float = 0.0
    reason: str = ""
    combo: str | None = None
    major: bool = False
    extra: dict = field(default_factory=dict)

    def raw_score(self) -> float:
        return self.visual + self.narrative + self.transition + self.emotion + self.motion + self.text


def extract_candidates(
    plan: EditPlan,
    phrases: list[dict] | None = None,
    transcript: dict | None = None,
) -> list[SfxCandidate]:
    """One in/out pair per B-roll. Caption, reveal, and joke accents are unused for now."""
    del phrases, transcript
    candidates: list[SfxCandidate] = []
    segs = list(plan.segments)
    first_broll = True

    for i, seg in enumerate(segs):
        if seg.visual != "broll":
            continue
        prev = segs[i - 1] if i else None
        long_talk = bool(prev and prev.visual == "talking_head" and (prev.end - prev.start) >= 4)
        major = first_broll or long_talk or seg.effect in ZOOM_EFFECTS or seg.effect in PAN_EFFECTS
        duration = float(seg.end) - float(seg.start)
        extra = {
            "pair_id": i,
            "first": first_broll,
            "duration": duration,
        }
        reason = "B-roll comes on screen" if not (seg.broll_type == "image") else "Still image or screenshot appears"
        candidates.append(
            SfxCandidate(
                t=float(seg.start),
                event_type="broll_in",
                visual=0.85,
                transition=0.9,
                reason=reason,
                major=major,
                extra=extra,
            )
        )
        if duration >= MIN_BOOKEND_DURATION:
            candidates.append(
                SfxCandidate(
                    t=float(seg.end),
                    event_type="broll_out",
                    visual=0.85,
                    transition=0.9,
                    reason="B-roll leaves the screen",
                    major=major,
                    extra=extra,
                )
            )
        first_broll = False

    candidates.sort(key=lambda c: (c.t, 0 if c.event_type == "broll_in" else 1))
    return candidates


def transcript_text(transcript: dict | None) -> str:
    if not transcript:
        return ""
    return str(transcript.get("full_text") or "")
