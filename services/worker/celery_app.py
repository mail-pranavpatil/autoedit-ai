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
    task_routes={"worker.publish_youtube": {"queue": "youtube"}},
    # Backstop so a hung external call (Whisper, LLM planner, ffmpeg deadlock)
    # can't park a video forever with nothing killing the task. Soft limit
    # raises SoftTimeLimitExceeded inside the task, which the pipeline's
    # except-Exception handlers already catch and turn into a FAILED video;
    # hard limit is a last-resort SIGKILL if that handling itself hangs.
    task_soft_time_limit=5400,
    task_time_limit=5700,
    # The kernel OOM-killer is the only thing that currently reclaims worker
    # memory, reactively, after the container's already in trouble (that's
    # what triggers Render's memory-cap alerts). Recycle a worker child once
    # its RSS creeps past ~300MB instead - checked after each task completes,
    # so it never interrupts an in-progress render.
    worker_max_memory_per_child=300_000,
)

celery_app.autodiscover_tasks(["worker"])
