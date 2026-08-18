from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from autoedit.auth import get_current_user
from autoedit.config import get_settings
from autoedit.db import get_db
from autoedit.edit_schema import merge_style_profile
from autoedit.models import DriveConnection, StyleProfile, User

router = APIRouter(prefix="/api", tags=["settings"])


class StyleBody(BaseModel):
    profile: dict


@router.get("/style")
def get_style(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(StyleProfile).filter(StyleProfile.user_id == user.id).first()
    return merge_style_profile(row.profile_json if row else None)


@router.put("/style")
def put_style(body: StyleBody, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(StyleProfile).filter(StyleProfile.user_id == user.id).first()
    merged = merge_style_profile(body.profile or {})
    if not row:
        row = StyleProfile(user_id=user.id, profile_json=merged)
        db.add(row)
    else:
        row.profile_json = merged
        flag_modified(row, "profile_json")
    db.commit()
    db.refresh(row)
    return merge_style_profile(row.profile_json)


@router.get("/settings")
def get_settings_payload(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conn = db.query(DriveConnection).filter(DriveConnection.user_id == user.id).first()
    s = get_settings()
    return {
        "googleConnected": bool(conn),
        "workerConcurrency": s.worker_concurrency,
        "transcriptionProvider": s.transcription_provider,
        "llmProvider": s.llm_provider,
        "hasOpenAIKey": bool(s.openai_api_key),
        "hasPexelsKey": bool(s.pexels_api_key),
    }
