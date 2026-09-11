from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from autoedit.auth import get_current_user
from autoedit.db import get_db
from autoedit.models import Project, User, Video
from autoedit.object_storage import serve_response

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/thumb/{video_id}")
def thumb(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = (
        db.query(Video)
        .join(Project)
        .filter(Video.id == video_id, Project.user_id == user.id)
        .first()
    )
    if not video or not video.thumbnail_path:
        raise HTTPException(404, "No thumbnail")
    return serve_response(video.thumbnail_path, media_type="image/jpeg")
