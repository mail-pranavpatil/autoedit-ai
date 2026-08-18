from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import joinedload

from fastapi import HTTPException

from autoedit.auth import get_valid_access_token
from autoedit.db import SessionLocal
from autoedit.logging_setup import setup_logging
from autoedit.models import User, Video
from autoedit.pipeline import process_video, render_video
from worker.celery_app import celery_app

setup_logging()
logger = logging.getLogger("autoedit")


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
