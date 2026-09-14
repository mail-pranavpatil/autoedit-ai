from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from autoedit.auth import get_current_user
from autoedit.db import get_db
from autoedit.models import ConnectedChannel, User

router = APIRouter(prefix="/api/channels", tags=["channels"])


class ChannelConnectRequest(BaseModel):
    platform: str = "youtube"
    channel_id: str
    channel_title: str
    thumbnail_url: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None


class ChannelGoalsRequest(BaseModel):
    target_views: int | None = None
    target_subs: int | None = None
    target_date: str | None = None  # ISO date string e.g. "2026-12-31"


class OnboardingCompleteRequest(BaseModel):
    editing_experience: str | None = None  # "noob" | "rookie" | "pro"
    creation_reason: str | None = None
    primary_channel_id: str | None = None


@router.get("")
def list_channels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    channels = (
        db.query(ConnectedChannel)
        .filter(ConnectedChannel.user_id == user.id)
        .order_by(ConnectedChannel.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(ch.id),
            "platform": ch.platform,
            "channelId": ch.channel_id,
            "channelTitle": ch.channel_title,
            "thumbnailUrl": ch.thumbnail_url,
            "goals": ch.goals or {},
            "createdAt": ch.created_at.isoformat() if ch.created_at else None,
        }
        for ch in channels
    ]


@router.post("/connect")
def connect_channel(
    req: ChannelConnectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not req.channel_id or not req.channel_title:
        raise HTTPException(400, "channel_id and channel_title are required")

    existing = (
        db.query(ConnectedChannel)
        .filter(
            ConnectedChannel.user_id == user.id,
            ConnectedChannel.platform == req.platform,
            ConnectedChannel.channel_id == req.channel_id,
        )
        .first()
    )

    if existing:
        existing.channel_title = req.channel_title
        if req.thumbnail_url:
            existing.thumbnail_url = req.thumbnail_url
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        ch = existing
    else:
        ch = ConnectedChannel(
            id=uuid.uuid4(),
            user_id=user.id,
            platform=req.platform,
            channel_id=req.channel_id,
            channel_title=req.channel_title,
            thumbnail_url=req.thumbnail_url,
            created_at=datetime.utcnow(),
        )
        db.add(ch)
        db.commit()
        db.refresh(ch)

    return {
        "id": str(ch.id),
        "platform": ch.platform,
        "channelId": ch.channel_id,
        "channelTitle": ch.channel_title,
        "thumbnailUrl": ch.thumbnail_url,
        "goals": ch.goals or {},
    }


@router.put("/{channel_id}/goals")
def update_channel_goals(
    channel_id: str,
    req: ChannelGoalsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = (
        db.query(ConnectedChannel)
        .filter(ConnectedChannel.user_id == user.id, ConnectedChannel.channel_id == channel_id)
        .first()
    )
    if not ch:
        try:
            ch_uuid = uuid.UUID(channel_id)
            ch = (
                db.query(ConnectedChannel)
                .filter(ConnectedChannel.user_id == user.id, ConnectedChannel.id == ch_uuid)
                .first()
            )
        except ValueError:
            pass

    if not ch:
        raise HTTPException(404, "Channel not found")

    ch.goals = {
        "targetViews": req.target_views,
        "targetSubs": req.target_subs,
        "targetDate": req.target_date,
    }
    ch.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ch)

    return {
        "id": str(ch.id),
        "channelId": ch.channel_id,
        "channelTitle": ch.channel_title,
        "goals": ch.goals,
    }


@router.post("/onboarding/complete")
def complete_onboarding(
    req: OnboardingCompleteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.onboarding_completed = True
    if req.editing_experience:
        user.editing_experience = req.editing_experience
    if req.creation_reason is not None:
        user.creation_reason = req.creation_reason
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "onboardingCompleted": True,
        "editingExperience": user.editing_experience,
        "creationReason": user.creation_reason,
    }
