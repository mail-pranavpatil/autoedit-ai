from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "production"
    frontend_url: str = "https://autoedit-web.onrender.com"
    api_url: str = "https://autoedit-api.onrender.com"
    session_secret: str = "change-me-to-a-long-random-string"
    token_encryption_key: str = ""

    database_url: str = "postgresql://autoedit:autoedit@localhost:5432/autoedit"
    redis_url: str = "redis://localhost:6379/0"
    worker_concurrency: int = 4

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "https://autoedit-web.onrender.com/api/auth/callback"
    # Session cookie: set true once served over HTTPS behind a single origin.
    cookie_secure: bool = True
    # Custom URL scheme the iOS shell registers; the mobile OAuth callback
    # redirects to "<scheme>://auth/callback?token=..." instead of setting a cookie.
    ios_redirect_scheme: str = "autoedit"

    openai_api_key: str = ""
    transcription_provider: str = "openai"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    pexels_api_key: str = ""

    # Jina reranker (optional multimodal image ranking layer; OFF by default)
    jina_api_key: str = ""
    enable_jina_reranker: bool = False
    jina_model: str = "jina-reranker-m0"
    jina_max_candidates: int = 30
    jina_timeout_seconds: float = 25.0

    # Dense per-phrase web-image B-roll (Apify Google Images). Kill-switch:
    # enable_dense_broll=false falls back to the old sparse Pexels behaviour.
    enable_dense_broll: bool = True
    apify_api_token: str = ""
    apify_image_actor: str = "hooli~google-images-scraper"
    apify_results_per_query: int = 15
    apify_timeout_seconds: float = 180.0
    # Per-phrase image-query planner. One call per video; gpt-4o follows the
    # coverage + on-subject rules much better than a mini model.
    broll_query_model: str = "gpt-4o"

    storage_dir: Path = Path("./storage")
    assets_dir: Path = Path("./assets")
    sfx_debug: bool = False
    sfx_allow_unverified_licenses: bool | None = None

    # "local" (default) keeps every media file on STORAGE_DIR, unchanged from
    # today - zero setup for local dev. "r2" uploads to Cloudflare R2 (or any
    # S3-compatible endpoint) instead, so the API and worker no longer need a
    # shared disk. See services/autoedit/object_storage.py.
    storage_backend: str = "local"
    r2_bucket: str = ""
    r2_endpoint: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""

    # Final render is a single huge filter_complex with ~10 concurrent video
    # decoders. Default frame-threaded decoding allocates threads x ref-frames of
    # full-res buffers per decoder, which OOM-kills memory-capped containers
    # (SIGKILL 9). Cap decoder / filtergraph / encoder threads to keep peak RAM
    # bounded. Raise this on hosts with plenty of memory to speed rendering up.
    # Email verification (SMTP or Resend)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Eren AI <noreply@autoedit.ai>"
    smtp_use_tls: bool = True
    resend_api_key: str = ""

    render_ffmpeg_threads: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
