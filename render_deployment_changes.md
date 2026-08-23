# AutoEdit AI — Render Deployment Changes

## Objective

Modify the existing AutoEdit AI repository so that it can be deployed reliably on Render as separate services.

The repository currently uses Docker Compose for local development with:

* PostgreSQL
* Redis
* API
* Celery worker
* YouTube Celery worker
* Next.js web application

Do **not** destroy or unnecessarily modify the existing local Docker Compose development workflow.

The goal is to make the project production-ready for Render while keeping local development working.

---

# 1. Current Architecture

Current services:

```text
postgres
redis
api
worker
youtube-worker
web
```

Current files:

```text
docker/
├── Dockerfile.api
├── Dockerfile.web
└── Dockerfile.worker

docker-compose.yml
apps/web/
services/
packages/
alembic/
```

The current Docker Compose setup uses Docker-internal hostnames:

```text
postgres
redis
api
```

These must NOT be used for Render production deployments.

---

# 2. Render Target Architecture

Prepare the repository for this Render architecture:

```text
                    Internet
                       │
                       ▼
                ┌─────────────┐
                │ autoedit-web│
                │   Next.js   │
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │ autoedit-api│
                │   FastAPI   │
                └──────┬──────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        PostgreSQL              Redis
             │                   │
             └─────────┬─────────┘
                       ▼
                Celery Workers
                ├── worker
                └── youtube-worker
```

Render services should be:

```text
autoedit-web
autoedit-api
autoedit-worker
autoedit-youtube-worker
```

PostgreSQL should use Render PostgreSQL or another managed PostgreSQL provider.

Redis should use a managed Redis-compatible provider.

---

# 3. Fix Dockerfile.web

Current Dockerfile.web uses:

```dockerfile
CMD ["npm", "run", "dev"]
```

This is a development server and should not be used for production.

Modify `docker/Dockerfile.web` to use a production Next.js build.

Use this structure:

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY apps/web/package.json /app/

RUN npm install

COPY apps/web /app

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]
```

Before making this change, inspect `apps/web/package.json`.

Confirm that:

```text
npm run build
```

exists.

Confirm that:

```text
npm run start
```

exists.

If the project uses a different package manager or build system, adapt the Dockerfile accordingly rather than blindly replacing it.

---

# 4. Fix Next.js Production Configuration

Inspect the Next.js application.

Make sure the production application listens on:

```text
0.0.0.0
```

and port:

```text
3000
```

Do not hardcode localhost URLs into production code.

---

# 5. API URL Configuration

The current Docker Compose configuration contains:

```text
API_URL=http://api:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

These are local Docker development values.

Do not remove them from local Docker Compose unless necessary.

Instead, make the web application configurable through environment variables.

Production Render values should be supplied through Render environment variables.

Expected production setup:

```text
NEXT_PUBLIC_API_URL=https://<autoedit-api-render-url>
```

The exact Render URL should NOT be hardcoded into source code.

---

# 6. API Dockerfile

Inspect:

```text
docker/Dockerfile.api
```

The API must:

1. Install FFmpeg.
2. Install Python dependencies.
3. Include the required application source.
4. Run database migrations.
5. Start FastAPI/Uvicorn.
6. Listen on `0.0.0.0`.
7. Respect the Render `PORT` environment variable if practical.

Current command:

```text
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Make it production-safe.

Prefer:

```text
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

if shell expansion is used correctly.

Do not break local Docker Compose.

---

# 7. Render API Port

The API must expose an HTTP server.

Expected local port:

```text
8000
```

Expected Render behavior:

```text
PORT=8000
```

The application must bind to:

```text
0.0.0.0
```

Never bind production API to:

```text
127.0.0.1
localhost
```

---

# 8. Remove Docker-Internal Production Dependencies

The following values are only valid inside Docker Compose:

```text
postgres
redis
api
```

Do not use these as production hostnames.

Current:

```text
DATABASE_URL=postgresql://autoedit:autoedit@postgres:5432/autoedit
```

Current:

```text
REDIS_URL=redis://redis:6379/0
```

These must become environment variables in production.

The code should read:

```text
DATABASE_URL
REDIS_URL
```

from the environment.

Do not hardcode production credentials.

---

# 9. Database Configuration

Inspect the entire codebase for:

```text
DATABASE_URL
```

Make sure every database connection uses the environment variable.

The production database URL will be supplied by Render.

Example:

```text
DATABASE_URL=<managed-postgresql-url>
```

Do NOT commit the production database URL.

Do NOT hardcode:

```text
autoedit
autoedit
postgres
5432
```

into production code.

The local Docker Compose values may remain in `docker-compose.yml`.

---

# 10. Redis Configuration

Inspect the codebase for:

```text
REDIS_URL
```

Celery must use the environment variable.

Do not hardcode:

```text
redis://redis:6379/0
```

into application code.

Local Docker Compose may continue using:

```text
redis://redis:6379/0
```

Production Render will provide a real Redis URL.

---

# 11. Celery Worker

Inspect:

```text
docker/Dockerfile.worker
```

Make sure it contains everything required by:

```text
worker.celery_app
```

The worker must be able to run:

```bash
celery -A worker.celery_app worker --loglevel=info --concurrency=2 -Q celery
```

Production worker configuration must use:

```text
DATABASE_URL
REDIS_URL
STORAGE_DIR
ASSETS_DIR
```

from environment variables.

Do not hardcode Docker service names.

---

# 12. YouTube Worker

The YouTube worker must be independently deployable.

It should run:

```bash
celery -A worker.celery_app worker --loglevel=info --concurrency=1 -Q youtube
```

It must use the same production:

```text
DATABASE_URL
REDIS_URL
```

as the main worker.

Do not require:

```text
postgres
redis
```

as hardcoded hostnames.

---

# 13. Worker Storage

The existing Docker Compose uses:

```text
./storage:/data/storage
./assets:/data/assets
```

Do not assume these local Docker volumes are persistent on Render.

Render instances have ephemeral filesystems unless persistent storage is specifically configured.

Therefore:

* Temporary video files may be stored locally during processing.
* Final user-generated videos should NOT rely on local Render filesystem persistence.
* Final assets should be uploaded to persistent object storage.

The application should support an architecture like:

```text
Render Worker
     │
     ▼
/data/storage
     │
     ▼
Process video
     │
     ▼
Upload final result
     │
     ▼
Persistent Object Storage
```

Use the project's existing storage abstraction if one already exists.

Do not introduce a completely new storage system unless necessary.

---

# 14. Storage Environment Variables

Inspect the existing project for storage configuration.

If the project already supports:

```text
STORAGE_DIR
ASSETS_DIR
```

keep these.

If persistent object storage is already implemented, make sure its credentials are environment variables.

Never commit:

* access keys
* secret keys
* bucket credentials
* API tokens

---

# 15. Database Migrations

The API currently runs:

```text
alembic upgrade head
```

before starting Uvicorn.

Keep this behavior if it is safe for the application.

However, ensure that:

1. The database is reachable.
2. The migration command can run using `DATABASE_URL`.
3. Multiple Render API instances would not cause unsafe migration races.

For the initial single-instance Render deployment, this is acceptable.

Do not remove Alembic.

---

# 16. Health Endpoints

Inspect the API.

Create or verify:

```text
GET /health
```

It should return a lightweight successful response such as:

```json
{
  "status": "ok"
}
```

Do not make the health endpoint perform expensive video processing.

If practical, also provide a deeper health endpoint for:

```text
database
redis
```

but keep `/health` lightweight.

---

# 17. CORS

Inspect the FastAPI CORS configuration.

Production must support the deployed web frontend.

Do not permanently use:

```text
allow_origins=["*"]
```

unless there is a specific reason.

Instead use:

```text
FRONTEND_URL
```

from the environment.

Example:

```text
FRONTEND_URL=https://<autoedit-web-render-url>
```

The API should allow this origin.

Local development must continue supporting:

```text
http://localhost:3000
```

---

# 18. Environment Variable Design

Create/update `.env.example`.

It must document all required production variables WITHOUT containing real secrets.

Example structure:

```env
DATABASE_URL=
REDIS_URL=

FRONTEND_URL=
NEXT_PUBLIC_API_URL=

STORAGE_DIR=/data/storage
ASSETS_DIR=/data/assets

OPENAI_API_KEY=
GEMINI_API_KEY=

WORKER_CONCURRENCY=2
```

Only include variables that are actually used by the project.

First inspect the codebase and determine the complete required list.

Do not invent environment variables that are not needed.

---

# 19. Never Commit Secrets

Check:

```text
.gitignore
```

Ensure it ignores:

```text
.env
.env.*
!.env.example
```

Also make sure existing code does not contain API keys.

Search the entire repository for:

```text
OPENAI_API_KEY
GEMINI_API_KEY
SECRET
PASSWORD
TOKEN
DATABASE_URL
```

Do not expose actual secrets in source code.

---

# 20. Keep Docker Compose Working

Do NOT delete or replace:

```text
docker-compose.yml
```

It should continue to support local development.

Local development should still use:

```text
postgres
redis
api
worker
youtube-worker
web
```

The Render production configuration should be achieved primarily through:

* environment variables
* Dockerfiles
* Render service configuration

rather than destroying the local development architecture.

---

# 21. Add Render Documentation

Create:

```text
RENDER_DEPLOYMENT.md
```

Document the exact Render deployment process.

Include:

## Services

```text
autoedit-web
autoedit-api
autoedit-worker
autoedit-youtube-worker
```

## Dockerfiles

```text
docker/Dockerfile.web
docker/Dockerfile.api
docker/Dockerfile.worker
```

## Required environment variables

Document every required variable.

## Ports

```text
Web: 3000
API: 8000
```

## External services

Document:

```text
PostgreSQL
Redis
Object Storage
```

## Deployment order

Use:

```text
1. PostgreSQL
2. Redis
3. API
4. Worker
5. YouTube Worker
6. Web
```

Explain why the API must know the database and Redis URLs before deployment.

---

# 22. Render Deployment Configuration

If useful, create a Render Blueprint configuration:

```text
render.yaml
```

However, DO NOT create a fake or incomplete configuration.

Only create `render.yaml` if the repository can correctly define the required Render services.

If creating it, clearly separate:

```text
web
api
worker
youtube-worker
```

Do not attempt to define PostgreSQL or Redis as Docker containers.

---

# 23. Production vs Development

The code must clearly distinguish:

```text
Development
```

from:

```text
Production
```

Development:

```text
localhost
Docker service names
hot reload
npm run dev
local volumes
```

Production:

```text
Render URLs
managed PostgreSQL
managed Redis
production Next.js build
no hot reload
environment variables
persistent object storage
```

---

# 24. Video Processing Requirements

The video editor uses FFmpeg.

Confirm that the API/worker Docker image has:

```bash
ffmpeg -version
```

available.

The worker must be able to perform the actual video pipeline.

Do not consider deployment successful merely because the HTTP server starts.

A real video-processing test must be performed.

---

# 25. Final Verification

After making changes, run locally:

```bash
docker compose build
```

Then:

```bash
docker compose up
```

Verify:

```text
PostgreSQL → healthy
Redis → healthy
API → running
Worker → running
YouTube Worker → running
Web → running
```

Test:

```text
GET /health
```

Then perform a real video-generation workflow.

Verify:

```text
1. User opens web application
2. Web application calls API
3. API creates job
4. Celery receives job
5. Worker processes job
6. FFmpeg executes
7. Output video is generated
8. Output is stored persistently
9. API returns result
10. Web application can play/download result
```

---

# 26. Important Render Constraint

Do not assume the free Render tier is suitable for long-running or CPU-heavy video processing.

The architecture must work technically, but heavy production video rendering may require a paid worker/server later.

The initial goal is:

```text
Working public MVP
```

not maximum-scale production infrastructure.

---

# 27. Do Not Make Unnecessary Changes

Before modifying anything:

1. Inspect the existing code.
2. Understand how API, Celery, Redis, PostgreSQL, and storage communicate.
3. Preserve existing functionality.
4. Make the smallest changes required for Render.
5. Do not rewrite the application architecture unnecessarily.
6. Do not change frontend UI.
7. Do not change business logic.
8. Do not remove existing Docker Compose functionality.

---

# 28. Final Deliverables

After completing the work, the repository should contain:

```text
docker/
├── Dockerfile.api
├── Dockerfile.web
└── Dockerfile.worker

docker-compose.yml

.env.example

RENDER_DEPLOYMENT.md

possibly:
render.yaml
```

The final project must:

```text
✓ Build Docker images successfully
✓ Run locally
✓ Start Next.js production server
✓ Start FastAPI
✓ Start Celery worker
✓ Start YouTube worker
✓ Connect to PostgreSQL through DATABASE_URL
✓ Connect to Redis through REDIS_URL
✓ Run Alembic migrations
✓ Support CORS through FRONTEND_URL
✓ Have a health endpoint
✓ Have FFmpeg available
✓ Avoid committed secrets
✓ Be deployable as separate Render services
✓ Preserve local Docker Compose development
```

## Final instruction to the coding agent

Do not just edit the Dockerfiles based on this document.

First inspect the entire repository and understand the existing architecture.

Then implement the minimum required changes.

After making changes:

```text
1. Run relevant tests.
2. Run Docker builds.
3. Verify the web production build.
4. Verify API startup.
5. Verify Celery startup.
6. Verify FFmpeg availability.
7. Check environment-variable usage.
8. Check for hardcoded localhost/Docker hostnames.
9. Check for secrets.
10. Report every changed file and why it was changed.
11. Report any remaining Render-specific limitation.
```

Do not claim Render deployment readiness unless the local production Docker builds succeed.
