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
    # A wedged transaction (lock contention, stuck autovacuum) can otherwise
    # hang a commit forever with no exception raised — a video parked at
    # RENDERING/97% for hours with nothing in the logs.
    connect_args={"options": "-c statement_timeout=30000"},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
