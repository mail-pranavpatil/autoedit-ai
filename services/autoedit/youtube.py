from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from autoedit.auth import get_valid_access_token, has_youtube_scope
from autoedit.models import DriveConnection, RenderJob, User, Video, YoutubeUpload
from autoedit.youtube_schedule import next_publish_slot, publish_at_rfc3339, youtube_title_from_filename

logger = logging.getLogger("autoedit")


def serialize_youtube(row: YoutubeUpload | None) -> dict | None:
    if not row:
        return None
    scheduled = None
    if row.scheduled_at:
        when = row.scheduled_at if row.scheduled_at.tzinfo else row.scheduled_at.replace(tzinfo=timezone.utc)
        scheduled = when.astimezone(timezone.utc).isoformat()
    return {
        "status": row.status,
        "scheduledAt": scheduled,
        "url": row.youtube_url,
        "error": row.error_message,
        "title": row.title,
    }


def serialize_youtube_listing(row: YoutubeUpload) -> dict:
    data = serialize_youtube(row) or {}
    video = row.video
    project = video.project if video else None
    return {
        "id": str(row.id),
        **data,
        "filename": video.filename if video else None,
        "videoId": str(video.id) if video else None,
        "projectId": str(project.id) if project else None,
        "projectName": project.name if project else None,
    }


def should_enqueue_youtube(db: Session, video: Video, *, from_full_process: bool) -> bool:
    user = db.query(User).filter(User.id == video.project.user_id).first()
    if not user or not user.youtube_auto_upload:
        return False
    conn = db.query(DriveConnection).filter(DriveConnection.user_id == user.id).first()
    if not conn or not has_youtube_scope(conn.scopes):
        logger.info("Skipping YouTube publish for %s: YouTube scope not granted", video.id)
        return False
    existing = db.query(YoutubeUpload).filter(YoutubeUpload.video_id == video.id).first()
    if existing and existing.status == "SCHEDULED":
        return False
    if existing and existing.status == "UPLOADING":
        return False
    if from_full_process:
        return True
    return bool(existing and existing.status in {"FAILED", "PENDING"})


def enqueue_youtube_if_needed(db: Session, video: Video, *, from_full_process: bool) -> None:
    if not should_enqueue_youtube(db, video, from_full_process=from_full_process):
        return
    logger.info("Publishing YouTube upload for video %s", video.id)
    publish_video_to_youtube(db, str(video.id))


def _occupied_slots(db: Session, user_id, exclude_upload_id=None) -> set[datetime]:
    q = db.query(YoutubeUpload.scheduled_at).filter(
        YoutubeUpload.user_id == user_id,
        YoutubeUpload.scheduled_at.is_not(None),
        YoutubeUpload.status.in_(("PENDING", "UPLOADING", "SCHEDULED")),
    )
    if exclude_upload_id is not None:
        q = q.filter(YoutubeUpload.id != exclude_upload_id)
    return {row[0] for row in q.all() if row[0] is not None}


def _reserve_slot(db: Session, row: YoutubeUpload, user_id) -> tuple[datetime, YoutubeUpload]:
    row_id = row.id
    for _ in range(12):
        row = db.query(YoutubeUpload).filter(YoutubeUpload.id == row_id).first()
        occupied = _occupied_slots(db, user_id, exclude_upload_id=row_id)
        slot = next_publish_slot(datetime.now(timezone.utc), occupied)
        naive_utc = slot.astimezone(timezone.utc).replace(tzinfo=None)
        row.scheduled_at = naive_utc
        row.status = "UPLOADING"
        row.error_message = None
        row.updated_at = datetime.utcnow()
        try:
            db.commit()
            db.refresh(row)
            return slot, row
        except IntegrityError:
            db.rollback()
            logger.info("YouTube slot collision for user %s, retrying", user_id)
    raise RuntimeError("Could not reserve a YouTube publish slot")


def _youtube_service(access_token: str):
    creds = Credentials(token=access_token)
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_scheduled_video(
    access_token: str,
    file_path: str,
    title: str,
    publish_at: datetime,
    duration: float | None,
) -> str:
    description = "#Shorts" if duration is not None and duration <= 60 else ""
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_rfc3339(publish_at),
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    service = _youtube_service(access_token)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _status, response = request.next_chunk()
    video_id = response["id"]
    return video_id


def publish_video_to_youtube(db: Session, video_id: str, *, force: bool = False) -> str:
    from autoedit.models import Project
    from fastapi import HTTPException

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return "missing"
    project = db.query(Project).filter(Project.id == video.project_id).first()
    user = db.query(User).filter(User.id == project.user_id).first() if project else None
    if not user:
        return "missing-user"

    row = db.query(YoutubeUpload).filter(YoutubeUpload.video_id == video.id).first()
    if row and row.status == "SCHEDULED" and not force:
        return "already"
    if row and row.status == "UPLOADING" and not force:
        return "in-progress"
    if not row:
        row = YoutubeUpload(user_id=user.id, video_id=video.id, status="PENDING")
        db.add(row)
        try:
            db.commit()
            db.refresh(row)
        except IntegrityError:
            db.rollback()
            row = db.query(YoutubeUpload).filter(YoutubeUpload.video_id == video.id).first()

    job = (
        db.query(RenderJob)
        .filter(RenderJob.video_id == video.id, RenderJob.status == "READY")
        .order_by(RenderJob.created_at.desc())
        .first()
    )
    output = job.output_path if job else None
    if not output or not Path(output).exists():
        row.status = "FAILED"
        row.scheduled_at = None
        row.error_message = "Rendered file not ready"
        db.commit()
        return "no-file"

    title = youtube_title_from_filename(video.filename)
    row.title = title
    try:
        slot, row = _reserve_slot(db, row, user.id)
        try:
            token = get_valid_access_token(db, user)
        except HTTPException as exc:
            raise RuntimeError(getattr(exc, "detail", None) or "Google access was revoked. Sign in again.") from exc
        youtube_id = upload_scheduled_video(token, output, title, slot, video.duration)
        row.youtube_video_id = youtube_id
        row.youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
        row.status = "SCHEDULED"
        row.error_message = None
        row.updated_at = datetime.utcnow()
        db.commit()
        logger.info("Scheduled YouTube upload %s at %s for video %s", youtube_id, slot, video.id)
        return "ok"
    except Exception as exc:
        logger.exception("YouTube publish failed for %s", video.id)
        db.rollback()
        row = db.query(YoutubeUpload).filter(YoutubeUpload.video_id == video.id).first()
        if row:
            row.status = "FAILED"
            row.scheduled_at = None
            row.error_message = str(exc)[-2000:]
            row.updated_at = datetime.utcnow()
            db.commit()
        return "failed"
