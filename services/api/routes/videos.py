from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from autoedit.auth import get_current_user
from autoedit.db import get_db
from autoedit.models import EditPlan, Project, RenderJob, Transcript, User, Video
from api.routes.projects import serialize_video

router = APIRouter(prefix="/api/videos", tags=["videos"])


def _owned_video(db: Session, user: User, video_id: uuid.UUID) -> Video:
    video = (
        db.query(Video)
        .join(Project)
        .options(joinedload(Video.transcript), joinedload(Video.edit_plans), joinedload(Video.render_jobs))
        .filter(Video.id == video_id, Project.user_id == user.id)
        .first()
    )
    if not video:
        raise HTTPException(404, "Video not found")
    return video


@router.get("/{video_id}")
def get_video(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _owned_video(db, user, video_id)
    plan = (
        db.query(EditPlan).filter(EditPlan.video_id == video.id).order_by(EditPlan.version.desc()).first()
    )
    data = serialize_video(video)
    data["projectId"] = str(video.project_id)
    data["transcript"] = None
    if video.transcript:
        data["transcript"] = {
            "language": video.transcript.language,
            "fullText": video.transcript.full_text,
            "segments": video.transcript.segments_json,
        }
    data["editPlan"] = plan.plan_json if plan else None
    job = (
        db.query(RenderJob).filter(RenderJob.video_id == video.id).order_by(RenderJob.created_at.desc()).first()
    )
    data["outputPath"] = job.output_path if job else None
    return data


@router.post("/{video_id}/process")
def process_one(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.tasks import process_video_task

    video = _owned_video(db, user, video_id)
    video.status = "QUEUED"
    video.current_stage = "Queued"
    video.progress = 1
    video.updated_at = datetime.utcnow()
    db.commit()
    process_video_task.delay(str(video.id))
    return serialize_video(video)


@router.post("/{video_id}/retry")
def retry_one(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.tasks import process_video_task

    video = _owned_video(db, user, video_id)
    video.retry_count += 1
    video.status = "QUEUED"
    video.error_message = None
    video.updated_at = datetime.utcnow()
    db.commit()
    process_video_task.delay(str(video.id))
    return serialize_video(video)


@router.delete("/{video_id}")
def delete_video(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _owned_video(db, user, video_id)
    db.delete(video)
    db.commit()
    return {"ok": True}


@router.get("/{video_id}/download")
def download_video(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _owned_video(db, user, video_id)
    job = (
        db.query(RenderJob)
        .filter(RenderJob.video_id == video.id, RenderJob.status == "READY")
        .order_by(RenderJob.created_at.desc())
        .first()
    )
    if not job or not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(404, "Rendered file not ready")
    return FileResponse(job.output_path, media_type="video/mp4", filename=f"{Path(video.filename).stem}-autoedit.mp4")


@router.get("/{video_id}/stream")
def stream_video(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _owned_video(db, user, video_id)
    job = (
        db.query(RenderJob)
        .filter(RenderJob.video_id == video.id)
        .order_by(RenderJob.created_at.desc())
        .first()
    )
    if not job or not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(404, "No output to preview")
    return FileResponse(job.output_path, media_type="video/mp4")
