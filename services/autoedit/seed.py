from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from autoedit.config import get_settings
from autoedit.models import LibraryAsset
from autoedit.edit_schema import LEGACY_SFX_NAMES
from autoedit.music import TRACKS
from autoedit.sfx.registry import load_catalog, resolve_sfx_path

SFX_NAMES = list(LEGACY_SFX_NAMES)

OLD_MUSIC_FILES = (
    "energetic.wav",
    "technology.wav",
    "cinematic.wav",
    "motivational.wav",
    "chill.wav",
)
OLD_MUSIC_NAMES = ("energetic", "technology", "cinematic", "motivational", "chill")


def seed_system_assets(db: Session) -> None:
    assets_dir = get_settings().assets_dir
    rows = db.query(LibraryAsset).filter(LibraryAsset.is_system.is_(True)).all()
    existing = {a.name: a for a in rows}

    for name in LEGACY_SFX_NAMES:
        row = existing.pop(name, None)
        if row and row.asset_type == "sfx":
            legacy_path = Path(row.local_path)
            db.delete(row)
            if legacy_path.exists() and legacy_path.parent == (assets_dir / "sfx").resolve():
                legacy_path.unlink(missing_ok=True)
        else:
            leftover = assets_dir / "sfx" / f"{name}.wav"
            leftover.unlink(missing_ok=True)

    for item in load_catalog():
        path = resolve_sfx_path(item, sfx_dir=assets_dir / "sfx")
        if not path:
            continue
        row = existing.get(item.id)
        if row:
            row.local_path = str(path.resolve())
            row.category = item.category
            row.enabled = True
            row.asset_type = "sfx"
            continue
        db.add(
            LibraryAsset(
                user_id=None,
                name=item.id,
                asset_type="sfx",
                category=item.category,
                local_path=str(path.resolve()),
                enabled=True,
                is_system=True,
            )
        )

    music_dir = assets_dir / "music"
    for old_name in OLD_MUSIC_NAMES:
        row = existing.pop(old_name, None)
        if row and row.asset_type == "music":
            db.delete(row)
    for filename in OLD_MUSIC_FILES:
        (music_dir / filename).unlink(missing_ok=True)

    keep_names = {track.id for track in TRACKS}
    keep_files = {track.file for track in TRACKS}
    for row in list(existing.values()):
        if row.asset_type == "music" and row.name not in keep_names:
            db.delete(row)
            existing.pop(row.name, None)

    if music_dir.exists():
        for path in music_dir.iterdir():
            if not path.is_file():
                continue
            if path.name in {".gitkeep", "background_music_decision_engine.md"}:
                continue
            if path.name not in keep_files:
                path.unlink(missing_ok=True)

    for track in TRACKS:
        path = music_dir / track.file
        if not path.exists():
            continue
        row = existing.get(track.id)
        if row:
            row.local_path = str(path.resolve())
            row.category = track.id
            row.enabled = True
            row.asset_type = "music"
            row.name = track.id
            continue
        db.add(
            LibraryAsset(
                user_id=None,
                name=track.id,
                asset_type="music",
                category=track.id,
                local_path=str(path.resolve()),
                enabled=True,
                is_system=True,
            )
        )
    db.commit()
