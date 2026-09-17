from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from autoedit.auth import (
    exchange_code,
    get_current_user,
    get_valid_access_token,
    google_auth_url,
    upsert_drive_connection,
    verify_supabase_jwt,
)
from autoedit.config import get_settings
from autoedit.db import get_db
from autoedit.models import ChannelStatsSnapshot, ConnectedChannel, User
from autoedit.security import create_oauth_state, read_oauth_state
from autoedit.youtube import fetch_user_youtube_channels

logger = logging.getLogger("autoedit")

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("/youtube/connect")
def connect_youtube_oauth(token: str, platform: str | None = None, db: Session = Depends(get_db)):
    """Start the Drive/YouTube data-access consent flow for an already
    logged-in (Supabase) user. Hit via a bare browser redirect (ASWebAuthenticationSession
    on iOS), so identity can't ride an Authorization header - the caller's
    current Supabase access token is passed as `token` instead and carried
    through the signed oauth `state` for the callback below to trust.
    """
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(500, "GOOGLE_CLIENT_ID is not configured")
    user_id = verify_supabase_jwt(token)
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(401, "User not found")
    state = create_oauth_state("ios" if platform == "ios" else "web", user_id=str(user_id))
    return RedirectResponse(google_auth_url(state))


@router.get("/youtube/callback")
def youtube_connect_callback(
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    parsed_state = read_oauth_state(state) if state else None
    is_ios = bool(parsed_state and parsed_state.get("p") == "ios")

    def _redirect(path: str) -> RedirectResponse:
        if is_ios:
            return RedirectResponse(f"{settings.ios_redirect_scheme}://{path}")
        return RedirectResponse(f"{settings.frontend_url}/{path}")

    user_id = parsed_state.get("user_id") if parsed_state else None
    if error or not code or not user_id:
        logger.warning("YouTube connect callback error=%s code_present=%s", error, bool(code))
        return _redirect(f"channels/youtube/connected?error={error or 'oauth'}")

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        return _redirect("channels/youtube/connected?error=oauth_failed")

    try:
        tokens = exchange_code(code)
        upsert_drive_connection(db, user, tokens)

        yt_channels = fetch_user_youtube_channels(tokens["access_token"])
        for ch in yt_channels:
            existing = (
                db.query(ConnectedChannel)
                .filter(ConnectedChannel.user_id == user.id, ConnectedChannel.channel_id == ch["channelId"])
                .first()
            )
            if existing:
                existing.channel_title = ch["channelTitle"]
                if ch.get("thumbnailUrl"):
                    existing.thumbnail_url = ch["thumbnailUrl"]
                existing.updated_at = datetime.utcnow()
            else:
                db.add(
                    ConnectedChannel(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        platform="youtube",
                        channel_id=ch["channelId"],
                        channel_title=ch["channelTitle"],
                        thumbnail_url=ch.get("thumbnailUrl"),
                        created_at=datetime.utcnow(),
                    )
                )
        db.commit()
        return _redirect("channels/youtube/connected")
    except Exception as e:
        logger.error("YouTube connect callback failed: %s", e, exc_info=True)
        return _redirect("channels/youtube/connected?error=oauth_failed")


@router.get("/youtube/my-channels")
def get_my_youtube_channels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        token = get_valid_access_token(db, user)
        channels = fetch_user_youtube_channels(token)
        for ch in channels:
            existing = (
                db.query(ConnectedChannel)
                .filter(ConnectedChannel.user_id == user.id, ConnectedChannel.channel_id == ch["channelId"])
                .first()
            )
            if existing:
                existing.channel_title = ch["channelTitle"]
                if ch.get("thumbnailUrl"):
                    existing.thumbnail_url = ch["thumbnailUrl"]
                existing.updated_at = datetime.utcnow()
            else:
                new_ch = ConnectedChannel(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    platform="youtube",
                    channel_id=ch["channelId"],
                    channel_title=ch["channelTitle"],
                    thumbnail_url=ch.get("thumbnailUrl"),
                    created_at=datetime.utcnow(),
                )
                db.add(new_ch)
        db.commit()
        if channels:
            return channels
    except Exception:
        pass

    # Fallback to already stored channels
    channels = (
        db.query(ConnectedChannel)
        .filter(ConnectedChannel.user_id == user.id, ConnectedChannel.platform == "youtube")
        .all()
    )
    return [
        {
            "channelId": ch.channel_id,
            "channelTitle": ch.channel_title,
            "thumbnailUrl": ch.thumbnail_url,
            "subscriberCount": (ch.goals or {}).get("lastSubs", 0),
        }
        for ch in channels
    ]



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


def _find_channel(db: Session, user: User, channel_id: str) -> ConnectedChannel | None:
    """Look up a connected channel by its platform channel_id, falling back to our own row id."""
    ch = (
        db.query(ConnectedChannel)
        .filter(ConnectedChannel.user_id == user.id, ConnectedChannel.channel_id == channel_id)
        .first()
    )
    if ch:
        return ch
    try:
        ch_uuid = uuid.UUID(channel_id)
    except ValueError:
        return None
    return (
        db.query(ConnectedChannel)
        .filter(ConnectedChannel.user_id == user.id, ConnectedChannel.id == ch_uuid)
        .first()
    )


def _compute_channel_progress(goals: dict) -> dict:
    """Real progress toward a channel's goals, from cached live stats + elapsed time.

    Returns {} when there isn't enough saved data (no target/deadline yet) to
    compute anything meaningful.
    """
    target_views = goals.get("targetViews")
    target_subs = goals.get("targetSubs")
    target_date_str = goals.get("targetDate")
    current_views = goals.get("lastViews")
    current_subs = goals.get("lastSubs")

    if not target_date_str or (target_views is None and target_subs is None):
        return {}

    try:
        target_date = datetime.fromisoformat(target_date_str)
    except (ValueError, TypeError):
        return {}

    start_date_str = goals.get("targetStartDate")
    start_date = datetime.fromisoformat(start_date_str) if start_date_str else target_date - timedelta(days=90)

    total_seconds = (target_date - start_date).total_seconds()
    elapsed_seconds = (datetime.utcnow() - start_date).total_seconds()
    expected_fraction = max(0.0, min(1.0, elapsed_seconds / total_seconds)) if total_seconds > 0 else 1.0

    views_progress = current_views / target_views if target_views and current_views is not None else None
    subs_progress = current_subs / target_subs if target_subs and current_subs is not None else None

    result: dict[str, Any] = {
        "currentViews": current_views,
        "currentSubs": current_subs,
        "viewsProgressPct": round(views_progress * 100, 1) if views_progress is not None else None,
        "subsProgressPct": round(subs_progress * 100, 1) if subs_progress is not None else None,
    }

    progresses = [p for p in (views_progress, subs_progress) if p is not None]
    if progresses:
        actual_fraction = sum(progresses) / len(progresses)
        result["velocityPercent"] = (
            round(((actual_fraction - expected_fraction) / expected_fraction) * 100, 1)
            if expected_fraction > 0.001
            else 0.0
        )
        if actual_fraction >= expected_fraction + 0.03:
            result["pacingLabel"] = "Pacing Ahead"
        elif actual_fraction <= expected_fraction - 0.03:
            result["pacingLabel"] = "Pacing Behind"
        else:
            result["pacingLabel"] = "On Track"

    return result


@router.get("")
def list_channels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    channels = (
        db.query(ConnectedChannel)
        .filter(ConnectedChannel.user_id == user.id)
        .order_by(ConnectedChannel.created_at.asc())
        .all()
    )

    live_stats: dict[str, dict] = {}
    try:
        token = get_valid_access_token(db, user)
        for ch_stats in fetch_user_youtube_channels(token):
            live_stats[ch_stats["channelId"]] = ch_stats
    except Exception:
        pass

    result = []
    for ch in channels:
        goals = dict(ch.goals or {})
        live = live_stats.get(ch.channel_id)
        if live:
            goals["lastViews"] = live["viewCount"]
            goals["lastSubs"] = live["subscriberCount"]
            goals["statsUpdatedAt"] = datetime.utcnow().isoformat()
            ch.goals = goals
            ch.updated_at = datetime.utcnow()

            last_snapshot = (
                db.query(ChannelStatsSnapshot)
                .filter(ChannelStatsSnapshot.channel_id == ch.id)
                .order_by(ChannelStatsSnapshot.captured_at.desc())
                .first()
            )
            if not last_snapshot or last_snapshot.captured_at < datetime.utcnow() - timedelta(hours=12):
                db.add(
                    ChannelStatsSnapshot(
                        id=uuid.uuid4(),
                        channel_id=ch.id,
                        views=live["viewCount"],
                        subscribers=live["subscriberCount"],
                        video_count=live["videoCount"],
                        captured_at=datetime.utcnow(),
                    )
                )

        result.append({
            "id": str(ch.id),
            "platform": ch.platform,
            "channelId": ch.channel_id,
            "channelTitle": ch.channel_title,
            "thumbnailUrl": ch.thumbnail_url,
            "goals": goals,
            "createdAt": ch.created_at.isoformat() if ch.created_at else None,
            **_compute_channel_progress(goals),
        })

    if live_stats:
        db.commit()

    return result


@router.get("/{channel_id}/history")
def get_channel_history(
    channel_id: str,
    days: int = 30,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = _find_channel(db, user, channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")

    since = datetime.utcnow() - timedelta(days=days)
    snapshots = (
        db.query(ChannelStatsSnapshot)
        .filter(ChannelStatsSnapshot.channel_id == ch.id, ChannelStatsSnapshot.captured_at >= since)
        .order_by(ChannelStatsSnapshot.captured_at.asc())
        .all()
    )
    return [
        {
            "capturedAt": s.captured_at.isoformat(),
            "views": s.views,
            "subscribers": s.subscribers,
            "videoCount": s.video_count,
        }
        for s in snapshots
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
    ch = _find_channel(db, user, channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")

    existing_goals = ch.goals or {}
    ch.goals = {
        **existing_goals,
        "targetViews": req.target_views,
        "targetSubs": req.target_subs,
        "targetDate": req.target_date,
        "targetStartDate": existing_goals.get("targetStartDate") or datetime.utcnow().isoformat(),
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
