from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from autoedit.auth import get_current_user
from autoedit.config import get_settings
from autoedit.db import get_db
from autoedit.models import LibraryAsset, User

router = APIRouter(prefix="/api/assets", tags=["assets"])

ALLOWED_AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".ogg"}
MAX_UPLOAD = 40 * 1024 * 1024


def serialize(a: LibraryAsset) -> dict:
    return {
        "id": str(a.id),
        "name": a.name,
        "assetType": a.asset_type,
        "category": a.category,
        "enabled": a.enabled,
        "isSystem": a.is_system,
        "previewUrl": f"/api/assets/{a.id}/preview",
        "createdAt": a.created_at.isoformat() if a.created_at else None,
    }


@router.get("")
def list_assets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(LibraryAsset)
        .filter((LibraryAsset.user_id == user.id) | (LibraryAsset.is_system.is_(True)))
        .order_by(LibraryAsset.asset_type, LibraryAsset.name)
        .all()
    )
    return [serialize(a) for a in rows]


@router.post("/upload")
async def upload_asset(
    assetType: str = Form(...),
    name: str = Form(...),
    category: str | None = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if assetType not in {"music", "sfx"}:
        raise HTTPException(400, "assetType must be music or sfx")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_AUDIO:
        raise HTTPException(400, "Unsupported audio type")
    dest_dir = get_settings().storage_dir / "uploads" / str(user.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid.uuid4()}{suffix}"
    size = 0
    with open(dest, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD:
                dest.unlink(missing_ok=True)
                raise HTTPException(400, "File too large")
            out.write(chunk)
    row = LibraryAsset(
        user_id=user.id,
        name=name.strip() or Path(file.filename or "asset").stem,
        asset_type=assetType,
        category=category,
        local_path=str(dest.resolve()),
        enabled=True,
        is_system=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.post("/{asset_id}/toggle")
def toggle(asset_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = (
        db.query(LibraryAsset)
        .filter(LibraryAsset.id == asset_id)
        .filter((LibraryAsset.user_id == user.id) | (LibraryAsset.is_system.is_(True)))
        .first()
    )
    if not row:
        raise HTTPException(404, "Asset not found")
    row.enabled = not row.enabled
    db.commit()
    return serialize(row)


@router.delete("/{asset_id}")
def delete_asset(asset_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(LibraryAsset).filter(LibraryAsset.id == asset_id, LibraryAsset.user_id == user.id).first()
    if not row:
        raise HTTPException(404, "Asset not found or cannot delete system asset")
    path = Path(row.local_path)
    db.delete(row)
    db.commit()
    if path.exists() and "uploads" in str(path):
        path.unlink(missing_ok=True)
    return {"ok": True}


@router.get("/{asset_id}/preview")
def preview(asset_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse

    row = (
        db.query(LibraryAsset)
        .filter(LibraryAsset.id == asset_id)
        .filter((LibraryAsset.user_id == user.id) | (LibraryAsset.is_system.is_(True)))
        .first()
    )
    if not row or not Path(row.local_path).exists():
        raise HTTPException(404, "Asset file missing")
    return FileResponse(row.local_path)
