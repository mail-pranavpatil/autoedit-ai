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
- `WORKER_CONCURRENCY` **must be `1`** on any worker plan under ~2 GB RAM. Each render spawns multiple sequential ffmpeg processes (B-roll pre-render → concat → final filter_complex); two concurrent renders easily exhaust container memory, causing the kernel OOM killer to SIGKILL any ffmpeg — even trivially light ones like the black-gap generator. The symptom is `gap_f0.mp4 died with <Signals.SIGKILL: 9>` during the `RENDERING` stage. Set `WORKER_CONCURRENCY=2` only when on an instance plan with ≥ 2 GB RAM. `render.yaml` puts `autoedit-worker` on `standard` (1 CPU/2GB) specifically because 400-600MB source videos were OOM-killing the old combined starter (512MB) container even at concurrency 1 — watch the per-stage RSS logs (`pipeline._set_status`) to see whether this plan is actually big enough for your source files.
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

### Object storage (R2) — required for the split API/worker layout

`autoedit-api` and `autoedit-worker` no longer share a disk — each render's
source/thumbnail/final output/B-roll cache goes through
`services/autoedit/object_storage.py` to Cloudflare R2 (`STORAGE_BACKEND=r2`),
which both services read/write independently. Local disk on the worker is now
a pure ephemeral L1 cache (redownloaded from R2 on a cache miss), not the
source of truth. Set `R2_BUCKET`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY` on **both** services (dashboard, `sync: false`).
`STORAGE_BACKEND` defaults to `local` — leave it unset for local dev
(`docker compose up`), so `object_storage.py`'s functions are no-ops and
everything behaves exactly as before this split.

Videos processed before this split still have local-disk paths in the
database and won't be downloadable/streamable after cutover (no data
migration was run) — re-process them if needed.

---

## Deploy via `render.yaml` (Blueprint)

`render.yaml` defines: managed Postgres + Redis, `autoedit-api` (FastAPI,
no disk), `autoedit-worker` (Celery, no disk), `autoedit-web` (Next.js proxy).

1. **Fork/repo on GitHub** connected to your Render account.
2. Render Dashboard → **New** → **Blueprint** → pick the repo → Render reads
   `render.yaml` → **Apply**. It creates all five resources.
   - If the validator rejects `type: redis`, change it to `type: keyvalue`.
   - Create an R2 bucket + API token (Cloudflare dashboard → R2) before this
     step if you don't have one yet — you'll need the bucket name, endpoint,
     and access key/secret for step 3.
3. First deploy will be **unhealthy** until you fill the `sync: false` vars
   on **both** `autoedit-api` and `autoedit-worker` (R2/`TOKEN_ENCRYPTION_KEY`/
   Google creds are needed on both; the rest per the table):
   | Key | Value | Service(s) |
   |---|---|---|
   | `TOKEN_ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"` | both |
   | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | from Google Cloud console OAuth client | both |
   | `GOOGLE_REDIRECT_URI` | `https://<autoedit-web URL>/api/auth/callback` | api |
   | `FRONTEND_URL` | `https://<autoedit-web URL>` | api |
   | `R2_BUCKET`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | from your R2 bucket | both |
   | `OPENAI_API_KEY`, `PEXELS_API_KEY`, `APIFY_API_TOKEN` | your keys | worker |
4. Google Cloud console → the OAuth client → Authorized redirect URIs, add:
   `https://<autoedit-web URL>/api/auth/callback` **and** `autoedit://auth/callback`.
5. **Manual Deploy** → *Clear build cache & deploy* on `autoedit-api`, then
   `autoedit-worker`, then `autoedit-web`.
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
