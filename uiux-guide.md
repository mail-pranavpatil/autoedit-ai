# Eren — Your AI Social Media Guy
## UI/UX Redesign Guide, Product Plan, and Implementation Brief

> **Purpose:** This document is the source-of-truth brief for redesigning the existing Eren app, previously known as AI Video Editor. Give this file to Claude Code before implementation. Claude Code must first audit the existing codebase, produce a plan, and only then implement the redesign in small, testable stages.

---

# 1. Product Vision

Eren is an AI-powered social media assistant that turns raw footage into ready-to-publish content.

The product should feel like:

- A friendly AI social-media assistant.
- A polished, modern iOS creator app.
- Simple enough for an average iOS user.
- Powerful enough for advanced creators.
- Playful, visual, smooth, and approachable.
- Professional rather than childish.
- Focused on outcomes instead of technical editing operations.

The user should not need to understand:

- Timelines.
- Tracks.
- Codecs.
- Rendering pipelines.
- Transcription stages.
- B-roll terminology.
- Technical export settings.
- API or backend concepts.

The user should understand the following journey immediately:

> **Open Eren → Create a video → Add footage → Let Eren edit → Review → Export or Publish**

The current AI editing engine and backend capabilities are valuable. The redesign must improve the experience without unnecessarily rewriting or breaking working functionality.

---

# 2. Design References and Visual Direction

The provided visual references communicate a design language based on:

- Large rounded cards.
- Soft geometric shapes.
- Bold, expressive typography.
- Pastel lime, lavender, coral, yellow, and teal accents.
- Strong visual grouping.
- Friendly icons.
- Simple, high-contrast layouts.
- Playful but controlled color usage.
- Smooth transitions and clear interaction feedback.

Adapt this style to Eren while retaining its current dark visual foundation.

## Visual personality

Eren should feel:

- Creative.
- Intelligent.
- Helpful.
- Confident.
- Smooth.
- Modern.
- Human.
- Easy to use.

Avoid making the app feel:

- Like a developer dashboard.
- Like a terminal.
- Like a desktop video editor squeezed onto a phone.
- Like a complex admin panel.
- Like a children's game.
- Like a generic AI app with excessive gradients.

## Design system direction

| Element | Recommendation |
|---|---|
| Background | Deep charcoal rather than pure black |
| Cards | Slightly lighter charcoal with subtle borders |
| Major card radius | Approximately 20–28 px |
| Buttons | Rounded pills or generously rounded rectangles |
| Typography | iOS system font / SF Pro where available |
| Primary accent | Mint green, consistent with the current Eren UI |
| Secondary accents | Lime, lavender, coral, pale yellow, soft teal |
| Icons | Simple, rounded, consistent stroke weight |
| Spacing | 8-point spacing system |
| Motion | Subtle spring-like transitions and purposeful feedback |
| Layout | Mobile-first, responsive, safe-area aware |
| Touch targets | At least 44 × 44 pt |
| Accessibility | Dynamic Type, labels, contrast, reduced motion support |

## Color usage rules

- Do not use every accent color on every screen.
- Use bright colors for categories, presets, creative actions, and important states.
- Keep the main application shell calm.
- Do not use color alone to communicate status.
- Ensure text contrast remains accessible.
- Maintain a coherent dark theme.
- Support light theme if the existing app already supports it or if it can be added safely.
- Use color to establish hierarchy, not as decoration everywhere.

---

# 3. Core UX Principles

## 3.1 Outcome-first design

The interface should focus on what the user wants to accomplish:

- Create a video.
- Review a finished video.
- Fix a problem.
- Publish a post.
- Choose a style.

Do not make internal system concepts the main navigation structure.

## 3.2 Progressive disclosure

Show the simplest possible interface first.

Hide advanced controls until the user asks for them.

Examples:

- Show “Customize edit” instead of exposing every AI setting.
- Show “Captions” instead of immediately displaying every caption property.
- Show “Video details” as a collapsible section.
- Show technical processing logs behind “View technical details.”
- Show advanced multi-track editing behind “Advanced timeline.”

## 3.3 One dominant action per screen

Every screen should have one obvious primary action.

Examples:

- Home: **Create a video**
- Create flow: **Let Eren edit**
- Result screen: **Save to Photos**
- Publish review: **Publish now** or **Schedule**
- Editor: **Export video**

Avoid competing primary buttons such as “Export / save” and “Download video.”

## 3.4 Mobile-first behavior

- Design for narrow iPhone screens first.
- Respect safe areas and the Dynamic Island.
- Keep important actions reachable with one hand.
- Avoid desktop-style dense layouts.
- Avoid horizontal overflow.
- Use bottom sheets or focused panels for contextual controls.
- Avoid requiring precise dragging for common operations.
- Support keyboard navigation where applicable.
- Support Dynamic Type and larger accessibility text.
- Keep tap targets at least 44 × 44 pt.
- Ensure all important workflows work without hover interactions.

## 3.5 Clear system feedback

Every data-driven screen must support:

- Loading.
- Empty.
- Success.
- Error.
- Retry.
- Permission denied.
- Offline or unavailable states where relevant.
- Processing in progress.
- Partial completion.
- Destructive-action confirmation.

## 3.6 Preserve user trust

- Never show internal API URLs.
- Never show stack traces.
- Never expose runtime configuration.
- Never show fake progress in production.
- Never claim an export or upload succeeded before the backend confirms it.
- Clearly distinguish “saved locally,” “uploaded,” “scheduled,” and “published.”
- Explain permissions at the moment they are requested.
- Preserve user data during errors.

---

# 4. Information Architecture

Use five primary destinations:

1. **Home**
2. **Projects**
3. **Create**
4. **Publish**
5. **Style**

Use a standard iOS-style bottom tab bar.

The Create action should be prominent and visually distinct, but it must remain accessible and behave consistently with the platform.

## Primary navigation

### Home

Purpose:

- Show what needs attention.
- Start a new video.
- Display recent projects.
- Show ready-to-review videos.
- Show processing status.
- Show the next scheduled post.

### Projects

Purpose:

- Browse all projects.
- Search projects.
- Filter projects.
- Open a project.
- Rename, duplicate, archive, or delete a project.

### Create

Purpose:

- Start a new AI editing workflow.
- Add footage.
- Choose format and direction.
- Customize optional settings.
- Start processing.

### Publish

Purpose:

- Review publishing queue.
- Publish now.
- Schedule posts.
- View scheduled, publishing, published, and failed posts.
- Manage connected publishing accounts.

### Style

Purpose:

- Choose a creative preset.
- Manage captions, B-roll, music, motion, and brand preferences.
- Configure global defaults.
- Preview style changes.

## Secondary navigation

Place the following behind a profile or settings destination:

- Account.
- Connected services.
- Google Drive permissions.
- YouTube account management.
- Settings.
- Help.
- System status.
- Sign out.

Do not make these primary tabs.

---

# 5. Screen-by-Screen Requirements

# 5.1 Authentication / Login

## Current problems

The current login screen exposes text similar to:

- `API_URL at runtime:`
- Technical runtime information.
- A long explanation of Google Drive and implementation details.

This feels like a development build.

## Required redesign

The login screen should communicate:

> Meet Eren. Your AI social media guy.

Suggested content:

- Eren branding or logo.
- Short headline.
- One concise explanation.
- Continue with Google button.
- Optional short privacy or permissions explanation.

Suggested copy:

> From raw footage to ready-to-post content. Upload your videos and let Eren handle the edit.

## Functional requirements

- Keep Google authentication working.
- Do not expose API URLs, runtime configuration, stack traces, or internal errors.
- Show a friendly loading state during authentication.
- Show a concise retryable error if authentication fails.
- Explain Google Drive access only when the relevant permission is requested.
- Preserve the existing account and session behavior.

---

# 5.2 Home / Dashboard

## Current problems

The current dashboard gives large visual emphasis to:

- Videos.
- Ready.
- Processing.
- Failed.

These metrics are useful internally but do not help an average user decide what to do next.

A large failed count can also create anxiety without explaining what action is needed.

## Required redesign

The Home screen should prioritize:

1. Create a video.
2. Ready-to-review work.
3. Recent projects.
4. Next scheduled post.
5. Problems requiring attention.

## Suggested layout

### Header

- Greeting.
- Current date or a subtle contextual line.
- Profile button.
- Optional notification indicator.

### Hero card

Headline:

> What are we creating today?

Supporting text:

> Upload your footage and let Eren handle the edit.

Primary action:

> Create a video

### Workspace summary

Show a small number of useful summaries:

- Videos created.
- Ready to review.
- Currently processing.
- Scheduled next.

Do not let metrics dominate the screen.

### Recent projects

Each project should show:

- Thumbnail.
- Project title.
- Status.
- Duration.
- Last edited time.
- Tap target to open the project.

### Attention area

Show failed jobs only when action is required.

Use friendly labels such as:

- Needs attention.
- Could not finish.
- Retry available.
- Missing permission.

## Functional requirements

- Keep all existing dashboard data.
- Convert technical states into friendly presentation labels.
- Use real backend data.
- Support loading, empty, and error states.
- Add navigation to the relevant project or action.
- Make Create a video the dominant action.

---

# 5.3 Projects

## Current problems

The current project list includes:

- Large empty cards.
- Repeated project names.
- Visible Delete actions on every card.
- No strong visual identity.
- Limited information for identifying a project.

## Required redesign

Use visual project cards.

Each card should show:

- Video thumbnail or generated placeholder.
- Project title.
- Duration.
- Status badge.
- Last edited time.
- Optional publishing state.
- Chevron or clear open affordance.

Suggested status labels:

- Draft.
- Processing.
- Ready to review.
- Scheduled.
- Published.
- Needs attention.
- Failed.

## Interactions

Tapping a card opens the project.

Secondary actions should live inside a context menu or swipe action:

- Rename.
- Duplicate.
- Archive.
- Delete.

Delete must:

- Be visually secondary.
- Require confirmation.
- Explain the consequence.
- Avoid accidental activation.

## Filters

Provide useful filters such as:

- All.
- Drafts.
- Processing.
- Ready.
- Scheduled.
- Published.
- Failed.

Use only filters supported by the actual data model.

## Search

Search should support:

- Project title.
- File name.
- Relevant metadata if available.

## Functional requirements

- Preserve all existing project operations.
- Do not lose access to projects with duplicate names.
- Show creation date or another secondary identifier when titles repeat.
- Use real thumbnails where available.
- Keep list performance acceptable for larger project libraries.
- Support empty search results.

---

# 5.4 Create Video Flow

This is the most important user journey in the app.

The flow should be guided rather than form-heavy.

Use three simple steps:

1. Add footage.
2. Choose direction.
3. Review and start.

## Step 1: Add footage

Support existing import sources:

- iPhone Photos.
- Files.
- Google Drive.
- Existing supported folder import.

Show selected footage with:

- Thumbnail.
- File name.
- Duration.
- Selection state.
- Remove action.
- Number of selected clips.

Allow multiple clips where supported.

Use friendly copy:

> Add your videos

> Choose clips from your iPhone or import a folder from Google Drive.

## Step 2: Choose direction

Use visual cards rather than technical selectors.

Suggested options:

- Reel — 9:16.
- YouTube — 16:9.
- Surprise me — AI chooses.

The actual supported formats must be verified against the current backend.

Optional customization should be hidden behind:

> Customize edit

Possible options:

- Style preset.
- Caption preset.
- Music.
- B-roll preference.
- Output quality.
- Brand kit.

Do not expose every option by default.

## Step 3: Review and start

Show a simple summary:

> 3 clips · Vertical reel · Auto captions · Cinematic style

Primary action:

> Let Eren edit

Before starting, confirm:

- Selected clips.
- Output format.
- Active style.
- Optional settings.
- Project name if required.

## Functional requirements

- Preserve current upload and import APIs.
- Do not create fake file selection behavior.
- Handle permissions and denied access.
- Handle upload progress.
- Handle partial upload failure.
- Allow removing selected clips.
- Prevent accidental duplicate submissions.
- Show a clear confirmation or processing transition after the request is accepted.

---

# 5.5 Processing Screen

## Current problems

The current screen resembles a terminal log.

It shows internal stages such as:

- Transcript.
- Thinking.
- Edit plan.
- Stock search.
- Assets.
- Render.
- Written.
- Validate.
- Done.

This may be useful for debugging but is intimidating as the default experience.

## Required redesign

Use a friendly progress screen.

Suggested headline:

> Eren is editing your video ✨

Suggested supporting copy:

> Eren is choosing the best moments, adding visuals, and preparing your edit.

Show:

- Project title.
- Progress percentage when real progress is available.
- Current step.
- Completed steps.
- Honest indeterminate progress when percentage is unavailable.
- Estimated time only if the system can calculate it reliably.

Suggested user-facing stages:

1. Understanding your footage.
2. Planning the edit.
3. Finding matching visuals.
4. Adding captions and sound.
5. Rendering your video.
6. Checking the final result.

## Technical details

Keep the existing detailed logs behind:

> View technical details

Technical logs should be useful for debugging but not the default presentation.

## Functional requirements

- Use real backend progress.
- Never show fake percentages in production.
- Support indeterminate progress.
- Allow leaving the screen while processing continues.
- Preserve processing state across navigation.
- Show notifications or in-app updates when processing finishes if supported.
- Provide retry and recovery actions.
- Explain failure in plain language.
- Preserve logs for support/debugging.

---

# 5.6 Editor

The editor requires the largest interaction-model improvement.

## Current problems

The current editor behaves like a desktop editor compressed into a mobile screen.

Problems include:

- Media, inspector, timeline, and actions compete for space.
- The timeline is difficult to understand on a phone.
- The inspector is always visible.
- Caption styles are dense.
- Export actions compete.
- Users need to understand editing terminology.

## Required redesign: preview-first mobile editor

The video preview must be the primary focus.

## Top bar

Include:

- Back.
- Project title.
- Undo.
- Redo.
- Preview/fullscreen.
- More actions.

Do not overcrowd the top bar.

## Main preview

Show:

- Large 9:16 preview where appropriate.
- Playback controls.
- Current time.
- Total duration.
- Accurate caption rendering.
- B-roll and overlays as they will appear in the export.

The preview should be as close as practical to the final render.

## Contextual editing tools

Use a horizontal tool strip or bottom action area:

- Captions.
- Visuals.
- Music.
- Transitions.
- Speed.
- Canvas.
- More.

Each tool should open a focused panel or bottom sheet.

Do not show the entire inspector at once.

## Captions

The caption editing experience should support the existing capabilities, including where available:

- Show/hide captions.
- Caption style selection.
- Font.
- Color.
- Size.
- Position.
- Animation.
- Timing.
- Preview.

Use visual style cards instead of dense controls.

## Visuals

The visuals panel should support:

- B-roll.
- Photos.
- Video overlays.
- Asset replacement.
- Visual timing where supported.
- Visual treatment or animation where supported.

## Music and sound

The sound panel should support:

- Music selection.
- Audio preview.
- Volume.
- Sound effects where supported.
- Mute or disable options where supported.

## Timeline

Keep the timeline, but make it secondary.

Default behavior:

- Compact timeline.
- Simple sequence view.
- Clear playhead.
- Large touch targets.
- Easy segment selection.

Advanced behavior:

- “Advanced timeline” mode.
- Multi-track view.
- A-roll, B-roll, captions, and music tracks.
- Precise editing for advanced users.

Do not force beginners to use a multi-track timeline.

Avoid requiring precise dragging for common operations. Provide accessible alternatives such as:

- Select segment.
- Set start.
- Set end.
- Split.
- Replace.
- Move earlier/later.
- Delete.

## Export

Use one primary action:

> Export video

After export, provide:

- Save to Photos.
- Share.
- Publish to YouTube.
- Download file if supported.
- Continue editing.

Do not show “Export / save” and “Download video” as competing primary actions.

## Functional requirements

- Preserve the existing editor data model.
- Preserve existing editing operations.
- Ensure changes are saved correctly.
- Support undo/redo if already available.
- Maintain accurate preview state.
- Handle unsaved changes.
- Prevent accidental loss of edits.
- Support loading and rendering states.
- Keep advanced editing available without making it the default.

---

# 5.7 Export / Result Screen

## Current problems

The current result screen contains useful information but gives too much prominence to technical details.

The preview should be the main focus.

## Required redesign

Suggested hierarchy:

1. Finished video preview.
2. “Your video is ready.”
3. Video title and status.
4. Main next action.
5. Secondary actions.
6. Collapsible technical details.

## Primary actions

Depending on the current state:

- Save to Photos.
- Publish to YouTube.
- Continue editing.

Use the most relevant action as primary.

## Secondary sections

Collapsible sections:

- Video details.
- Export settings.
- AI edit summary.

Technical details may include:

- Duration.
- Resolution.
- Aspect ratio.
- Codec.
- Audio details.
- File size.
- Export location.

These should not dominate the screen.

## Functional requirements

- Show the actual rendered video.
- Do not claim readiness before validation succeeds.
- Handle failed export.
- Provide retry.
- Preserve access to the editor.
- Support sharing and saving where supported.
- Make publishing status distinct from local export status.

---

# 5.8 Style Studio

The current Style Profile is too much like a technical settings form.

It should feel like a creative identity studio.

## Required redesign

Show:

- Active style.
- Visual style preview.
- Preset tiles.
- Short descriptions.
- Customize action.
- Clear indication of which style is active.

Suggested presets:

- Clean creator — minimal and modern.
- High energy — fast and punchy.
- Cinematic — moody and expressive.
- Bright and fun — playful and colorful.

These are starting concepts. Confirm which presets can actually be supported by the current system.

## Style settings

Organize advanced settings into:

1. Output.
2. Visual style.
3. Captions.
4. B-roll.
5. Music and sound.
6. Brand kit.

## Output

Possible settings:

- Aspect ratio.
- Resolution.
- Quality.

## Visual style

Possible settings:

- Preset.
- Zoom.
- Pan.
- Fade.
- Motion intensity.
- Visual treatment.

## Captions

Possible settings:

- Caption style.
- Font.
- Color.
- Size.
- Position.
- Animation.
- Default visibility.

## B-roll

Possible settings:

- Frequency.
- Type.
- Full-screen or overlay behavior.
- Visual source preferences.

## Music and sound

Possible settings:

- Default music.
- Volume.
- Sound effects.
- Audio behavior.

## Brand kit

Possible settings:

- Logo.
- Colors.
- Fonts.
- Watermark.
- Default branding.

## Important behavior

The global style profile defines defaults.

Per-video overrides must remain separate.

Changing the style for one video must not silently change the global profile.

## Functional requirements

- Preserve existing style settings and API contracts.
- Show live or representative previews where practical.
- Clearly indicate unsaved changes.
- Support Save and Cancel.
- Support reset to defaults.
- Avoid silently changing existing projects unless explicitly intended.

---

# 5.9 Asset Library

## Current problems

The current asset library resembles an audio file manager.

It is functional but not especially visual or approachable.

## Required redesign

Use category tiles inspired by the visual references.

Suggested categories:

- Music.
- Sound effects.
- B-roll.
- Brand assets.

Each category should have:

- A distinct but controlled accent color.
- A clear icon.
- A short description.
- A count where available.

## Asset cards

Each asset card should show:

- Name.
- Type.
- Preview.
- Duration where relevant.
- File size where relevant.
- Source: system or user.
- Enabled/disabled state.
- Favorite state if supported.

## Interactions

Support existing operations:

- Upload.
- Search.
- Filter.
- Preview.
- Enable/disable.
- Rename.
- Replace.
- Delete.
- Use in project.

Put destructive and less frequent operations in a context menu.

## Audio assets

Where practical, show:

- Play button.
- Waveform or progress indicator.
- Duration.
- Current playback position.

## Video/image assets

Where practical, show:

- Thumbnail.
- Aspect ratio.
- Duration for video.
- Source information.

## Functional requirements

- Preserve system assets.
- Clearly distinguish system assets from user assets.
- Preserve existing upload and storage behavior.
- Handle upload failures.
- Handle unsupported file types.
- Avoid loading all large assets at once.
- Use pagination or lazy loading if necessary.

---

# 5.10 Publish / YouTube

## Current problems

The current YouTube screen uses a table that is difficult to read on a mobile device.

## Required redesign

Use a visual publishing queue.

Each publishing card should show:

- Thumbnail.
- Video title.
- Platform.
- Scheduled time.
- Timezone.
- Status.
- Project reference.
- Primary action.

## Suggested statuses

- Draft.
- Ready to review.
- Scheduled.
- Publishing.
- Published.
- Failed.
- Needs attention.

## Publishing workflow

1. Select a finished video.
2. Choose YouTube.
3. Review title.
4. Review description.
5. Review thumbnail.
6. Choose visibility.
7. Choose Publish now or Schedule.
8. Confirm.
9. Show publishing status in the queue.

## Scheduling

Use a mobile-friendly date and time picker.

Make timezone explicit.

Preserve the configured timezone behavior. Do not hardcode IST unless that is genuinely the user's configured setting.

## Failed publishing

Provide:

- Plain-language explanation.
- Retry.
- Edit post.
- Reconnect account if needed.
- View details.

## Functional requirements

- Preserve YouTube authentication.
- Preserve publishing APIs.
- Preserve scheduling behavior.
- Preserve existing metadata behavior.
- Do not claim a video is published before confirmation.
- Support duplicate prevention where appropriate.
- Keep publishing status separate from editing/export status.

---

# 5.11 Side Menu and Settings

The current hamburger menu contains too many destinations.

## Required redesign

Use bottom-tab navigation for primary tasks.

Use a profile/settings area for:

- Account.
- Connected services.
- Google Drive.
- YouTube account.
- Preferences.
- Notifications.
- Help.
- System status.
- Sign out.

## Settings principles

- Group related settings.
- Use standard iOS list patterns.
- Explain dangerous actions.
- Avoid exposing technical configuration.
- Show connection status clearly.
- Provide reconnect actions.
- Make sign out secondary and confirm if appropriate.

---

# 6. Reusable Component Architecture

Build a consistent component system before implementing every screen.

Suggested components:

- `ErenAppShell`
- `ErenTabBar`
- `ErenButton`
- `ErenCard`
- `ErenSectionHeader`
- `ErenStatusBadge`
- `ErenThumbnail`
- `ErenProjectCard`
- `ErenAssetCard`
- `ErenPublishCard`
- `ErenStyleTile`
- `ErenBottomSheet`
- `ErenActionSheet`
- `ErenProgressView`
- `ErenEmptyState`
- `ErenErrorState`
- `ErenLoadingState`
- `ErenConfirmationDialog`
- `ErenMediaPicker`
- `ErenPreviewPlayer`
- `ErenTimeline`
- `ErenToolStrip`
- `ErenSettingsRow`
- `ErenPermissionNotice`

Use the existing framework's naming conventions if they differ.

## Component requirements

Every reusable component should have:

- Clear states.
- Consistent spacing.
- Accessible labels.
- Loading behavior where relevant.
- Error behavior where relevant.
- Responsive behavior.
- Dark-theme support.
- Reduced-motion support where relevant.

---

# 7. Data and Backend Preservation

Before changing UI, map the existing functionality.

The redesign must preserve:

- Authentication.
- Session handling.
- Project creation.
- Project deletion.
- Project renaming.
- Project duplication if supported.
- Video upload.
- Google Drive import.
- Processing jobs.
- Transcription.
- Edit planning.
- B-roll search.
- Asset downloads.
- Rendering.
- Validation.
- Export.
- Local saving.
- Sharing.
- YouTube connection.
- YouTube scheduling.
- YouTube publishing.
- Style profiles.
- Asset library operations.
- Existing editor operations.

## Rules

- Reuse existing API contracts where possible.
- Do not replace working backend logic with fake data.
- Do not silently change data semantics.
- Do not remove functionality because it is not visible in the first redesign pass.
- Preserve backwards compatibility with existing projects.
- Add adapters only when needed.
- Keep UI state separate from backend state.
- Use real status transitions.
- Handle race conditions and duplicate submissions.

---

# 8. Implementation Plan for Claude Code

Claude Code must follow this order.

## Phase 0: Audit before implementation

Inspect the codebase and identify:

- Framework.
- Entry points.
- Routing.
- Navigation.
- State management.
- Shared components.
- API clients.
- Authentication.
- Project models.
- Video models.
- Processing jobs.
- Editor architecture.
- Asset library.
- Style profile.
- YouTube integration.
- File import.
- Storage.
- Existing tests.
- Existing mobile/responsive behavior.

Produce a concise audit report before making major changes.

## Phase 1: Feature map and migration plan

Create a table mapping:

| Existing feature/action | Current location | New location | API/state dependency | Risk |
|---|---|---|---|---|

Every existing user action must have a destination in the redesigned app.

Identify:

- Features that can be moved directly.
- Features that need adapters.
- Features that need new UI.
- Features that need backend changes.
- Features that are risky to modify.

## Phase 2: Design foundation

Build:

- Design tokens.
- Colors.
- Typography hierarchy.
- Spacing.
- Radius.
- Buttons.
- Cards.
- Status badges.
- Bottom sheets.
- Empty states.
- Error states.
- Loading states.
- Tab bar.
- Shared project/asset/publish cards.

Do not begin by independently styling every screen.

## Phase 3: New app shell

Implement:

- Home.
- Projects.
- Create.
- Publish.
- Style.
- Profile/settings entry point.
- Safe-area handling.
- Responsive layout.

Verify navigation before proceeding.

## Phase 4: Home and Projects

Implement:

- Action-first Home.
- Recent projects.
- Visual project cards.
- Search.
- Filters.
- Context menus.
- Safe deletion flow.
- Loading, empty, and error states.

## Phase 5: Create flow

Implement:

- Add footage.
- Source selection.
- Selected media list.
- Format selection.
- Optional customization.
- Review summary.
- Start processing.

Test:

- Single clip.
- Multiple clips.
- Cancelled selection.
- Permission denial.
- Upload failure.
- Duplicate submission.
- Empty selection.

## Phase 6: Processing and result

Implement:

- Friendly progress screen.
- Real progress.
- Current stage.
- Technical details disclosure.
- Background navigation behavior.
- Completion state.
- Retry state.
- Finished video result screen.

## Phase 7: Editor

Implement in small increments:

1. Preview-first shell.
2. Playback controls.
3. Contextual tool strip.
4. Captions panel.
5. Visuals panel.
6. Music panel.
7. Compact timeline.
8. Advanced timeline.
9. Export flow.
10. Unsaved-change protection.

Do not remove the existing editor until the new editor supports the required workflows.

## Phase 8: Style and Assets

Implement:

- Visual style presets.
- Style editor.
- Global defaults.
- Per-video overrides.
- Asset categories.
- Asset cards.
- Upload and preview.
- Context menus.
- Search and filtering.

## Phase 9: Publish

Implement:

- Publishing queue.
- Review post.
- Publish now.
- Scheduling.
- Status cards.
- Failed publishing recovery.
- Account management.

## Phase 10: QA and polish

Test:

- Narrow iPhone-sized screens.
- Larger iPhones.
- Wider screens.
- Dark theme.
- Light theme if supported.
- Dynamic Type.
- Keyboard navigation where applicable.
- Screen reader labels.
- Reduced motion.
- Slow network.
- Offline state.
- Authentication failure.
- Upload failure.
- Processing failure.
- Export failure.
- YouTube failure.
- Empty data.
- Long titles.
- Duplicate titles.
- Large asset libraries.
- Long video names.
- Long processing jobs.

---

# 9. Acceptance Criteria

The redesign is successful when an average iOS user can:

## First-use experience

- Understand what Eren does immediately.
- Sign in without seeing technical information.
- Find the Create action without searching.
- Understand the difference between Projects and Publish.

## Create workflow

- Select footage without confusion.
- Understand the output format.
- Start an AI edit confidently.
- See honest progress.
- Leave the processing screen without interrupting the job.

## Review workflow

- Recognize when a video is ready.
- Preview the result.
- Save or share the result.
- Continue editing if necessary.

## Editing workflow

- Change captions.
- Change visuals.
- Change music.
- Understand where to find advanced editing.
- Export without confusion.

## Publishing workflow

- Review a post.
- Publish immediately.
- Schedule a post.
- Understand the current publishing status.
- Recover from a failed upload.

## Overall UX

- No critical action is hidden behind technical terminology.
- No screen feels like a desktop app squeezed onto a phone.
- Destructive actions are protected.
- Loading and error states are understandable.
- Existing functionality remains available.
- The UI feels consistent across all screens.
- The app feels playful and polished without sacrificing clarity.

---

# 10. Claude Code Operating Instructions

Use the following rules while implementing:

1. **Inspect first.** Do not make major assumptions about the codebase.
2. **Plan before coding.** Provide the audit and migration plan first.
3. **Preserve functionality.** Do not rewrite working backend logic without a clear reason.
4. **Implement in stages.** Make small, testable changes.
5. **Do not use fake data in production.**
6. **Do not expose technical internals to normal users.**
7. **Do not remove existing features.**
8. **Use reusable components.**
9. **Test every screen at iPhone widths.**
10. **Test all loading, empty, success, and error states.**
11. **Use real backend status and progress.**
12. **Keep global style defaults separate from per-video settings.**
13. **Keep editing status separate from export and publishing status.**
14. **Protect destructive actions.**
15. **Do not overuse color or animation.**
16. **Do not make advanced editing the default experience.**
17. **Verify all existing workflows after each major phase.**
18. **If a backend limitation prevents a UI feature, explain it and implement the best truthful fallback rather than simulating behavior.**

---

# 11. Initial Prompt to Give Claude Code

You are redesigning **Eren — Your AI Social Media Guy**, an existing AI video editing and social publishing application.

The attached `uiux-guide.md` is the product and UX source of truth.

Your first task is **not to code immediately**.

First:

1. Inspect the entire existing codebase.
2. Identify the framework, routing, state management, shared components, API contracts, authentication, project model, processing pipeline, editor, assets, style profile, and YouTube publishing system.
3. Map every existing user-facing action to its current implementation.
4. Identify what can be reused and what needs to change.
5. Identify risks and backend dependencies.
6. Produce:
   - A concise codebase audit.
   - A feature-preservation map.
   - A proposed component architecture.
   - A screen-by-screen migration plan.
   - A phased implementation plan.
   - A testing strategy.
7. Wait for approval before making major implementation changes.

After approval, implement the redesign in small stages.

The primary objective is not merely to restyle the current screens. Redesign the information architecture and interaction model so that an average iOS user can create, edit, review, export, and publish content without understanding video-editing terminology.

Preserve existing backend behavior and all important functionality. Use the guide's visual direction: rounded cards, playful but professional pastel accents, strong typography, smooth interactions, and a refined dark iOS-first interface.

Do not expose API URLs, runtime configuration, stack traces, fake progress, or internal technical logs to normal users.

---

# 12. Final Product Principle

The redesign should make Eren feel like:

> **A capable creative assistant that does the hard work for you.**

The user should think:

> “I just need to give Eren my footage and tell it what kind of content I want.”

The user should not think:

> “I need to learn how this video editor works before I can use it.”

The backend can remain sophisticated. The interface should not make the user feel that sophistication.
