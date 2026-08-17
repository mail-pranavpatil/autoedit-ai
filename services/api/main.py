from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from autoedit.config import get_settings
from autoedit.db import SessionLocal
from autoedit.logging_setup import setup_logging
from autoedit.seed import seed_system_assets
from api.routes import assets, auth, drive, health, media, projects, settings as settings_routes, videos

setup_logging()
logger = logging.getLogger("autoedit")
settings = get_settings()

app = FastAPI(title="AutoEdit AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rate: dict[str, list[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = [t for t in _rate[ip] if now - t < 60]
        if len(window) > 120:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        window.append(now)
        _rate[ip] = window
    return await call_next(request)


@app.on_event("startup")
def startup():
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.assets_dir.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        seed_system_assets(db)
    finally:
        db.close()
    logger.info("api_started")


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(drive.router)
app.include_router(videos.router)
app.include_router(assets.router)
app.include_router(settings_routes.router)
app.include_router(media.router)
