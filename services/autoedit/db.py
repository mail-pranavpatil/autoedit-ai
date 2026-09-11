from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from autoedit.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # Render free Postgres caps at ~5 simultaneous connections.
    # Celery holds one for the full job duration; Uvicorn needs the rest.
    pool_size=3,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
