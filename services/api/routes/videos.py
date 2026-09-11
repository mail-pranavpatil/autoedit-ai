from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from autoedit.auth import get_current_user
from autoedit.captions import phrases_from_plan_or_transcript
from autoedit.db import get_db
from autoedit.edit_schema import EditPlan as EditPlanSchema
from autoedit.models import BrollAsset, EditPlan, Project, RenderJob, User, Video, YoutubeUpload
from autoedit.pipeline import pick_music
from api.routes.projects import serialize_video

router = APIRouter(prefix="/api/videos", tags=["videos"])
logger = logging.getLogger("autoedit")


def _owned_video(db: Session, user: User, video_id: uuid.UUID) -> Video:
    video = (
        db.query(Video)
        .join(Project)
        .options(
            joinedload(Video.transcript),
            joinedload(Video.edit_plans),
            joinedload(Video.render_jobs),
            joinedload(Video.youtube_upload),  # must be eager — lazy load fails on detached instances
        )
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
    result = process_video_task.delay(str(video.id))
    video.celery_task_id = result.id
    db.commit()
    return serialize_video(video)


@router.post("/{video_id}/retry")
def retry_one(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.tasks import process_video_task

    video = _owned_video(db, user, video_id)
    video.retry_count += 1
    video.status = "QUEUED"
    video.error_message = None
    video.updated_at = datetime.utcnow()
    result = process_video_task.delay(str(video.id))
    video.celery_task_id = result.id
    db.commit()
    return serialize_video(video)


@router.post("/cancel-all")
def cancel_all_processing(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.celery_app import celery_app
    from autoedit.pipeline import abort_video

    videos = (
        db.query(Video)
        .join(Project)
        .filter(Project.user_id == user.id, Video.status.notin_(["READY", "FAILED", "DISCOVERED"]))
        .all()
    )
    for video in videos:
        if video.celery_task_id:
            celery_app.control.revoke(video.celery_task_id, terminate=True, signal="SIGKILL")
        abort_video(db, video, "Cancelled by user (stop all)")
    return {"cancelled": len(videos)}


@router.post("/{video_id}/cancel")
def cancel_video(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.celery_app import celery_app
    from autoedit.pipeline import abort_video

    video = _owned_video(db, user, video_id)
    if video.status in {"READY", "FAILED", "DISCOVERED"}:
        raise HTTPException(400, "Video is not processing")
    if video.celery_task_id:
        celery_app.control.revoke(video.celery_task_id, terminate=True, signal="SIGKILL")
    abort_video(db, video, "Cancelled by user")
    return serialize_video(video)


@router.post("/{video_id}/youtube/retry")
def retry_youtube(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from worker.tasks import publish_youtube_task

    video = _owned_video(db, user, video_id)
    if video.status != "READY":
        raise HTTPException(400, "Render the video before uploading to YouTube")
    if video.youtube_upload and video.youtube_upload.status == "SCHEDULED":
        raise HTTPException(400, "Already scheduled on YouTube")
    if video.youtube_upload:
        video.youtube_upload.status = "PENDING"
        video.youtube_upload.error_message = None
    else:
        db.add(YoutubeUpload(user_id=user.id, video_id=video.id, status="PENDING"))
    db.commit()
    db.expire(video, ["youtube_upload"])
    publish_youtube_task.delay(str(video.id), force=True)
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
    return FileResponse(
        job.output_path,
        media_type="video/mp4",
        filename=f"{Path(video.filename).stem}-autoedit.mp4",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


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
    return FileResponse(
        job.output_path,
        media_type="video/mp4",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


def _latest_plan(db: Session, video_id: uuid.UUID) -> EditPlan | None:
    return db.query(EditPlan).filter(EditPlan.video_id == video_id).order_by(EditPlan.version.desc()).first()


def _file_media_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
        ".m4v": "video/mp4",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
    }.get(suffix, "application/octet-stream")


@router.get("/{video_id}/editor")
def get_editor(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = (
        db.query(Video)
        .join(Project)
        .options(
            joinedload(Video.transcript),
            joinedload(Video.broll_assets),
            joinedload(Video.project),
        )
        .filter(Video.id == video_id, Project.user_id == user.id)
        .first()
    )
    if not video:
        raise HTTPException(404, "Video not found")
    plan_row = _latest_plan(db, video.id)
    plan_json = plan_row.plan_json if plan_row else None
    parsed = EditPlanSchema.model_validate(plan_json) if plan_json else None
    segments = video.transcript.segments_json if video.transcript else None
    phrases = phrases_from_plan_or_transcript(
        [p.model_dump() for p in parsed.caption_phrases] if parsed and parsed.caption_phrases else None,
        segments if isinstance(segments, list) else None,
        words_per_line=parsed.caption_style.words_per_line if parsed and parsed.caption_style else None,
    )
    job = db.query(RenderJob).filter(RenderJob.video_id == video.id).order_by(RenderJob.created_at.desc()).first()
    music = pick_music(db, parsed.music_category if parsed else "feeling_blue", user.id)
    data = serialize_video(video)
    data["projectId"] = str(video.project_id)
    data["editPlan"] = parsed.model_dump() if parsed else None
    data["captionPhrases"] = phrases
    data["sourceUrl"] = f"/api/videos/{video.id}/source"
    data["musicUrl"] = f"/api/videos/{video.id}/music" if music and music.local_path else None
    data["outputReady"] = bool(job and job.status == "READY" and job.output_path and Path(job.output_path).exists())
    data["brollAssets"] = [
        {
            "id": str(a.id),
            "query": a.query,
            "assetType": a.asset_type,
            "url": f"/api/videos/{video.id}/assets/{a.id}",
        }
        for a in video.broll_assets
        if a.local_path
    ]
    data["transcript"] = None
    if video.transcript:
        data["transcript"] = {
            "language": video.transcript.language,
            "fullText": video.transcript.full_text,
            "segments": video.transcript.segments_json,
        }
    return data


@router.get("/{video_id}/source")
def stream_source(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _owned_video(db, user, video_id)
    if not video.local_path or not Path(video.local_path).exists():
        raise HTTPException(404, "Source file not found")
    return FileResponse(video.local_path, media_type=_file_media_type(video.local_path))


@router.get("/{video_id}/music")
def stream_music(video_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    video = _owned_video(db, user, video_id)
    plan_row = _latest_plan(db, video.id)
    category = "feeling_blue"
    if plan_row:
        category = (plan_row.plan_json or {}).get("music_category") or category
    music = pick_music(db, category, user.id)
    if not music or not music.local_path or not Path(music.local_path).exists():
        raise HTTPException(404, "No music file")
    return FileResponse(music.local_path, media_type=_file_media_type(music.local_path))


@router.get("/{video_id}/assets/{asset_id}")
def stream_asset(
    video_id: uuid.UUID,
    asset_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = _owned_video(db, user, video_id)
    asset = db.query(BrollAsset).filter(BrollAsset.id == asset_id, BrollAsset.video_id == video.id).first()
    if not asset or not asset.local_path or not Path(asset.local_path).exists():
        raise HTTPException(404, "Asset not found")
    return FileResponse(asset.local_path, media_type=_file_media_type(asset.local_path))


class EditPlanBody(BaseModel):
    plan: dict


@router.put("/{video_id}/edit-plan")
def save_edit_plan(
    video_id: uuid.UUID,
    body: EditPlanBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = _owned_video(db, user, video_id)
    parsed = EditPlanSchema.model_validate(body.plan)
    latest = _latest_plan(db, video.id)
    version = (latest.version + 1) if latest else 1
    dumped = parsed.model_dump(mode="json")
    row = EditPlan(video_id=video.id, version=version, plan_json=dumped)
    db.add(row)
    db.commit()
    logger.info("Saved edit plan v%s caption_style=%s", version, dumped.get("caption_style", {}).get("preset"))
    return {"ok": True, "version": version, "editPlan": dumped}


class RenderBody(BaseModel):
    plan: dict


@router.post("/{video_id}/render")
def render_from_editor(
    video_id: uuid.UUID,
    body: RenderBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from worker.tasks import render_video_task

    video = _owned_video(db, user, video_id)
    if not video.local_path:
        raise HTTPException(400, "Source missing; process the video first")
    parsed = EditPlanSchema.model_validate(body.plan)
    dumped = parsed.model_dump(mode="json")
    latest = _latest_plan(db, video.id)
    version = (latest.version + 1) if latest else 1
    db.add(EditPlan(video_id=video.id, version=version, plan_json=dumped))
    video.status = "QUEUED"
    video.current_stage = "Queued render"
    video.progress = 1
    video.updated_at = datetime.utcnow()
    result = render_video_task.delay(str(video.id), plan_json=dumped)
    video.celery_task_id = result.id
    db.commit()
    logger.info(
        "Queue render %s plan v%s caption_style=%s",
        video.id,
        version,
        dumped.get("caption_style", {}).get("preset"),
    )
    return serialize_video(video)
