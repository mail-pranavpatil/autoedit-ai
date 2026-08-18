from __future__ import annotations

STYLE_BUCKETS = (
    "TECH",
    "EDUCATIONAL",
    "BUSINESS",
    "COMEDY",
    "CINEMATIC",
    "STORYTELLING",
    "NEWS",
    "MOTIVATIONAL",
    "TUTORIAL",
    "PRODUCT_DEMO",
)

# Preferred gap seconds (lo, hi) and score threshold.
STYLE_DENSITY = {
    "TECH": (2.0, 4.0, 0.52),
    "EDUCATIONAL": (2.5, 5.0, 0.55),
    "BUSINESS": (2.5, 5.0, 0.56),
    "COMEDY": (1.5, 3.5, 0.48),
    "CINEMATIC": (3.0, 8.0, 0.6),
    "STORYTELLING": (3.0, 6.0, 0.58),
    "NEWS": (2.5, 5.0, 0.58),
    "MOTIVATIONAL": (2.0, 5.0, 0.54),
    "TUTORIAL": (2.0, 4.5, 0.53),
    "PRODUCT_DEMO": (1.8, 4.0, 0.5),
}

# Category multipliers by content style.
STYLE_CATEGORY_WEIGHT = {
    "TECH": {
        "ui_text_accent": 1.1,
        "text_reveal": 1.0,
        "transition": 1.05,
        "fast_transition": 1.1,
        "directional_motion": 1.0,
        "camera": 0.9,
        "buildup": 0.85,
        "pattern_interrupt": 0.7,
        "comedy": 0.05,
    },
    "EDUCATIONAL": {
        "ui_text_accent": 1.15,
        "text_reveal": 1.05,
        "transition": 0.85,
        "fast_transition": 0.7,
        "directional_motion": 0.8,
        "camera": 1.1,
        "buildup": 0.7,
        "pattern_interrupt": 0.45,
        "comedy": 0.02,
    },
    "COMEDY": {
        "comedy": 1.2,
        "pattern_interrupt": 1.15,
        "ui_text_accent": 0.9,
        "transition": 0.8,
        "fast_transition": 0.85,
        "buildup": 0.5,
        "camera": 0.7,
    },
    "CINEMATIC": {
        "transition": 1.2,
        "buildup": 1.25,
        "directional_motion": 1.0,
        "ui_text_accent": 0.45,
        "comedy": 0.0,
        "fast_transition": 0.4,
        "camera": 0.7,
        "pattern_interrupt": 0.5,
    },
    "NEWS": {
        "transition": 0.7,
        "camera": 1.15,
        "buildup": 0.9,
        "ui_text_accent": 0.55,
        "comedy": 0.0,
        "pattern_interrupt": 0.35,
        "fast_transition": 0.5,
    },
}

LEGACY_SFX_TO_CATEGORY = {
    "whoosh": "transition",
    "pop": "ui_text_accent",
    "click": "ui_text_accent",
    "camera_shutter": "camera",
    "notification": "ui_text_accent",
    "ding": "ui_text_accent",
    "swipe": "directional_motion",
    "impact": "buildup",
    "bubble": "ui_text_accent",
    "cartoon": "comedy",
}


def detect_style(tone: str, music_category: str | None = None, transcript: str = "") -> str:
    blob = f"{tone} {music_category or ''} {transcript[:400]}".lower()
    checks = [
        ("COMEDY", ("comedy", "funny", "humor", "joke", "sarcastic", "sketch")),
        ("CINEMATIC", ("cinematic", "dramatic", "film", "epic")),
        ("NEWS", ("news", "breaking", "report", "headline")),
        ("TECH", ("tech", "technology", "software", "ai", "startup", "coding")),
        ("TUTORIAL", ("tutorial", "how to", "step by step", "learn")),
        ("PRODUCT_DEMO", ("product", "demo", "unbox", "review")),
        ("MOTIVATIONAL", ("motivat", "hustle", "mindset")),
        ("BUSINESS", ("business", "finance", "market", "company")),
        ("STORYTELLING", ("story", "narrative", "journey")),
        ("EDUCATIONAL", ("educat", "explain", "lesson", "history")),
    ]
    for bucket, keys in checks:
        if any(k in blob for k in keys):
            return bucket
    if music_category in {"technology", "cornfield_chase"}:
        return "TECH" if music_category == "technology" else "CINEMATIC"
    if music_category == "cinematic":
        return "CINEMATIC"
    if music_category in {"motivational", "thank_you"}:
        return "MOTIVATIONAL"
    return "EDUCATIONAL"


def preferred_gap(style_bucket: str, montage: bool) -> tuple[float, float, float]:
    lo, hi, thresh = STYLE_DENSITY.get(style_bucket, STYLE_DENSITY["EDUCATIONAL"])
    if montage:
        return (1.0, 3.0, max(0.45, thresh - 0.06))
    return lo, hi, thresh


def category_weight(style_bucket: str, category: str) -> float:
    table = STYLE_CATEGORY_WEIGHT.get(style_bucket) or STYLE_CATEGORY_WEIGHT["EDUCATIONAL"]
    if category in table:
        return table[category]
    return 0.7


def enabled_categories(sfx_enabled: list | None) -> set[str] | None:
    """None means all categories. Old whoosh/pop allowlists mean 'SFX on', not a tight filter."""
    if not sfx_enabled:
        return None
    keys = [str(name).strip() for name in sfx_enabled if str(name).strip()]
    if not keys:
        return None
    if all(key in LEGACY_SFX_TO_CATEGORY for key in keys):
        return None
    cats: set[str] = set()
    for key in keys:
        if key in LEGACY_SFX_TO_CATEGORY:
            cats.add(LEGACY_SFX_TO_CATEGORY[key])
        else:
            cats.add(key)
    return cats or None
