from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from autoedit.auth import exchange_code, fetch_userinfo, google_auth_url, get_current_user, upsert_user_and_tokens
from autoedit.config import get_settings
from autoedit.db import get_db
from autoedit.models import DriveConnection, User
from autoedit.security import COOKIE_NAME, create_oauth_state, create_session_token, read_oauth_state

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
    is_ios = bool(state and (read_oauth_state(state) or {}).get("p") == "ios")

    if error or not code:
        if is_ios:
            return RedirectResponse(f"{settings.ios_redirect_scheme}://auth/callback?error=oauth")
        return RedirectResponse(f"{settings.frontend_url}/login?error=oauth")

    tokens = exchange_code(code)
    userinfo = fetch_userinfo(tokens["access_token"])
    user = upsert_user_and_tokens(db, tokens, userinfo)
    token = create_session_token(str(user.id))

    if is_ios:
        # The native shell runs this flow in ASWebAuthenticationSession, which has
        # no shared cookie jar. Hand the signed session token back over the custom
        # scheme; the app injects it as the autoedit_session cookie into WKWebView.
        return RedirectResponse(f"{settings.ios_redirect_scheme}://auth/callback?token={token}")

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


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conn = db.query(DriveConnection).filter(DriveConnection.user_id == user.id).first()
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "pictureUrl": user.picture_url,
        "driveConnected": bool(conn),
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
