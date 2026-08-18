from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from autoedit.auth import get_current_user
from autoedit.db import get_db
from autoedit.models import User, Video, YoutubeUpload
from autoedit.youtube import serialize_youtube_listing

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


@router.get("/uploads")
def list_youtube_uploads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _kick_stale_pending(db, user.id)
    rows = (
        db.query(YoutubeUpload)
        .options(joinedload(YoutubeUpload.video).joinedload(Video.project))
        .filter(YoutubeUpload.user_id == user.id)
        .order_by(YoutubeUpload.scheduled_at.desc().nulls_last(), YoutubeUpload.created_at.desc())
        .all()
    )
    return [serialize_youtube_listing(row) for row in rows]


def _kick_stale_pending(db: Session, user_id) -> None:
    from worker.tasks import publish_youtube_task

    cutoff = datetime.utcnow() - timedelta(seconds=30)
    stale = (
        db.query(YoutubeUpload)
        .filter(
            YoutubeUpload.user_id == user_id,
            YoutubeUpload.status == "PENDING",
            YoutubeUpload.updated_at <= cutoff,
        )
        .all()
    )
    if not stale:
        return
    for row in stale:
        publish_youtube_task.delay(str(row.video_id), force=True)
        row.updated_at = datetime.utcnow()
    db.commit()
