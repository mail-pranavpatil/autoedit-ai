from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    frontend_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    session_secret: str = "change-me-to-a-long-random-string"
    token_encryption_key: str = ""

    database_url: str = "postgresql://autoedit:autoedit@localhost:5432/autoedit"
    redis_url: str = "redis://localhost:6379/0"
    worker_concurrency: int = 4

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/api/auth/callback"

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
    jina_timeout_seconds: float = 10.0

    storage_dir: Path = Path("./storage")
    assets_dir: Path = Path("./assets")
    sfx_debug: bool = False
    sfx_allow_unverified_licenses: bool | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
