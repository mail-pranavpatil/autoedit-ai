# Render Deployment Guide for AutoEdit AI

## Render Services

You will need to deploy the following as **separate Render services**:

- `autoedit-web` (Next.js frontend)
- `autoedit-api` (FastAPI backend)
- `autoedit-worker` (Celery worker for main jobs)
- `autoedit-youtube-worker` (Celery worker for YouTube jobs)

External dependencies (provision on Render or external provider):
- PostgreSQL (managed)
- Redis (managed, compatible)
- Object Storage (for persistent video output; e.g. S3, GCS, or similar)


## Ports
- Web: `3000`
- API: `8000`

---

## Required Environment Variables

The following **must be set per-service** (see `.env.example` for details; do NOT commit credentials):

- `DATABASE_URL` (from managed Postgres)
- `REDIS_URL` (from managed Redis)
- `FRONTEND_URL` (web on Render; e.g. https://autoedit-web.onrender.com)
- `NEXT_PUBLIC_API_URL` (web: should be `https://autoedit-api.onrender.com`)
- `SESSION_SECRET`, `TOKEN_ENCRYPTION_KEY`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `OPENAI_API_KEY`, `PEXELS_API_KEY` (if using AI/b-roll features)
- `STORAGE_DIR`/`ASSETS_DIR` (set to `/data/storage`, `/data/assets` by convention or use object storage integration)

See `.env.example` for a full, annotated list.

---

## Deployment Order

1. PostgreSQL (external, managed)
2. Redis (external, managed)
3. API (`autoedit-api`)
4. Main worker (`autoedit-worker`)
5. YouTube worker (`autoedit-youtube-worker`)
6. Frontend (`autoedit-web`)

**Why this order?**  The API and workers must connect to running/existing database and redis instances. Web should be last so it can reach the API.

---

## Special Notes

- All secrets and connection strings coming from Render, not source code!
- Ensure API/worker images can reach ffmpeg in their environment (installed in Dockerfiles).
- Local Docker Compose continues to work for development/testing.
- Object storage is required for durable result delivery.
- Never use Docker-specific hostnames in Render env; always use full URLs from providers.

---

## Limitations/Caveats

- Free Render services may not provide sufficient resources for continuous video rendering or prompt execution of heavy AI tasks.
- Local storage is ephemeral; upload user-generated output to persistent object store for production reliability.

---

For more details, see root `.env.example`, `decisions.md`, and code comments.
