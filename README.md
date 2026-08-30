# AutoEdit AI

Turn a Google Drive folder of talking-head clips into polished 9:16 reels.

The LLM decides **what** should happen. FFmpeg decides **how**.

```text
RECORD → UPLOAD TO DRIVE → CLICK PROCESS → GET FINISHED REELS
```

## Stack

- Next.js app (`apps/web`)
- FastAPI (`services/api`)
- Celery workers (`services/worker`) + Redis
- PostgreSQL
- FFmpeg in the API and worker images

## Quick start

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Create a Google Cloud OAuth client (Web application) with:

- Authorized redirect URI: `http://localhost:8000/api/auth/callback`
- Scopes: OpenID, email, profile, and `https://www.googleapis.com/auth/drive.readonly`

Put `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.

**Enable the Google Drive API** in the same Cloud project (APIs & Services → Library → Google Drive API → Enable). Sign-in works without this; listing folders does not.

3. Add keys (required for a real pipeline run):

- `OPENAI_API_KEY` — Whisper transcription + edit planner
- `PEXELS_API_KEY` — B-roll search
- `JINA_API_KEY` — optional. Only used when `ENABLE_JINA_RERANKER=true`, which
  reranks B-roll image candidates with `jina-reranker-m0` before selection.
  Off by default; any failure falls back to the existing selection.

4. Generate a Fernet key (optional but recommended):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set `TOKEN_ENCRYPTION_KEY` to that value.

5. Start everything:

```bash
docker compose up --build
```

- Web: http://localhost:3000
- API health: http://localhost:8000/health

On first boot the API runs migrations and seeds simple system SFX/music tones (replace them in **Assets** with real tracks).

### Local Python (optional)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r services/requirements.txt
export PYTHONPATH=services
alembic upgrade head
uvicorn api.main:app --reload --app-dir services
# other terminal, from services/
celery -A worker.celery_app worker --loglevel=info
```

```bash
cd apps/web && npm install && npm run dev
```

## First working demo

1. Sign in with Google at `/login`.
2. Create a project.
3. Import one talking-head MP4 from Drive.
4. Open the video and click **Process this video** (or **Process All**).
5. Wait on the queue until status is `READY`.
6. Preview and download a 1080×1920 H.264/AAC MP4.

Then try 5 videos, then a larger batch. Do not tune for 50 videos until one reel works.

## Tests

```bash
pip install -r services/requirements.txt
PYTHONPATH=services pytest
```

The media fixture test requires `ffmpeg` and `ffprobe` on PATH.

## Security notes

- Google tokens are encrypted at rest and never sent to the browser.
- Planner JSON is validated with Pydantic. Allowed effects/SFX/music are enums.
- FFmpeg is invoked only with argument arrays, never a shell string from the model.

## Out of MVP

Captions, jump cuts, billing, social publishing, teams, AI-generated B-roll.
