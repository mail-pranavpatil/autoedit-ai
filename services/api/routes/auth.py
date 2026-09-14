from __future__ import annotations

import base64
import json
import logging
import uuid

logger = logging.getLogger("autoedit")

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from datetime import datetime, timedelta

from autoedit.auth import (
    exchange_code,
    fetch_userinfo,
    google_auth_url,
    get_current_user,
    hash_password,
    upsert_user_and_tokens,
    verify_password,
)
from autoedit.config import get_settings
from autoedit.db import get_db
from autoedit.email_service import generate_verification_code, send_verification_email
from autoedit.models import DriveConnection, User
from autoedit.security import COOKIE_NAME, create_oauth_state, create_session_token, read_oauth_state

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


class ResendCodeRequest(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AppleAuthRequest(BaseModel):
    identity_token: str
    authorization_code: str | None = None
    user_id: str | None = None
    email: str | None = None
    name: str | None = None


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Valid email is required")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.is_verified:
            raise HTTPException(400, "An account with this email already exists")
        user = existing
        user.password_hash = hash_password(req.password)
        if req.name:
            user.name = req.name.strip()
    else:
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=req.name.strip() if req.name else email.split("@")[0],
            password_hash=hash_password(req.password),
            onboarding_completed=False,
            is_verified=False,
        )
        db.add(user)

    code = generate_verification_code()
    user.verification_code = code
    user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    db.refresh(user)

    send_verification_email(user.email, code, user.name)

    return {
        "ok": True,
        "requiresVerification": True,
        "email": user.email,
        "message": f"Verification code sent to {user.email}",
    }


@router.post("/verify-email")
def verify_email(req: VerifyEmailRequest, response: Response, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    code = req.code.strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")

    if not user.is_verified:
        if not user.verification_code or user.verification_code != code:
            raise HTTPException(400, "Invalid verification code")
        if user.verification_code_expires_at and user.verification_code_expires_at < datetime.utcnow():
            raise HTTPException(400, "Verification code expired. Please request a new one.")

        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires_at = None
        db.commit()
        db.refresh(user)

    token = create_session_token(str(user.id))
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 14,
        path="/",
    )
    return {
        "token": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "pictureUrl": user.picture_url,
            "onboardingCompleted": user.onboarding_completed,
            "isVerified": user.is_verified,
        },
    }


@router.post("/resend-code")
def resend_code(req: ResendCodeRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_verified:
        return {"ok": True, "alreadyVerified": True}

    code = generate_verification_code()
    user.verification_code = code
    user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    send_verification_email(user.email, code, user.name)
    return {"ok": True, "message": "Verification code resent"}


@router.post("/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash or not verify_password(user.password_hash, req.password):
        raise HTTPException(401, "Invalid email or password")

    if not user.is_verified:
        code = generate_verification_code()
        user.verification_code = code
        user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=15)
        db.commit()
        send_verification_email(user.email, code, user.name)
        raise HTTPException(403, "Please verify your email address to log in")

    token = create_session_token(str(user.id))
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 14,
        path="/",
    )
    return {
        "token": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "pictureUrl": user.picture_url,
            "onboardingCompleted": user.onboarding_completed,
            "isVerified": user.is_verified,
        },
    }



@router.post("/apple")
def apple_auth(req: AppleAuthRequest, response: Response, db: Session = Depends(get_db)):
    # Parse Apple identity token JWT payload
    sub = req.user_id
    email = req.email
    if req.identity_token:
        try:
            parts = req.identity_token.split(".")
            if len(parts) >= 2:
                # Add padding if needed
                payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
                claims = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
                if not sub:
                    sub = claims.get("sub")
                if not email:
                    email = claims.get("email")
        except Exception:
            pass

    if not sub:
        raise HTTPException(400, "Unable to verify Apple credentials")

    user = None
    if sub:
        user = db.query(User).filter(User.apple_sub == sub).first()
    if not user and email:
        user = db.query(User).filter(User.email == email.lower()).first()

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email.lower() if email else f"{sub}@appleid.apple.com",
            name=req.name or "Apple Creator",
            apple_sub=sub,
            onboarding_completed=False,
            is_verified=True,
        )
        db.add(user)
    else:
        if not user.apple_sub:
            user.apple_sub = sub
        if req.name and not user.name:
            user.name = req.name
        user.is_verified = True

    db.commit()
    db.refresh(user)

    token = create_session_token(str(user.id))
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 14,
        path="/",
    )
    return {
        "token": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "pictureUrl": user.picture_url,
            "onboardingCompleted": user.onboarding_completed,
        },
    }


@router.get("/google")
def start_google(platform: str | None = None):
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(500, "GOOGLE_CLIENT_ID is not configured")
    state = create_oauth_state("ios" if platform == "ios" else "web")
    return RedirectResponse(google_auth_url(state))


@router.get("/callback")
def google_callback(
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    parsed_state = read_oauth_state(state) if state else {}
    is_ios = bool(parsed_state and parsed_state.get("p") == "ios")
    intent = parsed_state.get("intent") if parsed_state else None
    target = "channels/youtube/connected" if intent == "youtube_connect" else "auth/callback"

    if error or not code:
        logger.warning("OAuth callback error=%s code_present=%s", error, bool(code))
        if is_ios:
            return RedirectResponse(f"{settings.ios_redirect_scheme}://{target}?error={error or 'oauth'}")
        return RedirectResponse(f"{settings.frontend_url}/login?error={error or 'oauth'}")

    try:
        tokens = exchange_code(code)
        userinfo = fetch_userinfo(tokens["access_token"])
        user = upsert_user_and_tokens(db, tokens, userinfo)
        token = create_session_token(str(user.id))

        # Auto-fetch and sync user's YouTube channels
        try:
            from autoedit.models import ConnectedChannel
            from autoedit.youtube import fetch_user_youtube_channels

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
        except Exception as yt_err:
            logger.warning("Failed to auto-sync YouTube channels in OAuth callback: %s", yt_err)

        if is_ios:
            return RedirectResponse(f"{settings.ios_redirect_scheme}://{target}?token={token}")

        response = RedirectResponse(f"{settings.frontend_url}/dashboard")
        response.set_cookie(
            COOKIE_NAME,
            token,
            httponly=True,
            samesite="lax",
            secure=settings.cookie_secure,
            max_age=60 * 60 * 24 * 14,
            path="/",
        )
        return response
    except Exception as e:
        logger.error("OAuth code exchange / callback failed: %s", e, exc_info=True)
        if is_ios:
            return RedirectResponse(f"{settings.ios_redirect_scheme}://{target}?error=oauth_failed")
        return RedirectResponse(f"{settings.frontend_url}/login?error=oauth_failed")



@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conn = db.query(DriveConnection).filter(DriveConnection.user_id == user.id).first()
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "pictureUrl": user.picture_url,
        "driveConnected": bool(conn),
        "onboardingCompleted": bool(user.onboarding_completed),
        "editingExperience": user.editing_experience,
        "creationReason": user.creation_reason,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
