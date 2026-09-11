# AutoEdit AI — project context for Claude

Paste-and-discuss brief. Covers what the project is, how it's built, and the
**exact stage of development** it's at (as of 2026-09-02).

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
| `apps/web` | Next.js + React + TS + Tailwind frontend |
| `services/api` | FastAPI app — auth, projects, drive, videos, assets, settings, media, youtube routes |
| `services/worker` | Celery worker (`celery_app.py`, `tasks.py`) |
| `services/autoedit` | **the actual pipeline** — shared by api + worker |
| `alembic/` | Postgres migrations (`0001_initial`, `0002_youtube_uploads`) |
| `assets/` | real SFX (`assets/sfx/*`) + 3 music tracks (`assets/music/*`) |
| `packages/edit-schema` | JSON schema mirror of the edit plan |
| `docker/` | `Dockerfile.{api,web,worker}` + root `docker-compose.yml` |

Infra: PostgreSQL (state), Redis (Celery queue + job status), FFmpeg/ffprobe in
the api and worker images.

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

### In flight right now — "dense B-roll" (uncommitted working tree on `main`)

Goal: instead of sparse stock B-roll every 4–8s, give **almost every spoken
phrase its own full-screen image** pulled from the real web.

New / changed (10 modified files + 4 new, not yet committed):

- **`services/autoedit/broll_plan.py`** (new) — one `gpt-4o` call
  (`BROLL_QUERY_MODEL`) turns ordered caption phrases into one literal
  image-search query per phrase; `build_dense_broll()` rewrites the timeline so
  each phrase becomes an image B-roll segment, gaps stay talking-head.
- **`providers.py`** — `ApifyImageSearch`: one Apify Actor run scrapes many
  Google Images queries at once; maps results to the shape Pexels/Jina expect;
  denylists paid-stock hosts and non-image crawler URLs. Pexels is now **video
  B-roll only**.
- **`compose.py`** — `write_broll_track()` pre-renders all image cuts into ONE
  1080×1920 track + show-windows, so the final graph adds a single overlay
  instead of dozens of concurrent image decoders.
- **`pipeline.py`** — dense path wired in after `enforce_visual_cadence`; one
  Apify run per video, serial candidate downloads, Jina rerank when enabled.
- **`config.py` / `.env.example`** — `ENABLE_DENSE_BROLL=true` (kill switch back
  to sparse Pexels), `APIFY_API_TOKEN`, `APIFY_IMAGE_ACTOR`,
  `APIFY_RESULTS_PER_QUERY`, `APIFY_TIMEOUT_SECONDS`, `BROLL_QUERY_MODEL`.
  `JINA_TIMEOUT_SECONDS` 10 → 25.
- **`edit_schema.py`** — `MAX_VISUAL_ASSETS` 16 → 120 (safety slice for
  phrase-density B-roll, not a design target).
- **`drive.py`** — `download_image()` helper (+ tests).
- New tests: `tests/test_apify_search.py`, `tests/test_broll_plan.py`,
  `tests/test_download_image.py`.

Git history context: commits `ff0ae2d` "jena ai changes with errors" then
`fce139a` "...errors removed" — the Jina/dense-broll work landed rough and is
still being stabilised. **The working tree is mid-refactor; nothing since
`fce139a` is committed.**

### Known loose ends / things to decide

- **Apify actor id mismatch**: `config.py` default is
  `hooli~google-images-scraper`, `README.md` says `emastra~google-images-scraper`.
  Pick one and verify its input/output schema against `ApifyImageSearch._build_input`
  / `_map_item`.
- Dense B-roll not yet committed or run at batch scale; `_collect_broll` does one
  Apify run + **serial** downloads per video — flagged in a `ponytail:` comment as
  the wall-time bottleneck for reels with many phrases.
- **Object storage wired (2026-09-12).** `services/autoedit/object_storage.py`
  ships a dual-mode `local`/`r2` backend (`STORAGE_BACKEND` env var, default
  `local`) — Cloudflare R2 in production, unchanged local-disk behavior for
  dev. `storage/broll-cache/` is local-only (gitignored, not actually
  committed despite what this doc used to say) and is now a pure ephemeral
  L1 cache on the worker; R2 is the source of truth. Videos processed before
  this shipped keep local-disk paths and aren't downloadable post-cutover —
  no data migration was run.
- Auth is minimal (Google OAuth sign-in only, single-user assumptions in places).
- No billing / multi-tenancy / rate limiting (explicitly out of MVP).
- Deploy target is Render as 3 services (`autoedit-web`, `autoedit-api`,
  `autoedit-worker`, `render.yaml`) + managed Postgres + Redis — API and
  worker split, each with its own disk-free container. YouTube publishing
  still shares the main worker via a separate Celery queue rather than its
  own 4th service.

---

## 4. Running it

```bash
cp .env.example .env          # fill GOOGLE_*, OPENAI_API_KEY, PEXELS_API_KEY,
                              # APIFY_API_TOKEN, optionally JINA_API_KEY,
                              # TOKEN_ENCRYPTION_KEY (Fernet)
docker compose up --build     # web :3000, api :8000/health
```

API runs migrations + seeds system SFX/music on first boot.

Local Python without Docker:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r services/requirements.txt
export PYTHONPATH=services
alembic upgrade head
uvicorn api.main:app --reload --app-dir services
# separate terminal, from services/:
celery -A worker.celery_app worker --loglevel=info
# separate terminal:
cd apps/web && npm install && npm run dev
```

Tests: `PYTHONPATH=services pytest` (media render test needs `ffmpeg`/`ffprobe`
on PATH).

---

## 5. Hard rules (from `plan.md` §§46–48)

- Validate all AI JSON; never trust LLM output; allowed effects / SFX / music are
  enums.
- Never pass an LLM string into FFmpeg. `LLM JSON → Pydantic → EditPlan →
  composition engine → safe argv`.
- Google OAuth tokens: encrypted at rest (`security.py`), never sent to the
  browser.
- One failed video must never crash the batch.
- Pipeline stays resumable and stage-aware — don't re-run completed stages.
