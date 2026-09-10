#!/usr/bin/env bash
# Runs the FastAPI server AND the Celery worker in ONE container so they share
# the same filesystem (STORAGE_DIR). This is required unless object storage is
# wired: the worker writes the finished reel to /data/storage and the API serves
# it from the same path — separate Render services have separate disks and the
# API would 404.
#
# ponytail: one box, one filesystem, no S3. If either process exits the
# container exits and Render restarts it. Split into separate services + wire
# object storage (S3/GCS/R2) when you outgrow a single instance.
set -euo pipefail

celery -A worker.celery_app worker \
  --loglevel=info -Q celery,youtube \
  --concurrency="${WORKER_CONCURRENCY:-2}" &
CELERY_PID=$!

uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
UVICORN_PID=$!

trap 'kill -TERM "$CELERY_PID" "$UVICORN_PID" 2>/dev/null || true' TERM INT

# Exit (non-zero) as soon as either process dies so Render recycles the container.
wait -n
kill -TERM "$CELERY_PID" "$UVICORN_PID" 2>/dev/null || true
exit 1
