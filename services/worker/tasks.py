from __future__ import annotations

import logging
import uuid

from celery.signals import task_failure
from sqlalchemy.orm import joinedload

from fastapi import HTTPException

from autoedit.auth import get_valid_access_token
from autoedit.db import SessionLocal
from autoedit.logging_setup import setup_logging
from autoedit.models import User, Video
from autoedit.pipeline import abort_video, process_video, render_video
from worker.celery_app import celery_app

setup_logging()
logger = logging.getLogger("autoedit")

_RECOVERABLE_TASKS = {"worker.process_video", "worker.render_video"}


@task_failure.connect
def _mark_video_failed_on_worker_loss(sender=None, task_id=None, exception=None, args=None, kwargs=None, **_kw):
    """Safety net for OOM/SIGKILL: if the celery worker process itself dies mid-task
    (not just an ffmpeg subprocess it spawned), nothing inside process_video/
    render_video survives to run their own except-block cleanup - the video row
    just stays parked at whatever stage was last committed, forever. With
    task_reject_on_worker_lost left at its default (False), Celery treats a lost
    worker as a task failure and fires this signal from the surviving master
    process, so we can mark the video FAILED from here instead.
    """
    name = getattr(sender, "name", "") or ""
    if name not in _RECOVERABLE_TASKS:
        return
    video_id = (args[0] if args else None) or (kwargs or {}).get("video_id")
    if not video_id:
        return
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == uuid.UUID(str(video_id))).first()
        if not video or video.status in {"FAILED", "READY"}:
            return
        abort_video(db, video, str(exception or "worker process lost"))
        logger.error("Marked video %s FAILED after worker loss (task %s)", video_id, task_id)
    finally:
        db.close()


@celery_app.task(name="worker.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="worker.process_video", bind=True, max_retries=0)
def process_video_task(self, video_id: str) -> str:
    db = SessionLocal()
    try:
        video = (
            db.query(Video)
            .options(joinedload(Video.project))
            .filter(Video.id == uuid.UUID(video_id))
            .first()
        )
        if not video:
            return "missing"
        user = db.query(User).filter(User.id == video.project.user_id).first()
        token = None
        if user:
            try:
                token = get_valid_access_token(db, user)
            except HTTPException:
                logger.warning("No valid Google token for video %s", video_id)
        process_video(db, video_id, access_token=token)
        return "ok"
    except Exception:
        logger.exception("process_video_task failed for %s", video_id)
        raise
    finally:
        db.close()


@celery_app.task(name="worker.render_video", bind=True, max_retries=0)
def render_video_task(self, video_id: str, plan_json: dict | None = None) -> str:
    db = SessionLocal()
    try:
        render_video(db, video_id, plan_json=plan_json)
        return "ok"
    except Exception:
        logger.exception("render_video_task failed for %s", video_id)
        raise
    finally:
        db.close()


@celery_app.task(name="worker.publish_youtube", bind=True, max_retries=0)
def publish_youtube_task(self, video_id: str, force: bool = False) -> str:
    from autoedit.youtube import publish_video_to_youtube

    db = SessionLocal()
    try:
        return publish_video_to_youtube(db, video_id, force=force)
    except Exception:
        logger.exception("publish_youtube_task failed for %s", video_id)
        raise
    finally:
        db.close()
