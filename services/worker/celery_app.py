from celery import Celery

from autoedit.config import get_settings

settings = get_settings()
celery_app = Celery("autoedit", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_concurrency=settings.worker_concurrency,
    include=["worker.tasks"],
)

celery_app.autodiscover_tasks(["worker"])
