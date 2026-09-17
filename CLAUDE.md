# AutoEdit AI — project context for Claude

Paste-and-discuss brief. Covers what the project is, how it's built, and the
**exact stage of development** it's at (as of 2026-09-13).

---

## 1. What it is

A web app that turns a Google Drive folder of raw talking-head clips into
finished 9:16 social reels, in batch, with near-zero user effort:

```
RECORD → UPLOAD TO DRIVE → CLICK PROCESS → DOWNLOAD FINISHED REELS
```

Core principle: **the LLM decides *what* happens, FFmpeg decides *how*.** No LLM
in the render path. Every planner response is validated against a strict Pydantic
schema; FFmpeg is only ever called with argument arrays, never a shell string.

Full product spec lives in `plan.md` (52 sections). This file is the status layer
on top of it.

---

## 2. Architecture

Monorepo:

| Path | What |
|------|------|
| `apps/web` | Next.js + React + TS + Tailwind frontend — secondary surface; login + a handful of screens, most day-to-day usage is the mobile app |
| `apps/mobile` | Flutter app — has grown a full native tab UI (Home/Videos/Goals/Settings, see `lib/features/dashboard`) on top of the original WebView-shell idea; `lib/webview_shell.dart` is unreferenced (no caller anywhere) but kept correct |
| `services/api` | FastAPI app — auth, projects, drive, videos, assets, settings, media, youtube routes |
| `services/worker` | Celery worker (`celery_app.py`, `tasks.py`) |
| `services/autoedit` | **the actual pipeline** — shared by api + worker |
| `supabase/migrations/` | Postgres schema, applied via `supabase db push` (see §2a) |
| `assets/` | real SFX (`assets/sfx/*`) + 3 music tracks (`assets/music/*`) |
| `packages/edit-schema` | JSON schema mirror of the edit plan |
| `docker/` | `Dockerfile.{api,web,worker}` + root `docker-compose.yml` |

Infra: Postgres + Auth via Supabase (state + login/signup), Redis (Celery
queue + job status), FFmpeg/ffprobe in the api and worker images.

### 2a. Auth & database (Supabase)

Login/signup and the Postgres database both live in Supabase now (migrated
2026-09-15 off a self-hosted Postgres + homegrown session/password system):

- **`public.users`** is a profile table keyed off Supabase's own
  `auth.users` (`id uuid references auth.users(id)`), auto-populated by a
  `handle_new_user` trigger on signup — app code never inserts into it
  directly. No password hash, OAuth `sub`, or email-verification columns
  live here anymore; Supabase owns all of that.
- **Backend** (`services/autoedit/auth.py`'s `get_current_user`) only ever
  *verifies* the JWT Supabase issues client-side (`SUPABASE_JWT_SECRET`) — it
  never creates sessions or stores passwords. `services/api/routes/auth.py`
  is trimmed to just `GET /api/auth/me`.
- **Google sign-in is split in two**: Supabase's Google provider handles
  login identity only (mobile: `AuthService.signInWithGoogle()` via
  `supabase.auth.signInWithOAuth`). Drive/YouTube data access is a *separate*
  post-login consent step — `GET /api/channels/youtube/connect` (needs the
  caller's Supabase access token as a `?token=` query param, since it's hit
  via a bare browser redirect that can't carry an Authorization header) →
  `GET /api/channels/youtube/callback` exchanges the code and stores
  encrypted Drive/YouTube tokens against the already-known user id carried in
  the signed oauth `state`.
- **Apple Sign-In** goes through `supabase.auth.signInWithIdToken` (Supabase
  verifies the identity token's signature against Apple's keys — the old
  custom route decoded it without verification).
- **Migrations**: `supabase/migrations/*.sql`, applied with `supabase db
  push` (Supabase CLI, run via `npx supabase ...` if not installed globally).
  Alembic is gone.
- **`DATABASE_URL` must use the connection *pooler*, session mode (port 5432,
  `aws-0-<region>.pooler.supabase.com`), not the direct `db.<ref>.supabase.co`
  host — that one is IPv6-only and was unreachable from Docker Desktop on
  Windows in testing (`Network is unreachable`). Session mode (not 6543
  transaction mode) keeps `db.py`'s `SET statement_timeout` working.
- Mobile uses the `supabase_flutter` SDK (session persistence/refresh handled
  by the SDK, not hand-rolled); web uses `@supabase/supabase-js` browser
  client (`apps/web/lib/supabase.ts`).

### Pipeline (`services/autoedit/pipeline.py`)

`process_video()` runs a resumable, stage-aware state machine:

```
DOWNLOADING → DOWNLOADED → PROBING → TRANSCRIBING → TRANSCRIBED
→ PLANNING → PLAN_READY → SEARCHING_BROLL → BROLL_READY
→ RENDERING → RENDERED → VALIDATING → READY   (or FAILED at any stage)
```

- Transcripts reused across videos by `source_hash`; weak/invalid edit plans
  auto-rebuilt; a re-render (`render_video()`) reuses existing transcript, plan,
  and downloaded B-roll.
- Transcription + edit planner: OpenAI (`llm_model` default `gpt-4o-mini`).
- Providers are swappable behind interfaces in `providers.py`
  (`TranscriptionProvider`, `LLMProvider`, `AssetSearchProvider`).
- Render is one large `filter_complex` in `compose.py`. `RENDER_FFMPEG_THREADS`
  (default 1) caps decoder/filter/encoder threads — uncapped it OOM-kills small
  containers (SIGKILL 9).
- On `READY`, `enqueue_youtube_if_needed()` can push the reel to a YouTube
  auto-upload queue with IST slot scheduling (`youtube.py`,
  `youtube_schedule.py`).

---

## 3. Exact stage of development

### Done and working (MVP + past it)

The single-video and batch pipelines work end-to-end: Drive import →
transcript → validated edit plan → B-roll fetch → Ken Burns / zoom / pan / fade
→ SFX → ducked music → 1080×1920 H.264/AAC render → ffprobe validation →
preview + download. `plan.md` milestones **1–9 are effectively complete.**

Shipped on top of the base MVP (see git log):

- **CapCut-style editor** (`apps/web/components/editor/*`) — timeline, media bin,
  inspector, preview stage; re-render from edited plan via `render_video()`.
- **Word-highlight captions** + caption presets (`captions.py`,
  `components/editor/captionStyle.ts`).
- **SFX engine** (`services/autoedit/sfx/*`) — catalog, style-aware event
  placement, timing, license gating, decision log per job.
- **Music** — 3 bundled tracks, tone-based selection (`music.py`, `tones.py`).
- **YouTube auto-upload** with IST scheduling (route + worker + `0002` migration).
- **Render/Docker productionization** (commit `f41aaad`) — prod Dockerfiles,
  `PORT` injection, env/config plumbing, `RENDER_DEPLOYMENT.md`,
  `render_deployment_changes.md`, `decisions.md`.
- **Jina reranker** (`image_ranking/`) — multimodal rerank of image B-roll
  candidates. OFF by default (`ENABLE_JINA_RERANKER=false`); any failure falls
  back to the existing selection.
- **Dense B-roll** — instead of sparse stock B-roll every 4–8s, almost every
  spoken phrase gets its own full-screen image pulled from the real web.
  `broll_plan.py` (one `gpt-4o` call, `BROLL_QUERY_MODEL`) turns ordered
  caption phrases into one literal image-search query per phrase;
  `build_dense_broll()` rewrites the timeline so each phrase becomes an image
  B-roll segment, gaps stay talking-head. `providers.py`'s `ApifyImageSearch`
  runs one Apify Actor (`hooli~google-images-scraper`) per video to scrape all
  queries at once; `compose.py`'s `write_broll_track()` pre-renders every image
  cut into one 1080×1920 track so the final graph adds a single overlay
  instead of dozens of concurrent image decoders. Kill switch:
  `ENABLE_DENSE_BROLL=false` falls back to sparse Pexels (video B-roll only
  once dense mode is on).
- **Object storage** — `services/autoedit/object_storage.py` ships a dual-mode
  `local`/`r2` backend (`STORAGE_BACKEND` env var, default `local`) —
  Cloudflare R2 in production, unchanged local-disk behavior for dev.
  `storage/broll-cache/` is a pure ephemeral L1 cache on the worker; R2 is the
  source of truth.
- **iOS app** (`apps/mobile`) — started as a `webview_flutter` wrapper around
  the hosted web app; has since grown a full native tab UI (`lib/features/dashboard`)
  and native auth (see §2a). `lib/webview_shell.dart` (Google OAuth divert,
  file downloads since WKWebView ignores `Content-Disposition: attachment`,
  off-origin links to Safari) has no caller anywhere in the app today, but is
  kept correct rather than left stale — its OAuth bridge now mirrors a
  Supabase session into the WebView as the `sb_access_token` cookie, matching
  how `apps/web` mirrors its own session (§2a). No offline support, no push
  notifications — explicit non-goals, see `apps/mobile/README.md`. CI
  (`.github/workflows/ios.yml`) compiles it unsigned on `macos-latest`;
  producing a real IPA needs Apple signing secrets.

### Known loose ends / things to decide

- Dense B-roll not yet run at batch scale; `_collect_broll` does one Apify run
  + **serial** downloads per video — flagged in a `ponytail:` comment as the
  wall-time bottleneck for reels with many phrases.
- Videos rendered before the R2 storage cutover had their local-disk output
  files lost when the old container was recycled — unrecoverable, no
  migration was possible. `serialize_video()`
  (`services/api/routes/projects.py`) now checks `object_exists()` before
  exposing `outputUrl` for a READY video, so the UI shows "video unavailable"
  for these instead of a dead download link.
- Auth now covers email/password + Google + Apple via Supabase (§2a), but
  still single-user assumptions in places (no orgs/teams).
- No billing / multi-tenancy / rate limiting (explicitly out of MVP).
- Deploy target is Render as 3 services (`autoedit-web`, `autoedit-api`,
  `autoedit-worker`, `render.yaml`) + Supabase (Postgres + Auth) + Render
  Redis — API and worker split, each with its own disk-free container.
  YouTube publishing still shares the main worker via a separate Celery
  queue rather than its own 4th service.
- `apps/web` mirrors the Supabase session into a `sb_access_token` cookie
  (`components/providers.tsx`) purely so plain `<img>`/`<video>`/`<audio>`
  tags to auth-gated media routes (thumbnails, source/output video, music,
  B-roll assets — none of which can carry an Authorization header) stay
  authenticated; `get_current_user` reads it as a third fallback after the
  header and the `?token=` query param (the latter is for the mobile
  OAuth-connect redirect specifically, not general browser use).

---

## 4. Running it

```bash
cp .env.example .env          # fill GOOGLE_*, OPENAI_API_KEY, PEXELS_API_KEY,
                              # APIFY_API_TOKEN, optionally JINA_API_KEY,
                              # TOKEN_ENCRYPTION_KEY (Fernet), DATABASE_URL/
                              # SUPABASE_URL/SUPABASE_JWT_SECRET (Supabase project)
npx supabase link --project-ref <ref>   # once per machine
npx supabase db push                    # applies supabase/migrations/*.sql
docker compose up --build     # web :3000, api :8000/health (no local postgres
                               # container anymore - DATABASE_URL points at Supabase)
```

API seeds system SFX/music on first boot; schema/migrations are applied via
`supabase db push` above, not on container start.

Local Python without Docker:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r services/requirements.txt
export PYTHONPATH=services
uvicorn api.main:app --reload --app-dir services
# separate terminal, from services/:
celery -A worker.celery_app worker --loglevel=info
# separate terminal:
cd apps/web && npm install && npm run dev
```

Tests: `PYTHONPATH=services pytest` (media render test needs `ffmpeg`/`ffprobe`
on PATH).

iOS shell: `cd apps/mobile && flutter run --dart-define=AUTOEDIT_APP_URL=<url>`
(needs macOS + Xcode to run on a device/simulator; `flutter analyze`/`flutter
test` work anywhere — see `apps/mobile/README.md`).

---

## 5. Hard rules (from `plan.md` §§46–48)

- Validate all AI JSON; never trust LLM output; allowed effects / SFX / music are
  enums.
- Never pass an LLM string into FFmpeg. `LLM JSON → Pydantic → EditPlan →
  composition engine → safe argv`.
- Google Drive/YouTube OAuth tokens: encrypted at rest (`security.py`), never
  sent to the browser. Login/signup itself is Supabase's problem now, not
  ours — see §2a.
- One failed video must never crash the batch.
- Pipeline stays resumable and stage-aware — don't re-run completed stages.
