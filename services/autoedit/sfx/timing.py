from __future__ import annotations

LEAD_IN = {
    "hard_pop": 0.0,
    "long_pop": 0.04,
    "camera_shutter": 0.0,
    "fast_double": 0.0,
    "cinematic_whoosh": 0.45,
    "medium_whoosh": 0.35,
    "arrow_whoosh": 0.28,
    "vinyl": 0.05,
    "cartoon_whistle": 0.02,
    "riser": 1.55,
}


def aligned_start(event_t: float, sfx_type: str, kind: str | None = None) -> float:
    lead = LEAD_IN.get(sfx_type)
    if lead is None:
        if kind == "riser":
            lead = 1.55
        elif kind == "transition":
            lead = 0.35
        else:
            lead = 0.04
    return max(0.0, event_t - lead)
