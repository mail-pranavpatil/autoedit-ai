from __future__ import annotations

from sqlalchemy.orm import Session

from autoedit.config import get_settings
from autoedit.models import LibraryAsset
from autoedit.tones import write_tone

SFX_NAMES = [
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

MUSIC_CATEGORIES = ["energetic", "technology", "cinematic", "motivational", "chill"]


def seed_system_assets(db: Session) -> None:
    assets_dir = get_settings().assets_dir
    existing = {a.name for a in db.query(LibraryAsset).filter(LibraryAsset.is_system.is_(True)).all()}
    freqs = [180, 420, 880, 1200, 980, 660, 240, 90, 1500, 330]
    for name, freq in zip(SFX_NAMES, freqs):
        path = assets_dir / "sfx" / f"{name}.wav"
        if not path.exists():
            write_tone(path, freq, 0.35, volume=0.35)
        if name not in existing:
            db.add(
                LibraryAsset(
                    user_id=None,
                    name=name,
                    asset_type="sfx",
                    category="system",
                    local_path=str(path.resolve()),
                    enabled=True,
                    is_system=True,
                )
            )
    for i, cat in enumerate(MUSIC_CATEGORIES):
        path = assets_dir / "music" / f"{cat}.wav"
        if not path.exists():
            write_tone(path, 110 + i * 20, 8.0, volume=0.12)
        if cat not in existing:
            db.add(
                LibraryAsset(
                    user_id=None,
                    name=cat,
                    asset_type="music",
                    category=cat,
                    local_path=str(path.resolve()),
                    enabled=True,
                    is_system=True,
                )
            )
    db.commit()
