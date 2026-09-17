import logging
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from autoedit.config import get_settings
from autoedit.db import get_db
from autoedit.models import DriveConnection, User
from autoedit.security import decrypt_secret, encrypt_secret

logger = logging.getLogger("autoedit")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"

# Login identity comes from Supabase now - this Google OAuth flow is only
# ever used post-login, to grant Drive/YouTube data access (see
# services/api/routes/channels.py's /youtube/connect + /youtube/callback).
SCOPES = [
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
        if resp.is_error:
            logger.error("Google token exchange error: status=%d body=%s", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()


def upsert_drive_connection(db: Session, user: User, token_payload: dict) -> None:
    """Attach Drive/YouTube tokens from the connect-flow callback to an
    already-authenticated (Supabase) user."""
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


@lru_cache
def _jwks_client() -> PyJWKClient:
    settings = get_settings()
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True)


def verify_supabase_jwt(token: str) -> uuid.UUID:
    """Decode+verify a Supabase-issued access token, returning the user id
    (the `sub` claim). Supabase signs tokens with the project's JWT signing
    key (ES256/RS256, fetched from its JWKS endpoint by `kid`) rather than a
    static shared secret. Raises HTTPException(401) on any failure."""
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as e:
        logger.warning("Supabase JWT verification failed: %s: %s", type(e).__name__, e)
        raise HTTPException(401, "Session expired")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(401, "Session expired")
    try:
        return uuid.UUID(sub)
    except ValueError:
        raise HTTPException(401, "Session expired")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    else:
        # Plain <img>/<video>/<audio> tags can't set a header. The mobile
        # OAuth-connect redirect (channels.py) passes ?token= explicitly;
        # apps/web mirrors the session into a cookie instead (see
        # components/providers.tsx) so every media route works without each
        # call site resolving a token itself.
        token = request.query_params.get("token") or request.cookies.get("sb_access_token")
    if not token:
        raise HTTPException(401, "Not signed in")
    user_id = verify_supabase_jwt(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user
