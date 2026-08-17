from fastapi import APIRouter
from redis import Redis
from sqlalchemy import text

from autoedit.config import get_settings
from autoedit.db import engine
from autoedit.media import ffmpeg_available

router = APIRouter()


@router.get("/health")
@router.get("/api/health")
def health():
    settings = get_settings()
    db_ok = False
    redis_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    try:
        redis_ok = Redis.from_url(settings.redis_url).ping() is True
    except Exception:
        redis_ok = False
    return {
        "api": True,
        "redis": redis_ok,
        "database": db_ok,
        "ffmpeg": ffmpeg_available(),
    }
