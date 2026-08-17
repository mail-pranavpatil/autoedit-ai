# AutoEdit AI — Detailed UI Screens Specification

## 0. Purpose

This document defines the complete frontend/UI specification for AutoEdit AI.

The existing `plan.md` defines the backend, processing pipeline, FFmpeg architecture, database, queue, and AI system.

This document defines:

- every screen
- every route
- every major component
- what appears on each screen
- what actions are available
- loading states
- empty states
- error states
- processing states
- navigation
- responsive behavior
- visual hierarchy
- interaction rules

Cursor should use this document to build the frontend.

---

# 1. Product UI Philosophy

AutoEdit AI is a creator utility, not a complicated professional video editor.

The UI should communicate one core promise:

> Upload your raw videos. AutoEdit AI handles the editing.

The user should never need to understand:

- FFmpeg
- AI pipelines
- queues
- transcription providers
- B-roll APIs
- rendering workers
- codecs
- JSON
- background jobs

The interface should make the entire workflow feel like:

```text
CONNECT DRIVE
      ↓
SELECT VIDEOS
      ↓
CHOOSE STYLE
      ↓
PROCESS
      ↓
REVIEW
      ↓
DOWNLOAD
```

---

# 2. Number of Screens

The MVP should have **10 primary screens/routes**.

## Primary screens

1. Dashboard
2. Project Detail
3. Import from Google Drive
4. Video Processing Queue
5. Video Detail / Preview
6. Batch Results
7. Asset Library
8. Style Profile
9. Settings
10. Help / System Status

There should also be reusable modal/drawer states for:

- Create Project
- Select Drive Folder
- Import Videos
- Process Confirmation
- Retry Job
- Delete Confirmation
- Asset Upload
- Video Preview
- Error Details

Do NOT create separate pages for these unless necessary.

---

# 3. Global Application Shell

Every authenticated application screen should use the same shell.

## Desktop Layout

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Logo / AutoEdit AI                         Search    Notifications │
├───────────────┬─────────────────────────────────────────────────────┤
│               │                                                     │
│ Dashboard     │                                                     │
│ Projects      │                    MAIN CONTENT                     │
│ Assets        │                                                     │
│ Style         │                                                     │
│ Settings      │                                                     │
│               │                                                     │
│               │                                                     │
│               │                                                     │
│────────────────                                                     │
│ Help          │                                                     │
│ System Status │                                                     │
│               │                                                     │
│ User Profile  │                                                     │
└───────────────┴─────────────────────────────────────────────────────┘
```

## Sidebar

Items:

```text
Dashboard
Projects
Assets
Style Profile
Settings
────────────
Help
System Status
```

The current route should have an obvious active state.

At the bottom:

```text
User
Email
Settings
Logout
```

## Top Bar

Desktop top bar:

- current page title
- optional breadcrumb
- global search only if useful
- notification/status indicator
- user avatar/menu

Do not overcrowd the top bar.

---

# 4. Navigation

Recommended routes:

```text
/dashboard

/projects
/projects/[projectId]

/projects/[projectId]/import
/projects/[projectId]/queue
/projects/[projectId]/results
/projects/[projectId]/videos/[videoId]

/assets
/style
/settings
/help
/system
```

If authentication is implemented:

```text
/login
```

Authentication UI is not the focus of the MVP.

---

# 5. Screen 1 — Dashboard

## Route

```text
/dashboard
```

## Purpose

Give the user an immediate overview of their content-processing workflow.

The dashboard should answer:

- How many videos are processing?
- How many are complete?
- What projects exist?
- What should I do next?

---

## Header

```text
Dashboard

Turn your raw recordings into finished reels.

[ + New Project ]
```

Primary CTA:

```text
+ New Project
```

---

## Stats Row

Four cards:

```text
┌──────────────┐
│ Projects     │
│ 4            │
└──────────────┘

┌──────────────┐
│ Processing   │
│ 7            │
└──────────────┘

┌──────────────┐
│ Completed    │
│ 128          │
└──────────────┘

┌──────────────┐
│ Failed       │
│ 3            │
└──────────────┘
```

Cards should be compact.

Clicking a stat should navigate to the relevant filtered project/video view.

---

## Active Processing Section

If jobs are active:

```text
Currently Processing

August Reels

████████████████░░░░  78%

31 / 40 videos completed

[ View Queue ]
```

If multiple projects are processing, show the top 2–3.

---

## Recent Projects

Card grid or table.

Each project card:

```text
August Reels

40 videos
32 completed
2 failed
6 processing

Last updated:
Today, 3:42 PM

[ Open Project ]
```

Include project thumbnail if available.

---

## Empty Dashboard

If no projects exist:

```text
Your workspace is empty.

Create your first project and turn a folder of raw videos
into finished reels.

[ Create First Project ]
```

Optional visual:

- subtle abstract film/video icon
- no stock photography required

---

# 6. Screen 2 — Projects

## Route

```text
/projects
```

## Purpose

List all projects.

---

## Header

```text
Projects

Your video editing projects.

[ + New Project ]
```

---

## Search / Filters

Controls:

```text
Search projects...

Status:
All
Processing
Completed
Needs Attention

Sort:
Recently Updated
Newest
Oldest
```

---

## Project List

Use cards on desktop.

Each card:

```text
┌─────────────────────────────────────────┐
│ Thumbnail strip                         │
│                                         │
│ August Reels                            │
│ 50 videos                               │
│                                         │
│ ███████████████░░░  82%                 │
│                                         │
│ ✓ 41 completed   ◐ 7 processing         │
│ ✕ 2 failed      ○ 0 queued              │
│                                         │
│ Updated 12 min ago                      │
│                                         │
│ [ Open Project ]                        │
└─────────────────────────────────────────┘
```

---

## Project Card Menu

Three-dot menu:

```text
Open
Rename
Duplicate Settings
Retry Failed
Delete
```

Delete requires confirmation.

---

## Empty State

```text
No projects yet.

[ Create Project ]
```

---

# 7. Create Project Modal

Triggered by:

```text
+ New Project
```

Modal:

```text
Create Project

Project name
[ August Reels ]

Optional description
[ Monthly short-form content ]

[ Cancel ]     [ Create Project ]
```

After creation:

Navigate to:

```text
/projects/[projectId]
```

---

# 8. Screen 3 — Project Detail

## Route

```text
/projects/[projectId]
```

## Purpose

This is the main workspace for a content batch.

---

## Header

```text
← Projects

August Reels

50 videos · Updated 5 minutes ago

[ Import Videos ]   [ Process All ]
```

Primary CTA:

```text
Process All
```

If there are unprocessed videos.

If processing is already running:

```text
[ View Processing ]
```

---

## Project Summary

Top cards:

```text
Total
50

Ready
41

Processing
7

Failed
2
```

---

## Progress Banner

If processing:

```text
Processing August Reels

████████████████░░░░ 78%

41 of 50 videos completed

Current:
"Why AI developers should learn T-shaped skills"

[ View Queue ]
```

---

## Video Grid

Main section.

Each video card:

```text
┌──────────────────────┐
│                      │
│     VIDEO THUMB      │
│                      │
│      00:48           │
│                      │
├──────────────────────┤
│ AI Skills T-Shaped   │
│                      │
│ ✓ Ready              │
│                      │
│ [ Preview ]          │
└──────────────────────┘
```

Status badges:

```text
Queued
Downloading
Transcribing
Planning
Finding B-roll
Rendering
Ready
Failed
```

---

## Video Card Menu

```text
Preview
Process
Retry
Download
View Details
Delete
```

---

## Filters

```text
All
Queued
Processing
Ready
Failed
```

Search:

```text
Search videos...
```

---

# 9. Screen 4 — Google Drive Import

## Route

```text
/projects/[projectId]/import
```

## Purpose

Import raw videos from Google Drive.

---

## Step 1 — Connection

If not connected:

```text
Import from Google Drive

Connect your Google Drive to import your raw videos.

[ Connect Google Drive ]
```

Explain briefly:

```text
AutoEdit AI only needs access to the files/folder
you choose to import.
```

---

## Connected State

```text
Google Drive ✓ Connected

Connected account:
user@gmail.com

[ Change Account ]
```

---

## Folder Picker

```text
Select a folder

My Drive
  >
Content
  >
August
  >
August Reels

[ Select This Folder ]
```

Show folders with:

- folder icon
- name
- modified date

---

## Video Discovery

After selecting:

```text
August Reels

52 supported videos found

48 MP4
4 MOV

[ Select All ]
[ Deselect All ]
```

---

## Video Selection List

Each row:

```text
☑ thumbnail
  reel_001.mp4
  00:42
  1080x1920
```

Allow selecting individual videos.

Top:

```text
52 videos found
52 selected
```

---

## Bottom Sticky Action Bar

```text
52 videos selected

[ Cancel ]      [ Import 52 Videos ]
```

---

## Import Success

After import:

```text
52 videos imported successfully.

[ View Project ]
```

---

# 10. Screen 5 — Video Processing Queue

## Route

```text
/projects/[projectId]/queue
```

## Purpose

Show detailed live processing.

This screen is extremely important for batch jobs.

---

## Header

```text
Processing Queue

August Reels

41 / 50 complete

[ Pause Queue ] [ Retry Failed ]
```

If pause is not implemented, do not display a fake Pause button.

---

## Overall Progress

Large:

```text
████████████████░░░░ 82%

41 completed
7 processing
2 failed
0 queued
```

---

## Queue Table

Columns:

```text
Video
Status
Stage
Progress
Duration
Actions
```

Example:

```text
AI Careers.mp4
✓ Ready
Complete
100%
00:48
[ Preview ]

T-Shaped Skills.mp4
◐ Rendering
Rendering final video
72%
00:52
[ View ]

AI Tools.mp4
◐ Transcribing
Transcribing audio
35%
00:41
[ View ]

Startup Mistakes.mp4
✕ Failed
B-roll search
—
00:56
[ Retry ]
```

---

## Stage Labels

Use human-readable labels:

```text
Downloading video
Reading video
Transcribing speech
Understanding content
Finding B-roll
Preparing visuals
Adding sound effects
Mixing music
Rendering video
Checking final video
Ready
```

Never show internal enum names like:

```text
SEARCHING_BROLL
```

to the normal user.

---

## Processing Detail Drawer

Clicking a processing video opens a drawer.

```text
AI Careers.mp4

Current stage:
Finding B-roll

████████████░░░░ 72%

Completed stages:
✓ Downloaded
✓ Transcribed
✓ Edit plan created
✓ B-roll found

Current:
Finding visual assets

Estimated remaining:
Not available
```

Do not show fake time estimates.

---

# 11. Screen 6 — Video Detail / Preview

## Route

```text
/projects/[projectId]/videos/[videoId]
```

## Purpose

Review one generated video.

---

## Layout

Desktop:

```text
┌───────────────────────┬───────────────────────────────┐
│                       │ Video Information             │
│                       │                               │
│     VIDEO PLAYER      │ Title                         │
│                       │ Duration                      │
│      9:16             │ Status                        │
│                       │                               │
│                       │ Processing Summary             │
│                       │                               │
│                       │ B-roll: 7 assets              │
│                       │ SFX: 4                        │
│                       │ Music: Technology             │
│                       │                               │
│                       │ [ Download ]                  │
│                       │ [ Reprocess ]                 │
└───────────────────────┴───────────────────────────────┘
```

---

## Video Player

Vertical player.

Controls:

- play/pause
- seek
- volume
- fullscreen
- playback speed

Do not build a full editing timeline.

---

## Metadata

```text
Video

Filename:
reel_021.mp4

Duration:
00:47

Resolution:
1080×1920

Status:
Ready
```

---

## AI Processing Summary

```text
AI Edit Summary

Tone:
Energetic

B-roll:
6 scenes

Transitions:
Zoom / Pan / Fade

Sound Effects:
4

Background Music:
Technology
```

---

## Download

Primary button:

```text
Download MP4
```

Optional:

```text
Download Source Assets
```

Do not include this unless implemented.

---

## Failed Video State

Instead of player:

```text
This video could not be processed.

Failed during:
Finding B-roll

Reason:
Asset provider temporarily unavailable.

[ Retry Video ]

[ View Technical Details ]
```

---

# 12. Screen 7 — Batch Results

## Route

```text
/projects/[projectId]/results
```

## Purpose

Final output/review screen.

---

## Header

```text
August Reels

Processing complete

48 of 50 videos completed.

[ Download All Ready Videos ]
```

---

## Results Summary

```text
48 Ready
2 Failed
```

---

## Completed Video Grid

Show cards with:

- thumbnail
- title
- duration
- ready badge
- preview
- download

---

## Download All

Button:

```text
Download All Ready Videos
```

If browser limitations make ZIP generation impractical, use a server-generated ZIP.

Only display the button if it actually works.

---

## Failed Section

```text
Needs Attention

2 videos failed.

[ Retry All Failed ]
```

List failed videos with:

- filename
- failed stage
- concise reason
- retry button

---

# 13. Screen 8 — Asset Library

## Route

```text
/assets
```

## Purpose

Manage reusable music and SFX.

---

## Header

```text
Asset Library

Your music and sound effects.

[ Upload Asset ]
```

---

## Tabs

```text
Music
Sound Effects
```

---

## Music Tab

Cards:

```text
Technology.mp3

02:14

Category:
Technology

Enabled ✓

[ Preview ] [ Menu ]
```

Menu:

```text
Rename
Change Category
Disable
Delete
```

---

## SFX Tab

Cards:

```text
Whoosh.wav

00:02

Type:
Whoosh

Enabled ✓

[ Preview ] [ Menu ]
```

---

## Upload Modal

```text
Upload Asset

Type:
( ) Music
( ) Sound Effect

File:
[ Choose File ]

Name:
[ Whoosh ]

Category:
[ Whoosh ]

[ Cancel ] [ Upload ]
```

---

## Empty Asset State

Music:

```text
No music uploaded.

Upload 4–5 background tracks to let AutoEdit
automatically choose music for your reels.

[ Upload Music ]
```

SFX:

```text
No sound effects yet.

Add reusable effects like whoosh, pop, click,
shutter and impact.

[ Upload SFX ]
```

---

# 14. Screen 9 — Style Profile

## Route

```text
/style
```

## Purpose

Define the editing style used by the AI planner.

This screen controls the default behavior of generated reels.

---

## Header

```text
Style Profile

Define how AutoEdit should edit your videos.

[ Save Changes ]
```

---

## Output Settings

```text
Output Format

Aspect Ratio
9:16

Resolution
1080 × 1920

FPS
30
```

If these are fixed in MVP, show them as informational rather than editable.

---

## B-roll Settings

```text
B-roll

Frequency

○ Low
● Medium
○ High

Preferred assets

☑ Video
☑ Images

Use AI-generated visuals as fallback
☐
```

The AI generation fallback should remain disabled by default.

---

## Animation Settings

```text
Animations

☑ Slow Zoom In
☑ Slow Zoom Out
☑ Pan Left
☑ Pan Right
☑ Fade
```

---

## SFX Settings

```text
Sound Effects

Enabled ✓

Whoosh       ✓
Pop          ✓
Click        ✓
Shutter      ✓
Notification ✓
Impact       ✓
```

---

## Audio Settings

```text
Background Music

Enabled ✓

Music Volume

8% ─────────●──── 20%

SFX Volume

10% ────────●──── 40%
```

---

## Editing Philosophy

Optional text:

```text
Editing Intensity

○ Minimal
● Social / Balanced
○ Dynamic
```

Recommended default:

```text
Social / Balanced
```

---

## Save State

After changes:

```text
✓ Style profile saved
```

Do not require a full page refresh.

---

# 15. Screen 10 — Settings

## Route

```text
/settings
```

Settings should be organized into sections.

---

## General

```text
Workspace name
Timezone
Default project behavior
```

---

## Integrations

```text
Google Drive
Connected ✓

[ Disconnect ]

AI Provider
Configured ✓

B-roll Provider
Pexels ✓
```

Never expose API keys in plaintext.

---

## Rendering

```text
Worker concurrency

4

Temporary storage

./storage
```

If a setting is developer-only, do not expose it in the normal user settings.

---

## Danger Zone

```text
Delete all generated outputs
Delete project
Disconnect integrations
```

Use strong confirmation dialogs.

---

# 16. Screen 11 — Help / System Status

## Route

```text
/help
```

This can technically be a lightweight screen.

---

## Help

Sections:

```text
How AutoEdit works
Importing videos
Understanding processing states
Managing music and SFX
Troubleshooting failed videos
```

Use concise explanations.

---

## System Status

Can be included at the bottom or as a tab.

Show:

```text
Application       ✓ Operational
Database          ✓ Operational
Processing Queue  ✓ Operational
FFmpeg Workers    ✓ Operational
Google Drive      ✓ Connected
B-roll Provider   ✓ Operational
```

If unavailable:

```text
Processing Workers
⚠ Degraded
```

Do not expose technical stack traces here.

---

# 17. Global Modal Specifications

## Process Confirmation

When user clicks Process All:

```text
Ready to process

50 videos are ready.

AutoEdit will:
✓ Transcribe videos
✓ Generate edit plans
✓ Find B-roll
✓ Add sound effects
✓ Add background music
✓ Render final videos

[ Cancel ] [ Start Processing ]
```

---

## Retry Confirmation

```text
Retry video?

This will retry the failed processing stage.

[ Cancel ] [ Retry ]
```

---

## Delete Confirmation

```text
Delete project?

This will remove the project and its generated outputs.

This action cannot be undone.

Type:
DELETE

[ Cancel ] [ Delete Project ]
```

Only use text confirmation for destructive project deletion.

---

# 18. Global Loading States

Never show blank pages while loading.

Use skeletons.

Dashboard:

```text
████████
████████████
████████
```

Project grid:

Show skeleton cards matching the actual layout.

Video player:

Show vertical player skeleton.

---

# 19. Global Empty States

Every collection must have a useful empty state.

Bad:

```text
No data.
```

Good:

```text
No videos imported yet.

Connect Google Drive and select a folder
containing your raw recordings.

[ Import Videos ]
```

Every empty state should explain the next action.

---

# 20. Global Error States

Errors should be human-readable.

Bad:

```text
HTTP 500
```

Good:

```text
Something went wrong while loading your videos.

Please try again.

[ Retry ]
```

For processing failures, show the actual stage and concise cause.

---

# 21. Notifications

Use toast notifications for small events.

Examples:

```text
✓ Project created
✓ 50 videos imported
✓ Style profile saved
✓ Video ready
✓ Processing started
```

Errors:

```text
Failed to import videos.
[ View Details ]
```

Do not overuse notifications.

---

# 22. Responsive Design

The primary target is desktop because batch video management is easier on desktop.

Still support:

- tablet
- mobile

## Mobile

Sidebar becomes a bottom/nav drawer.

Project video grid becomes:

```text
1–2 columns
```

Video preview becomes full width.

Queue table becomes cards.

Do not attempt to reproduce the desktop table exactly on mobile.

---

# 23. Design System

Use a consistent design system.

## Typography

Recommended:

- Inter
- Geist
- system sans-serif

Use one primary font.

Avoid mixing multiple decorative fonts.

---

## Radius

Use moderate rounded corners.

Recommended:

```text
8px
10px
12px
```

Avoid excessive pill-shaped UI.

---

## Buttons

Primary:

```text
[ Process All ]
```

Secondary:

```text
[ Import Videos ]
```

Danger:

```text
[ Delete ]
```

Ghost:

```text
[ Preview ]
```

---

## Status Colors

Use color semantically.

```text
Ready       green
Processing  blue
Queued      neutral
Failed      red
Warning     amber
```

Do not make the entire UI colorful.

---

# 24. Visual Hierarchy

Each page should have:

```text
Page title
↓
One-line explanation
↓
Primary CTA
↓
Important status
↓
Main content
```

Do not create multiple competing primary buttons.

---

# 25. Video Thumbnail Treatment

All video cards should use actual thumbnails from the video when available.

Thumbnail:

```text
9:16
```

Overlay:

```text
duration
status
```

Do not generate fake thumbnails.

If thumbnail generation isn't implemented yet, use a neutral video placeholder.

---

# 26. Processing Animation

Processing should feel alive but not distracting.

Use:

- progress bar
- subtle spinner
- stage label

Avoid:

- huge animated graphics
- fake percentage changes
- infinite decorative animation

Progress must reflect backend state.

---

# 27. Preview Behavior

When user clicks Preview:

Option A:

Navigate to Video Detail.

Option B:

Open a large modal if preview is short.

Recommended:

Use Video Detail for completed videos.

Use a drawer for processing status.

---

# 28. Project-Level Actions

Project header menu:

```text
Rename
Import More Videos
Process All
Retry Failed
View Results
Project Settings
Delete Project
```

Only show actions relevant to current project state.

Example:

If all videos are ready:

```text
Process All
```

should not appear.

Instead:

```text
Download All
```

---

# 29. Video-Level Actions

For a ready video:

```text
Preview
Download
Reprocess
Delete
```

For a failed video:

```text
Retry
View Error
Delete
```

For processing:

```text
View Progress
```

Do not offer actions that cannot work.

---

# 30. First-Time User Experience

On first launch:

Dashboard should show:

```text
Welcome to AutoEdit AI

Turn a folder of raw recordings into finished reels.

Step 1
Connect Google Drive

Step 2
Select your video folder

Step 3
Let AutoEdit edit everything

[ Create Your First Project ]
```

Do not create a long onboarding wizard.

---

# 31. Main Happy Path

The UI must optimize for this exact flow:

```text
Dashboard
   ↓
+ New Project
   ↓
Create Project
   ↓
Project Detail
   ↓
Import Videos
   ↓
Google Drive
   ↓
Select Folder
   ↓
Select Videos
   ↓
Import
   ↓
Project Detail
   ↓
Process All
   ↓
Processing Queue
   ↓
Batch Results
   ↓
Video Detail
   ↓
Download
```

This path should require minimal clicks.

---

# 32. Important UX Rule: Do Not Hide Progress

Because 50-video processing can take time, the user must always be able to answer:

```text
How many are done?
How many remain?
What is currently happening?
Did anything fail?
```

Therefore:

- show global project progress
- show per-video status
- show failed count
- show current stage
- preserve state after refresh

---

# 33. Important UX Rule: User Can Leave

The user should NOT need to keep the processing page open.

Example:

```text
Processing 50 videos...

You can safely leave this page.
Processing will continue in the background.
```

If browser notifications are not implemented, do not claim notifications.

When the user returns:

```text
41 videos completed while you were away.
```

---

# 34. Batch Completion State

When processing finishes:

Show a completion banner:

```text
✓ Your reels are ready.

48 of 50 videos were successfully processed.

2 videos need attention.

[ Review Results ]
```

Do not show a fake celebratory animation.

A subtle success state is enough.

---

# 35. Accessibility

Implement:

- keyboard navigation
- visible focus states
- semantic buttons
- labels for form inputs
- sufficient contrast
- aria labels for icon-only buttons
- captions/accessible labels where appropriate
- don't rely on color alone for status

---

# 36. Frontend State Architecture

Use a clear server/client separation.

Recommended:

- server fetching where practical
- React Query/TanStack Query for live job/project data if useful
- WebSocket/SSE for processing progress if implemented
- polling as a simpler fallback

For MVP, polling every few seconds is acceptable.

Do not build WebSockets solely for architectural purity.

---

# 37. Real-Time Progress

Preferred implementation:

```text
Frontend
   ↓
GET /api/projects/:id/progress
   ↓
poll every 2–5 seconds while processing
```

Stop polling when:

```text
all complete
or
no active jobs
```

Later V2 can use SSE/WebSockets.

---

# 38. Frontend Component Structure

Suggested:

```text
components/
├── layout/
│   ├── AppShell
│   ├── Sidebar
│   ├── Topbar
│   └── MobileNav
│
├── dashboard/
│   ├── StatsCards
│   ├── ActiveProcessing
│   └── ProjectCard
│
├── projects/
│   ├── ProjectHeader
│   ├── ProjectStats
│   ├── VideoGrid
│   ├── VideoCard
│   ├── VideoFilters
│   └── ProjectActions
│
├── import/
│   ├── DriveConnect
│   ├── FolderPicker
│   ├── VideoSelector
│   └── ImportSummary
│
├── queue/
│   ├── QueueHeader
│   ├── OverallProgress
│   ├── QueueList
│   ├── QueueItem
│   └── ProcessingDrawer
│
├── video/
│   ├── VideoPlayer
│   ├── VideoMetadata
│   ├── EditSummary
│   └── VideoActions
│
├── assets/
│   ├── AssetTabs
│   ├── AssetCard
│   └── UploadAssetModal
│
├── style/
│   ├── OutputSettings
│   ├── BrollSettings
│   ├── AnimationSettings
│   ├── SfxSettings
│   └── AudioSettings
│
└── common/
    ├── EmptyState
    ├── ErrorState
    ├── LoadingSkeleton
    ├── StatusBadge
    ├── ConfirmDialog
    └── Toast
```

---

# 39. UI Data Contracts

The frontend should consume real API objects.

Example project:

```typescript
type Project = {
  id: string;
  name: string;
  totalVideos: number;
  readyVideos: number;
  processingVideos: number;
  failedVideos: number;
  queuedVideos: number;
  createdAt: string;
  updatedAt: string;
};
```

Example video:

```typescript
type Video = {
  id: string;
  filename: string;
  duration: number;
  width: number;
  height: number;
  status: VideoStatus;
  progress: number;
  currentStage?: string;
  thumbnailUrl?: string;
  outputUrl?: string;
  errorMessage?: string;
};
```

Do not duplicate backend logic in the frontend.

---

# 40. Frontend Implementation Order

Cursor should implement UI in this order.

## Phase UI-1

Create:

- global layout
- sidebar
- topbar
- routing
- design tokens
- buttons
- cards
- badges
- modals
- toast
- skeletons

## Phase UI-2

Build:

- Dashboard
- Projects
- Project Detail

Use real API data.

## Phase UI-3

Build:

- Google Drive Import
- folder picker
- video selector

Connect to actual Drive API.

## Phase UI-4

Build:

- Processing Queue
- progress
- retry
- processing drawer

Connect to actual queue status.

## Phase UI-5

Build:

- Video Detail
- player
- metadata
- download
- error state

## Phase UI-6

Build:

- Batch Results
- download all
- failed section

## Phase UI-7

Build:

- Asset Library
- asset upload
- music/SFX management

## Phase UI-8

Build:

- Style Profile
- Settings
- Help
- System Status

## Phase UI-9

Responsive/accessibility pass.

## Phase UI-10

Polish and QA.

---

# 41. UI Acceptance Criteria

The UI is complete only when:

### Dashboard

- [ ] User can create a project.
- [ ] Existing projects are visible.
- [ ] Processing statistics are accurate.
- [ ] Active processing is visible.

### Project

- [ ] User can import videos.
- [ ] User can see all imported videos.
- [ ] User can filter videos.
- [ ] User can process all.
- [ ] User can open a video.

### Google Drive

- [ ] User can connect Drive.
- [ ] User can browse folders.
- [ ] User can select videos.
- [ ] User can import selected videos.
- [ ] Import progress is visible.

### Queue

- [ ] User sees total progress.
- [ ] User sees per-video progress.
- [ ] User sees current stage.
- [ ] Failed videos are clearly marked.
- [ ] Retry works.

### Video Detail

- [ ] Ready video can be played.
- [ ] Metadata is visible.
- [ ] Download works.
- [ ] Failed video shows useful error information.

### Results

- [ ] Completed videos are listed.
- [ ] Failed videos are listed.
- [ ] Download All works when implemented.

### Assets

- [ ] User can upload music.
- [ ] User can upload SFX.
- [ ] User can preview assets.
- [ ] User can enable/disable assets.
- [ ] User can delete assets.

### Style

- [ ] User can configure editing behavior.
- [ ] Changes persist.
- [ ] Planner receives the saved profile.

### Settings

- [ ] Integrations are visible.
- [ ] No secret keys are exposed.
- [ ] Destructive actions require confirmation.

---

# 42. Critical Rule for Cursor

Do not build the UI as a static mockup.

Every visible action must either:

1. work against the real backend, or
2. be clearly marked as unavailable/not implemented.

Never implement fake:

- progress
- processing
- downloads
- Google Drive connections
- video rendering
- status updates

The frontend must reflect the actual backend state.

---

# 43. Critical Rule for Design

Do not turn AutoEdit AI into a clone of Premiere Pro, CapCut, or a generic AI dashboard.

The main differentiator is simplicity.

The user should see:

```text
What do I need to do?

→ Import videos

What is happening?

→ Processing

What do I have?

→ Finished reels
```

Everything else should remain secondary.

---

# 44. Final Screen Map

The final application should feel like this:

```text
                         AUTOEDIT AI
                              │
             ┌────────────────┼────────────────┐
             │                │                │
         Dashboard         Projects          Assets
             │                │
             │                ▼
             │          Project Detail
             │                │
             │       ┌────────┼─────────┐
             │       │        │         │
             │    Import    Queue    Results
             │       │        │         │
             │       │        │         ▼
             │       │        │    Video Detail
             │       │        │
             │       ▼        │
             │   Google Drive │
             │                │
             └────────────────┼────────────────┐
                              │                │
                         Style Profile       Settings
                              │
                              ▼
                         Edit Behavior
```

---

# 45. Final User Experience

The ideal experience is:

```text
Morning:

"Today's 40 reels are ready to edit."

Open AutoEdit AI.

Click:

[ New Project ]

Select:

August Reels

Click:

[ Import ]

Click:

[ Process All ]

Leave.

Later:

Open AutoEdit AI.

48 reels ready.

Click:

[ Review Results ]

Preview.

Click:

[ Download All Ready Videos ]

Done.
```

That is the UX target.

The application should make editing feel like a background infrastructure task rather than a daily creative chore.
