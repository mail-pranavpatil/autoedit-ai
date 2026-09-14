from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from cryptography.fernet import Fernet, InvalidToken

from autoedit.config import get_settings

COOKIE_NAME = "autoedit_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 14


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_token(user_id: str) -> str:
    secret = get_settings().session_secret
    body = json.dumps({"uid": user_id, "exp": int(time.time()) + SESSION_TTL_SECONDS})
    encoded = base64.urlsafe_b64encode(body.encode()).decode()
    return f"{encoded}.{_sign(encoded, secret)}"


def read_session_token(token: str) -> str | None:
    secret = get_settings().session_secret
    try:
        encoded, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _sign(encoded, secret)):
        return None
    try:
        body = json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())
    except Exception:
        return None
    if int(body.get("exp", 0)) < int(time.time()):
        return None
    return str(body.get("uid") or "") or None


def create_oauth_state(platform: str = "web", **kwargs) -> str:
    """Signed OAuth `state`. Carries the caller platform ("web" | "ios") with
    integrity so the callback can trust it, plus a nonce so states are unique.
    """
    secret = get_settings().session_secret
    payload = {"p": platform or "web", "n": secrets.token_urlsafe(8)}
    payload.update(kwargs)
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"{encoded}.{_sign(encoded, secret)}"



def read_oauth_state(token: str) -> dict | None:
    secret = get_settings().session_secret
    try:
        encoded, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _sign(encoded, secret)):
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())
    except Exception:
        return None


def _fernet() -> Fernet:
    settings = get_settings()
    key = settings.token_encryption_key
    if not key:
        digest = hashlib.sha256(settings.session_secret.encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    raw = key.encode() if isinstance(key, str) else key
    if len(raw) != 44:
        digest = hashlib.sha256(raw).digest()
        raw = base64.urlsafe_b64encode(digest)
    return Fernet(raw)


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt stored token") from exc


def hash_file(path: str, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()
