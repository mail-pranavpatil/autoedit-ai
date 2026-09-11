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
- `RENDER_FFMPEG_THREADS` (default `1`) caps ffmpeg decoder/filter/encoder threads on the worker. The final render is one large `filter_complex` with ~10 concurrent video decoders; leaving threads uncapped OOM-kills small instances (job fails with `ffmpeg ... died with <Signals.SIGKILL: 9>`). Raise to `2`–`4` only on worker plans with several GB of RAM.
- Local Docker Compose continues to work for development/testing.
- Object storage is required for durable result delivery.
- Never use Docker-specific hostnames in Render env; always use full URLs from providers.

---

## Limitations/Caveats

- Free Render services may not provide sufficient resources for continuous video rendering or prompt execution of heavy AI tasks.
- Local storage is ephemeral; upload user-generated output to persistent object store for production reliability.

---

## Single-origin layout (required for the iOS shell)

The `apps/mobile` WebView shell — and any deploy where web and API are on
different hosts under a public suffix like `onrender.com` — needs the session
cookie to be **same-site**. Serve everything behind one hostname:

- Web service env: `NEXT_PUBLIC_API_URL=""` (browser calls `/api/*` same-origin)
  and `API_PROXY_ORIGIN=<internal API url>`. `apps/web/next.config.js` rewrites
  `/api/:path*` and `/health` to that origin.
- API/worker env: `COOKIE_SECURE=true`, `IOS_REDIRECT_SCHEME=autoedit`,
  `GOOGLE_REDIRECT_URI=https://<web-domain>/api/auth/callback`,
  `FRONTEND_URL=https://<web-domain>`.
- Google OAuth client: authorize `https://<web-domain>/api/auth/callback` and
  `autoedit://auth/callback`.

### Durable storage without object storage (single-user)

Render disks attach to one service, so the multi-service split above can't share
rendered files without S3/GCS/R2. So the API and the Celery worker run in **one
container** (`docker/start-combined.sh`) sharing **one persistent disk** at
`/data` (`STORAGE_DIR=/data/storage`, `ASSETS_DIR=/data/assets`). Split them back
out and wire object storage when render throughput or multi-instance forces it.

---

## Deploy via `render.yaml` (Blueprint)

`render.yaml` defines exactly this: managed Postgres + Redis, `autoedit`
(FastAPI + Celery, with the disk), `autoedit-web` (Next.js proxy).

1. **Fork/repo on GitHub** connected to your Render account.
2. Render Dashboard → **New** → **Blueprint** → pick the repo → Render reads
   `render.yaml` → **Apply**. It creates all four resources.
   - If the validator rejects `type: redis`, change it to `type: keyvalue`.
   - The persistent disk needs the API service on a **paid** instance
     (`starter`, ~$7/mo). To stay free: delete the `disk:` block and set
     `STORAGE_DIR=/tmp/storage` — finished reels are then lost on every
     restart/redeploy (DB rows survive; a re-render re-fetches source + B-roll).
3. First deploy will be **unhealthy** until you fill the `sync: false` vars:
   Dashboard → `autoedit` → Environment →
   | Key | Value |
   |---|---|
   | `TOKEN_ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"` |
   | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | from Google Cloud console OAuth client |
   | `GOOGLE_REDIRECT_URI` | `https://<autoedit-web URL>/api/auth/callback` |
   | `FRONTEND_URL` | `https://<autoedit-web URL>` |
   | `OPENAI_API_KEY`, `PEXELS_API_KEY`, `APIFY_API_TOKEN` | your keys |
4. Google Cloud console → the OAuth client → Authorized redirect URIs, add:
   `https://<autoedit-web URL>/api/auth/callback` **and** `autoedit://auth/callback`.
5. **Manual Deploy** → *Clear build cache & deploy* on `autoedit`, then
   `autoedit-web`.
6. Verify: `curl https://<autoedit-web URL>/health` → `{"api":true,"redis":true,
   "database":true,"ffmpeg":true}`. Sign in; import a Drive folder; process one
   clip to `READY`; download the reel.

`render.yaml` auto-wires `DATABASE_URL`, `REDIS_URL`, `SESSION_SECRET`
(generated), and `API_PROXY_ORIGIN` (web → API internal address).

**Pitfall already hit and fixed:** Next's `rewrites()` (used for the same-origin
proxy) are resolved into a static manifest at `next build` time, not at
container startup — and Render only passes a service's env vars into `docker
build` for names declared `ARG` in the Dockerfile. `docker/Dockerfile.web`
declares `ARG API_PROXY_ORIGIN` / `ARG NEXT_PUBLIC_API_URL` for this reason. If
you ever see `/health` 500 with `Failed to proxy http://localhost:8000/...` in
the `autoedit-web` logs, this is why — some build-time value wasn't threaded
through as an `ARG`.

### GitHub Actions credentials

**None.** Render deploys by pulling the connected repo directly — nothing goes in
`.github/workflows/`. The iOS workflow (`ios.yml`) also needs no secrets: it's an
unsigned compile check. Secrets only enter the picture for a *signed* iOS build
(TestFlight / device install) — see the plan's Phase 5c.

---

For more details, see root `.env.example`, `decisions.md`, and code comments.
