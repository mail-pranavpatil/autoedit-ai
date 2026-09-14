import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from autoedit.config import get_settings
from autoedit.db import get_db
from autoedit.models import DriveConnection, User
from autoedit.security import COOKIE_NAME, decrypt_secret, encrypt_secret, read_session_token

logger = logging.getLogger("autoedit")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.readonly",
    YOUTUBE_READONLY_SCOPE,
    YOUTUBE_UPLOAD_SCOPE,
]



def has_youtube_scope(scopes: str | None) -> bool:
    if not scopes:
        return False
    return YOUTUBE_UPLOAD_SCOPE in scopes.split() or YOUTUBE_UPLOAD_SCOPE in scopes


def google_auth_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    settings = get_settings()
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


def fetch_userinfo(access_token: str) -> dict:
    with httpx.Client(timeout=30) as client:
        resp = client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        resp.raise_for_status()
        return resp.json()


def upsert_user_and_tokens(db: Session, token_payload: dict, userinfo: dict) -> User:
    email = userinfo.get("email")
    sub = userinfo.get("sub")
    if not email or not sub:
        raise HTTPException(400, "Google account did not return email")

    user = db.query(User).filter((User.google_sub == sub) | (User.email == email)).first()
    if not user:
        user = User(id=uuid.uuid4(), email=email, google_sub=sub)
        db.add(user)
    user.email = email
    user.google_sub = sub
    user.name = userinfo.get("name")
    user.picture_url = userinfo.get("picture")
    user.is_verified = True
    user.updated_at = datetime.utcnow()
    db.flush()

    access = token_payload.get("access_token")
    refresh = token_payload.get("refresh_token")
    expires_in = int(token_payload.get("expires_in") or 3600)
    conn = db.query(DriveConnection).filter(DriveConnection.user_id == user.id).first()
    if not conn:
        conn = DriveConnection(user_id=user.id, provider="google", access_token_encrypted=encrypt_secret(access or ""))
        db.add(conn)
    conn.access_token_encrypted = encrypt_secret(access or "")
    if refresh:
        conn.refresh_token_encrypted = encrypt_secret(refresh)
    conn.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
    conn.scopes = token_payload.get("scope")
    conn.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def refresh_access_token(db: Session, conn: DriveConnection) -> str:
    if not conn.refresh_token_encrypted:
        raise HTTPException(401, "Google Drive access was revoked. Sign in again.")
    settings = get_settings()
    refresh = decrypt_secret(conn.refresh_token_encrypted)
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code >= 400:
            logger.warning("Google token refresh failed: %s", resp.text)
            raise HTTPException(401, "Google Drive access was revoked. Sign in again.")
        payload = resp.json()
    access = payload["access_token"]
    conn.access_token_encrypted = encrypt_secret(access)
    expires_in = int(payload.get("expires_in") or 3600)
    conn.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
    db.commit()
    return access


def get_valid_access_token(db: Session, user: User) -> str:
    conn = db.query(DriveConnection).filter(DriveConnection.user_id == user.id).first()
    if not conn:
        raise HTTPException(401, "Connect Google Drive by signing in.")
    if conn.token_expiry and conn.token_expiry > datetime.utcnow() + timedelta(seconds=30):
        return decrypt_secret(conn.access_token_encrypted)
    return refresh_access_token(db, conn)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash or ":" not in stored_hash:
        return False
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Not signed in")
    user_id = read_session_token(token)
    if not user_id:
        raise HTTPException(401, "Session expired")
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user
