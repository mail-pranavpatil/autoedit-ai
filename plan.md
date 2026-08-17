# AutoEdit AI — Complete Build Plan

## 1. Product Overview

Build a web application that automatically converts a folder of raw talking-head short-form videos into polished, social-media-ready vertical videos.

Primary use case:

1. User records 30–100 short videos.
2. User uploads them to a Google Drive folder.
3. User connects Google Drive to AutoEdit AI.
4. User selects a folder.
5. AutoEdit AI processes all videos in a queue.
6. For each video it:
   - extracts/transcribes speech with timestamps
   - understands the transcript
   - identifies useful B-roll opportunities
   - searches free stock image/video APIs for relevant assets
   - selects/creates an edit plan
   - applies simple B-roll animations
   - adds subtle sound effects
   - selects/loops background music
   - mixes audio
   - renders a 9:16 MP4
7. User previews and downloads the finished videos.

The application should be opinionated and fast. It is NOT intended to be a Premiere Pro replacement.

Core philosophy:

> LLM decides WHAT should happen. FFmpeg decides HOW it happens.

Do not use an LLM for actual video rendering.

---

# 2. MVP Goal

The first version must successfully process a batch of videos end-to-end.

### MVP must support

- Google Drive folder connection
- video discovery
- video download
- transcription with timestamps
- AI-generated edit plan
- B-roll search
- image/video asset downloading
- B-roll placement
- zoom/pan/fade effects
- 5–10 reusable SFX
- 4–5 user-provided background music tracks
- voice/music/SFX audio mixing
- FFmpeg rendering
- batch processing
- progress tracking
- final video preview
- final video download
- retry failed jobs
- persistent processing status

### MVP should NOT include

- complex timeline editor
- manual frame-by-frame editing
- AI avatars
- AI voice generation
- automatic social publishing
- billing
- team collaboration
- complex user roles
- sophisticated caption editor
- automatic thumbnail generation
- unnecessary animations
- expensive AI video generation by default

---

# 3. Product Requirements

## 3.1 Input

Supported input formats:

- MP4
- MOV
- M4V
- WebM where practical

Expected input:

- talking-head videos
- 9:16, 16:9, or 1:1
- 20 seconds to 3 minutes
- one speaker preferred

Output:

- MP4
- H.264 video
- AAC audio
- 1080x1920
- 30 FPS unless source requires otherwise
- optimized for Instagram Reels / YouTube Shorts

---

# 4. Recommended Architecture

Use a monorepo.

Suggested structure:

```text
autoedit-ai/
├── apps/
│   └── web/
│       ├── app/
│       ├── components/
│       ├── lib/
│       ├── hooks/
│       └── styles/
│
├── services/
│   ├── api/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   └── main.py
│   │
│   └── worker/
│       ├── tasks/
│       ├── pipeline/
│       ├── media/
│       ├── ai/
│       └── main.py
│
├── packages/
│   ├── edit-schema/
│   └── shared/
│
├── assets/
│   ├── sfx/
│   └── music/
│
├── scripts/
├── docker/
├── .env.example
├── docker-compose.yml
└── README.md
```

Recommended stack:

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui where useful

### API

- Python
- FastAPI
- Pydantic

### Background jobs

- Redis
- Celery

Alternative:
- RQ if Celery becomes unnecessarily complex.

Use Redis as the queue and job-status backend.

### Database

- PostgreSQL
- Supabase is acceptable for hosted PostgreSQL.

### Media processing

- FFmpeg
- ffprobe

### AI

Use provider abstraction.

Do NOT hard-code the application around one AI provider.

Create interfaces such as:

```text
TranscriptionProvider
LLMProvider
ImageSearchProvider
VideoSearchProvider
```

This allows switching providers later.

### Storage

For local development:

```text
./storage/
```

For production:

- S3-compatible storage
- Cloudflare R2 is preferred if cost-effective
- Google Drive remains the source for raw videos

---

# 5. System Architecture

```text
                     ┌─────────────────────┐
                     │      Next.js        │
                     │      Web App        │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │      FastAPI        │
                     │       API           │
                     └───────┬─────┬───────┘
                             │     │
                 ┌───────────┘     └────────────┐
                 ▼                              ▼
        ┌────────────────┐              ┌───────────────┐
        │   PostgreSQL   │              │     Redis     │
        │     State      │              │     Queue     │
        └────────────────┘              └───────┬───────┘
                                                │
                          ┌─────────────────────┼────────────────────┐
                          ▼                     ▼                    ▼
                    ┌──────────┐         ┌──────────┐         ┌──────────┐
                    │ Worker 1 │         │ Worker 2 │         │ Worker N │
                    └────┬─────┘         └────┬─────┘         └────┬─────┘
                         │                    │                    │
                         └────────────────────┼────────────────────┘
                                              ▼
                                    ┌──────────────────┐
                                    │   Media Engine   │
                                    │     FFmpeg       │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                      Final MP4 files
```

---

# 6. Core Processing Pipeline

Every video should go through this pipeline:

```text
DISCOVER
   ↓
DOWNLOAD
   ↓
VALIDATE
   ↓
PROBE MEDIA
   ↓
TRANSCRIBE
   ↓
ANALYZE TRANSCRIPT
   ↓
GENERATE EDIT PLAN
   ↓
SEARCH B-ROLL
   ↓
DOWNLOAD ASSETS
   ↓
PREPARE B-ROLL
   ↓
BUILD VIDEO COMPOSITION
   ↓
ADD SFX
   ↓
ADD MUSIC
   ↓
MIX AUDIO
   ↓
RENDER
   ↓
VALIDATE OUTPUT
   ↓
STORE RESULT
   ↓
READY
```

Each step must have a status.

---

# 7. Processing State Machine

Use these states:

```text
DISCOVERED
QUEUED
DOWNLOADING
DOWNLOADED
PROBING
TRANSCRIBING
TRANSCRIBED
PLANNING
PLAN_READY
SEARCHING_BROLL
BROLL_READY
RENDERING
RENDERED
VALIDATING
READY
FAILED
```

Failed jobs must store:

- failed stage
- error message
- stack trace/server log reference
- retry count

The UI must allow:

```text
Retry
```

without restarting the entire batch.

---

# 8. Database Schema

Create at minimum these tables.

## users

```text
id
email
created_at
updated_at
```

Authentication can be minimal in MVP.

## drive_connections

```text
id
user_id
provider
access_token_encrypted
refresh_token_encrypted
created_at
updated_at
```

Never expose tokens to the frontend.

## projects

```text
id
user_id
name
created_at
updated_at
```

## source_folders

```text
id
project_id
provider
external_folder_id
folder_name
created_at
```

## videos

```text
id
project_id
external_file_id
filename
source_url
local_path
duration
width
height
fps
status
error_message
created_at
updated_at
```

## transcripts

```text
id
video_id
provider
language
full_text
segments_json
created_at
```

## edit_plans

```text
id
video_id
version
plan_json
created_at
updated_at
```

## assets

```text
id
video_id
provider
external_id
asset_type
query
source_url
local_path
license_info
metadata_json
created_at
```

## render_jobs

```text
id
video_id
status
progress
current_stage
output_path
error_message
started_at
completed_at
created_at
```

---

# 9. Google Drive Integration

Implement OAuth 2.0.

Required functionality:

- connect Google Drive
- list folders
- list videos inside selected folder
- identify supported video files
- download files
- preserve external Google Drive file ID
- avoid downloading the same file twice
- refresh OAuth tokens
- handle revoked permissions

The frontend should show:

```text
Google Drive
────────────────────────────

Connected ✓

Select folder

[ August Reels ]

52 videos found

[ Import Videos ]
```

For MVP, manual folder selection is enough.

Do NOT automatically scan the entire Drive.

---

# 10. Transcription

Create a transcription abstraction:

```python
class TranscriptionProvider:
    async def transcribe(self, audio_path) -> Transcript:
        ...
```

The transcript must include timestamps.

Example:

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 3.8,
      "end": 3.8,
      "text": "Most developers are learning AI completely wrong."
    }
  ]
}
```

Prefer word-level timestamps if the provider supports them.

Do not make the entire pipeline dependent on word-level timestamps.

---

# 11. AI Edit Planner

This is the main AI component.

Input:

- transcript
- video duration
- video metadata
- user style profile

Output:

strict JSON.

The LLM must NEVER return arbitrary prose.

Use a JSON schema.

Example:

```json
{
  "video_summary": "Short summary",
  "tone": "energetic",
  "music_category": "technology",
  "segments": [
    {
      "start": 0,
      "end": 4.5,
      "visual": "talking_head",
      "broll_query": null,
      "broll_type": null,
      "effect": "slow_zoom_in",
      "sfx": null
    },
    {
      "start": 4.5,
      "end": 8.5,
      "visual": "broll",
      "broll_query": "developer using AI tools",
      "broll_type": "video",
      "effect": "pan_left",
      "sfx": "whoosh"
    }
  ]
}
```

---

# 12. Edit Planner Rules

The AI should follow these rules.

## B-roll

Use B-roll only when it improves comprehension.

Do not replace the talking head constantly.

Default target:

- 1 B-roll every 4–8 seconds
- fewer for strong personal statements
- more for explanatory sections

Never cover the entire video with B-roll unless explicitly requested.

## Effects

Allowed effects:

```text
none
slow_zoom_in
slow_zoom_out
pan_left
pan_right
pan_up
pan_down
fade_in
fade_out
```

Do not use aggressive effects by default.

## SFX

Allowed:

```text
whoosh
pop
click
camera_shutter
notification
ding
swipe
impact
bubble
cartoon
```

SFX should be sparse.

Maximum default:

```text
1 SFX every 3–5 seconds
```

but the AI should use fewer when appropriate.

## Music

Allowed categories:

```text
energetic
technology
cinematic
motivational
chill
```

Select based on transcript tone.

---

# 13. B-roll Search

Create a provider interface:

```python
class AssetSearchProvider:
    async def search(
        self,
        query: str,
        asset_type: str,
        orientation: str
    ):
        ...
```

Implement Pexels first.

Optional later providers:

- Pixabay
- Unsplash for still images
- user-uploaded B-roll library

Prefer:

1. video B-roll
2. image
3. AI-generated image as fallback

Do not generate AI B-roll in MVP unless explicitly enabled.

---

# 14. B-roll Query Generation

The LLM should produce search-friendly queries.

Bad:

```text
"the existential challenge developers face in a rapidly changing AI ecosystem"
```

Good:

```text
developer coding laptop
```

Good:

```text
AI chatbot customer support
```

Good:

```text
business automation office
```

Search queries should be:

- concrete
- visual
- short
- 2–6 words

---

# 15. Asset Selection

If multiple assets are returned, score them.

Possible scoring:

```text
relevance: 50%
orientation: 15%
resolution: 15%
duration: 10%
visual quality: 10%
```

Prefer vertical assets where possible.

If vertical is unavailable:

- crop to 9:16
- use smart center crop
- avoid stretching

---

# 16. B-roll Rendering

B-roll should appear as an overlay/full-screen visual depending on style.

For MVP use:

```text
Full-screen B-roll
```

with optional talking-head picture-in-picture deferred to V2.

Every B-roll segment must be converted to 9:16.

For images:

- create virtual video duration
- apply Ken Burns-style motion
- crop to 1080x1920
- render at target FPS

---

# 17. Effects Engine

Create a reusable FFmpeg effects library.

Example API:

```python
apply_zoom_in(...)
apply_zoom_out(...)
apply_pan_left(...)
apply_pan_right(...)
apply_fade(...)
```

Do NOT construct massive unreadable FFmpeg commands throughout the application.

Create a dedicated media abstraction layer.

Example:

```text
services/worker/media/
├── ffmpeg.py
├── filters.py
├── transitions.py
├── audio.py
├── images.py
└── composition.py
```

---

# 18. Audio Engine

There are three audio layers:

```text
VOICE
MUSIC
SFX
```

## Voice

Preserve original voice.

Normalize reasonably.

Do not aggressively process speech in MVP.

## Music

Music must be:

- looped if necessary
- trimmed to video length
- normalized
- reduced under speech

Default music volume:

```text
8–15%
```

Use sidechain/ducking if practical.

If sidechain is too complex initially, use a simple low music gain.

## SFX

Default volume:

```text
15–30%
```

SFX should never overpower speech.

---

# 19. User Asset Library

Allow the user to upload:

```text
SFX
Music
```

UI:

```text
Assets

Music
────────────────
energetic.mp3
technology.mp3
cinematic.mp3
motivational.mp3

SFX
────────────────
whoosh.wav
pop.wav
click.wav
shutter.wav
impact.wav
```

Allow:

- upload
- delete
- rename
- enable/disable

---

# 20. Style Profile

Create a settings page.

Example:

```text
STYLE PROFILE

Aspect Ratio
9:16

Resolution
1080x1920

B-roll Frequency
Low / Medium / High

B-roll Type
Video / Images / Both

Transitions
✓ Zoom
✓ Pan
✓ Fade

SFX
✓ Whoosh
✓ Pop
✓ Click
✓ Shutter

Music
✓ Energetic
✓ Technology
✓ Cinematic
✓ Motivational

Music Volume
12%

SFX Volume
25%
```

Store this configuration as JSON.

The AI planner must receive the active style profile.

---

# 21. Rendering Strategy

Never render inside the Next.js request lifecycle.

Never make the browser responsible for rendering.

Instead:

```text
API
 ↓
Redis queue
 ↓
Worker
 ↓
FFmpeg
```

Every video should be an independent job.

---

# 22. Parallel Processing

The system must support multiple worker processes.

Example:

```text
20 videos

Worker 1 → Video 1
Worker 2 → Video 2
Worker 3 → Video 3
Worker 4 → Video 4

When Video 1 finishes:
Worker 1 → Video 5
```

Make worker concurrency configurable:

```env
WORKER_CONCURRENCY=4
```

Do not blindly use unlimited concurrency.

Media processing is CPU-intensive.

---

# 23. Job Progress

Expose progress through API.

Example:

```json
{
  "status": "RENDERING",
  "progress": 73,
  "current_stage": "Rendering final video"
}
```

Stages should have approximate weighted progress:

```text
Download        10%
Probe            5%
Transcription   15%
AI Planning     10%
B-roll          15%
Rendering       40%
Validation       5%
```

These values do not need to be exact.

---

# 24. Frontend Pages

## Dashboard

Show:

- total videos
- processing
- completed
- failed
- recent projects

## Project Page

Show:

```text
Project: August Reels

52 videos

[ Process All ]

Processing:
12

Completed:
35

Failed:
2

Queued:
3
```

## Video Queue

Each row:

```text
Thumbnail
Filename
Duration
Status
Progress
Current Stage
Actions
```

Actions:

- Preview
- Retry
- Delete
- Download

## Asset Library

Manage music and SFX.

## Settings

Manage:

- style
- AI provider
- asset providers
- rendering settings

---

# 25. API Endpoints

Implement REST APIs.

## Projects

```text
GET    /api/projects
POST   /api/projects
GET    /api/projects/{id}
DELETE /api/projects/{id}
```

## Google Drive

```text
GET /api/drive/auth
GET /api/drive/callback
GET /api/drive/folders
GET /api/drive/folders/{id}/videos
POST /api/drive/import
```

## Videos

```text
GET    /api/videos
GET    /api/videos/{id}
POST   /api/videos/{id}/process
POST   /api/videos/{id}/retry
DELETE /api/videos/{id}
GET    /api/videos/{id}/download
```

## Batch

```text
POST /api/projects/{id}/process
GET  /api/projects/{id}/progress
POST /api/projects/{id}/retry-failed
```

## Assets

```text
GET    /api/assets
POST   /api/assets/upload
DELETE /api/assets/{id}
```

## Settings

```text
GET /api/settings
PUT /api/settings
```

---

# 26. Security

Important:

- never expose Google OAuth tokens to frontend
- encrypt stored refresh tokens
- validate uploaded file types
- limit upload size
- sanitize filenames
- never execute user-provided shell commands
- never interpolate arbitrary strings directly into shell commands
- use subprocess argument arrays where possible
- clean temporary files
- restrict filesystem paths
- validate FFmpeg inputs
- do not allow path traversal
- rate-limit API endpoints
- keep API keys server-side

---

# 27. Temporary Storage

Each job gets an isolated workspace:

```text
storage/jobs/{job_id}/
├── source.mp4
├── audio.wav
├── transcript.json
├── edit_plan.json
├── assets/
├── intermediate/
└── final.mp4
```

After successful completion:

- preserve final output
- optionally remove intermediates

After failure:

- preserve logs
- optionally preserve intermediates for debugging

Implement cleanup jobs.

---

# 28. FFmpeg Requirements

Verify FFmpeg exists during startup.

Expose:

```text
GET /health
```

which reports:

```json
{
  "api": true,
  "redis": true,
  "database": true,
  "ffmpeg": true
}
```

Use `ffprobe` to determine:

- duration
- width
- height
- FPS
- codec
- audio presence

---

# 29. Output Validation

After rendering:

Run ffprobe.

Verify:

- file exists
- duration > 0
- video stream exists
- audio stream exists when source had audio
- resolution = 1080x1920
- codec = H.264
- file is readable

Only mark:

```text
READY
```

after validation succeeds.

---

# 30. Performance Requirements

Primary objective:

> Process a large batch without making the user wait for every individual video.

Requirements:

- concurrent transcription where provider permits
- concurrent B-roll searches
- concurrent asset downloads
- parallel FFmpeg workers
- caching
- avoid duplicate asset downloads
- avoid re-transcribing completed videos
- avoid re-running completed stages
- resumable pipeline
- retry individual stages where practical

The pipeline should be stage-aware.

For example, if rendering fails:

```text
Do NOT:

download video
transcribe
search B-roll
again
```

Instead:

```text
reuse existing assets
reuse transcript
reuse edit plan
retry rendering
```

---

# 31. Caching

Cache:

### Transcripts

Key:

```text
hash(source_file)
```

### AI edit plans

Key:

```text
hash(transcript + style_profile + planner_version)
```

### B-roll search results

Key:

```text
provider + query + orientation
```

### Downloaded assets

Key:

```text
provider + external_asset_id
```

This reduces cost and API usage dramatically.

---

# 32. AI Cost Control

The LLM should receive only what it needs.

Do not send:

- raw video
- huge unnecessary metadata
- complete asset search results

Send:

- transcript
- duration
- style profile

Use structured JSON output.

Keep prompts deterministic and versioned.

Store:

```text
planner_version
```

with every edit plan.

---

# 33. Error Handling

Every pipeline stage must catch errors.

Example:

```text
TRANSCRIBING
    ↓ error
FAILED
```

UI:

```text
Video 23

Failed during transcription.

[ Retry ]
```

Do not crash the entire batch because one video fails.

---

# 34. Logging

Use structured logs.

Every log should contain:

```text
job_id
video_id
stage
timestamp
message
```

Example:

```text
[video_23][BROLL_SEARCH] Searching "AI coding assistant"
```

Do not log:

- OAuth tokens
- API keys
- private user data unnecessarily

---

# 35. Developer Experience

Create:

```text
.env.example
```

with:

```env
DATABASE_URL=
REDIS_URL=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

LLM_API_KEY=
TRANSCRIPTION_API_KEY=

PEXELS_API_KEY=

STORAGE_PATH=./storage

WORKER_CONCURRENCY=4
```

Create:

```text
docker-compose.yml
```

for:

- PostgreSQL
- Redis

Local development should be:

```bash
docker compose up -d
```

Then:

```bash
npm install
pip install -r requirements.txt
npm run dev
```

Document exact commands in README.

---

# 36. Testing

Implement tests for:

## Backend

- Google Drive service
- transcript parsing
- edit plan validation
- B-roll query generation
- asset selection
- job state transitions
- API endpoints

## Media

Use a tiny sample video.

Test:

- probe
- crop
- zoom
- pan
- fade
- audio mix
- B-roll composition
- final output validation

## End-to-end

Create one test video and run:

```text
source
→ transcript
→ plan
→ B-roll
→ render
→ validation
→ ready
```

Do not rely only on mocked FFmpeg tests.

---

# 37. Sample Data

Include:

```text
tests/fixtures/
├── sample.mp4
├── sample_transcript.json
├── sample_edit_plan.json
└── sample_style_profile.json
```

Also include 5 dummy SFX and 2 royalty-cleared test music tracks if licensing permits.

Do not commit copyrighted commercial music.

---

# 38. UX Principles

The application should feel extremely simple.

The user should not need to understand:

- FFmpeg
- transcription
- workers
- queues
- AI models
- codecs
- B-roll APIs

Primary workflow:

```text
Connect Drive
      ↓
Select Folder
      ↓
Review Videos
      ↓
Generate
      ↓
Wait / Continue Working
      ↓
Finished
      ↓
Download
```

---

# 39. Visual Design

Use a modern, clean creator-tool aesthetic.

Prefer:

- dark/light neutral UI
- clear status badges
- large thumbnails
- minimal controls
- progress bars
- obvious primary actions
- responsive design

Do not overdesign.

This is a utility.

---

# 40. Important Product Decision

The first version is an AUTOMATED VIDEO ASSEMBLER, not a full AI editor.

The system should optimize for:

```text
80% quality
+
90% automation
+
very low user effort
```

instead of:

```text
99% theoretical editing quality
+
lots of manual controls
```

The user can always do a final manual touch-up in CapCut/Premiere if necessary.

---

# 41. Suggested Default Editing Style

For the first version:

```text
Canvas: 1080x1920

B-roll:
1 every 4–8 seconds

Image duration:
2–4 seconds

Zoom:
slow and subtle

Pan:
slow

Fade:
short

SFX:
subtle

Music:
8–15%

Voice:
dominant

Transitions:
simple
```

Avoid:

- glitch effects
- excessive emojis
- aggressive transitions
- random SFX every sentence
- excessive zoom
- distracting B-roll

---

# 42. Future V2 Features

After MVP works:

## Captions

Automatically generate:

- word-highlight captions
- sentence captions
- dynamic emphasis

## Jump cuts

Detect silence and unnecessary pauses.

## Face detection

Keep face centered when converting landscape footage to vertical.

## Smart reframing

Track speaker automatically.

## AI B-roll generation

Use AI image generation only when stock search fails.

## B-roll library

Allow user to upload personal reusable B-roll.

## Brand profiles

Store:

- fonts
- colors
- caption style
- intro
- outro
- logo

## Templates

Example:

```text
Tech Reel
Business Reel
Story Reel
Educational Reel
News Reel
```

## Social publishing

Later:

- YouTube
- Instagram where API capabilities permit
- TikTok where API capabilities permit

---

# 43. Future SaaS Architecture

If the tool becomes public:

```text
User
 ↓
Project
 ↓
Job Queue
 ↓
GPU/CPU Worker Pool
 ↓
Object Storage
```

Add:

- authentication
- subscriptions
- usage limits
- credits
- multi-tenancy
- billing
- monitoring
- abuse prevention

Do NOT implement these in MVP.

---

# 44. Implementation Order

Cursor should implement in this exact sequence.

## Phase 1 — Project Foundation

- create monorepo
- create Next.js app
- create FastAPI app
- create worker
- configure PostgreSQL
- configure Redis
- configure Docker
- configure environment variables
- create README
- create health checks

## Phase 2 — Database

- implement schema
- migrations
- models
- repositories/services

## Phase 3 — Google Drive

- OAuth
- folder browsing
- video discovery
- download
- token handling

## Phase 4 — Video Infrastructure

- ffprobe
- media validation
- temporary workspace
- media metadata extraction

## Phase 5 — Transcription

- provider abstraction
- transcription implementation
- timestamped transcript
- caching

## Phase 6 — AI Planner

- style profile
- planner prompt
- JSON schema
- validation
- planner versioning
- caching

## Phase 7 — B-roll

- Pexels provider
- search
- scoring
- downloading
- caching
- orientation handling

## Phase 8 — FFmpeg Engine

Implement:

- crop
- scale
- zoom
- pan
- fade
- image-to-video
- video overlay
- audio mixing
- music looping
- SFX placement

## Phase 9 — Full Pipeline

Connect:

```text
Drive
→ download
→ transcribe
→ plan
→ B-roll
→ FFmpeg
→ validate
→ output
```

## Phase 10 — Queue

- Celery
- Redis
- worker concurrency
- retries
- job status
- progress

## Phase 11 — Frontend

- dashboard
- project page
- Drive picker
- processing queue
- progress
- preview
- download
- assets
- settings

## Phase 12 — Hardening

- tests
- logging
- cleanup
- error handling
- security
- performance
- documentation

---

# 45. Definition of Done

The MVP is complete only when the following works.

### Scenario

User has:

```text
Google Drive/
└── August Reels/
    ├── reel01.mp4
    ├── reel02.mp4
    ├── reel03.mp4
    ├── ...
    └── reel50.mp4
```

User opens AutoEdit AI.

User:

```text
Connect Google Drive
→ Select August Reels
→ Import 50 videos
→ Process All
```

System:

```text
Downloads videos
→ transcribes
→ generates edit plans
→ finds B-roll
→ downloads assets
→ applies effects
→ adds SFX
→ adds music
→ renders
→ validates
```

Final dashboard:

```text
50 videos

Completed: 48
Failed: 2
Processing: 0
Queued: 0

[ Download All ]

Failed:
reel17.mp4
reel34.mp4

[ Retry Failed ]
```

User can preview a completed video and download it.

---

# 46. Cursor Execution Instructions

You are an autonomous senior full-stack engineer.

Build this project from this plan.

Do NOT skip architecture because an implementation is difficult.

Do NOT replace required functionality with fake UI.

Do NOT create mock buttons that don't work.

Do NOT hard-code fake processing progress.

Do NOT simulate video rendering.

The core pipeline must actually process real videos.

However, implement incrementally and keep the application runnable after every phase.

### Rules

1. Inspect the repository before changing anything.
2. Reuse existing code when appropriate.
3. Do not overwrite working code unnecessarily.
4. Create clean abstractions.
5. Keep provider integrations replaceable.
6. Keep secrets server-side.
7. Validate all AI JSON.
8. Never trust LLM output blindly.
9. Never execute arbitrary shell commands from AI output.
10. Use FFmpeg through safe subprocess argument arrays.
11. Make processing resumable.
12. Make jobs idempotent where practical.
13. Never let one failed video crash the batch.
14. Log every pipeline stage.
15. Add tests for important components.
16. Keep the UI functional while backend work progresses.
17. Do not add unnecessary features.
18. Prefer simple deterministic systems over "AI magic."
19. Optimize for batch processing.
20. Keep the system deployable.

---

# 47. AI Planner Safety Rules

The LLM is allowed to return only structured editing decisions.

It must NOT:

- execute commands
- provide shell commands
- provide URLs that are directly executed
- choose arbitrary filesystem paths
- modify application configuration
- access credentials
- control workers

The backend validates every planner response against a strict schema.

Allowed effects must come from an enum.

Allowed SFX names must come from the registered SFX library.

Allowed music categories must come from registered categories.

---

# 48. Rendering Rules

Never pass an LLM-generated string directly into an FFmpeg command.

Instead:

```text
LLM JSON
 ↓
Pydantic validation
 ↓
Internal EditPlan object
 ↓
Media composition engine
 ↓
safe FFmpeg arguments
```

This is mandatory.

---

# 49. Batch Optimization

When processing 50 videos:

Do not unnecessarily repeat identical work.

For example:

If 20 videos request:

```text
developer coding laptop
```

the system should reuse cached search results.

If the exact same asset is selected for multiple videos:

- download once
- reuse locally

If two videos have the same source hash:

- do not transcribe twice

If a video has already reached:

```text
PLAN_READY
```

do not restart from:

```text
DOWNLOADING
```

---

# 50. Development Milestones

Cursor should stop after each milestone and verify the system.

### Milestone 1

Foundation boots.

Expected:

```text
Next.js ✓
FastAPI ✓
Postgres ✓
Redis ✓
Worker ✓
```

### Milestone 2

Google Drive works.

Expected:

```text
Connect Drive
→ choose folder
→ list videos
→ download video
```

### Milestone 3

Transcription works.

Expected:

```text
video.mp4
→ transcript.json
```

### Milestone 4

AI planner works.

Expected:

```text
transcript.json
→ validated edit_plan.json
```

### Milestone 5

B-roll works.

Expected:

```text
query
→ asset
→ downloaded asset
```

### Milestone 6

FFmpeg engine works.

Expected:

```text
sample.mp4
+
sample B-roll
+
music
+
SFX
→ final.mp4
```

### Milestone 7

Full single-video pipeline works.

### Milestone 8

Batch pipeline works.

### Milestone 9

Frontend fully connected.

### Milestone 10

Performance/security/testing pass.

---

# 51. First Working Demo

Before considering the project complete, make this exact demo work:

Input:

```text
1 talking-head MP4
```

Pipeline:

```text
MP4
↓
Transcription
↓
AI Edit Plan
↓
2–3 B-roll assets
↓
1–2 SFX
↓
1 music track
↓
Zoom/pan/fade
↓
FFmpeg
```

Output:

```text
1080x1920 final.mp4
```

Then expand to:

```text
5 videos
```

Then:

```text
50 videos
```

Do not attempt 50-video optimization before the single-video pipeline works.

---

# 52. Final Engineering Principle

The application should be built around this equation:

```text
Raw Video
+
Transcript
+
Edit Plan
+
B-roll
+
SFX
+
Music
+
FFmpeg
=
Finished Reel
```

The AI is the decision-making layer.

The media engine is deterministic.

The queue makes it scalable.

The web application makes it usable.

The entire system should ultimately reduce the user's editing workflow to:

```text
RECORD
   ↓
UPLOAD TO DRIVE
   ↓
CLICK PROCESS
   ↓
GET FINISHED REELS
```

That is the product.
