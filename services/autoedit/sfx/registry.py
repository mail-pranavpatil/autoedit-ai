from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

COPY_SUFFIX = re.compile(r" copy(?: \d+)?$", re.IGNORECASE)


@dataclass(frozen=True)
class SfxMeta:
    id: str
    file: str
    category: str
    type: str
    energy: float
    duration_class: str
    mood: tuple[str, ...]
    best_for: tuple[str, ...]
    avoid_for: tuple[str, ...]
    priority: float
    license: str
    source: str
    commercial_use: bool | str
    redistribution_allowed: bool | str
    unverified_license: bool

    @classmethod
    def from_dict(cls, raw: dict) -> SfxMeta:
        return cls(
            id=str(raw["id"]),
            file=str(raw["file"]),
            category=str(raw["category"]),
            type=str(raw["type"]),
            energy=float(raw.get("energy", 0.5)),
            duration_class=str(raw.get("duration_class", "short")),
            mood=tuple(raw.get("mood") or ()),
            best_for=tuple(raw.get("best_for") or ()),
            avoid_for=tuple(raw.get("avoid_for") or ()),
            priority=float(raw.get("priority", 0.5)),
            license=str(raw.get("license", "unknown")),
            source=str(raw.get("source", "unknown")),
            commercial_use=raw.get("commercial_use", "VERIFY"),
            redistribution_allowed=raw.get("redistribution_allowed", "VERIFY"),
            unverified_license=bool(raw.get("unverified_license", False)),
        )


def catalog_path() -> Path:
    return Path(__file__).resolve().parent / "catalog.json"


def load_catalog(path: Path | None = None) -> list[SfxMeta]:
    data = json.loads((path or catalog_path()).read_text())
    return [SfxMeta.from_dict(item) for item in data.get("items") or []]


def canonical_filename(name: str) -> str:
    p = Path(name)
    stem = COPY_SUFFIX.sub("", p.stem)
    return f"{stem}{p.suffix}"


def index_sfx_dir(sfx_dir: Path) -> dict[str, Path]:
    """Map canonical filename (lower) -> preferred existing path, ignoring duplicate copies."""
    found: dict[str, Path] = {}
    if not sfx_dir.exists():
        return found
    for path in sorted(sfx_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".wav", ".mp3", ".m4a", ".aac", ".ogg"}:
            continue
        key = canonical_filename(path.name).lower()
        is_copy = bool(COPY_SUFFIX.search(path.stem))
        existing = found.get(key)
        if existing is None:
            found[key] = path
            continue
        existing_copy = bool(COPY_SUFFIX.search(existing.stem))
        if existing_copy and not is_copy:
            found[key] = path
    return found


def sfx_search_dirs(explicit: Path | None = None) -> list[Path]:
    if explicit is not None:
        return [explicit]
    dirs: list[Path] = []
    try:
        from autoedit.config import get_settings

        dirs.append(get_settings().assets_dir / "sfx")
    except Exception:
        pass
    dirs.extend(
        [
            Path("/data/assets/sfx"),
            Path("assets/sfx"),
        ]
    )
    try:
        dirs.append(catalog_path().resolve().parents[3] / "assets" / "sfx")
    except IndexError:
        pass
    out: list[Path] = []
    seen: set[str] = set()
    for d in dirs:
        try:
            key = str(d.resolve()) if d.exists() else str(d)
        except OSError:
            key = str(d)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def resolve_sfx_path(meta: SfxMeta, sfx_dir: Path | None = None) -> Path | None:
    for root in sfx_search_dirs(sfx_dir):
        indexed = index_sfx_dir(root)
        key = canonical_filename(meta.file).lower()
        hit = indexed.get(key)
        if hit and hit.exists():
            return hit
        direct = root / meta.file
        if direct.exists():
            return direct
    return None


def resolve_by_id(
    sfx_id: str,
    catalog: list[SfxMeta] | None = None,
    sfx_dir: Path | None = None,
) -> Path | None:
    items = catalog if catalog is not None else load_catalog()
    for item in items:
        if item.id == sfx_id:
            return resolve_sfx_path(item, sfx_dir=sfx_dir)
    return None
