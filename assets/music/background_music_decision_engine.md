# Background Music Decision Engine

## Purpose

The AI video editor has exactly three background music tracks available.

The AI must choose the most appropriate track based on the reel's emotional tone, narrative arc, pacing, subject matter, and ending.

Do NOT randomly select a track.
Do NOT select music based only on keywords/topic.

Primary question:

> What should the viewer feel while watching this reel?

---

# MUSIC LIBRARY

## Track 1 — Thank You (Instrumental)

### Emotional profile
Warm, emotional, grateful, wholesome, reflective, peaceful, personal.

### Best for
- Gratitude
- Appreciation
- Personal milestones
- Journey recap
- Community/follower appreciation
- Success with an emotional payoff
- Behind-the-scenes
- Personal achievements
- Positive reflection
- Emotional closing

### Narrative arc
Journey → progress → achievement → gratitude

or

Struggle → progress → emotional payoff

### Strong signals
- Thank-you messages
- Milestones
- Personal journeys
- Community appreciation
- Emotional endings
- Reflection on progress

### Avoid
- Aggressive/high-energy content
- Fast tutorials
- Technical demonstrations
- Dark/negative stories
- High-stakes news
- Comedy
- Suspense-heavy content

---

# Track 2 — Cornfield Chase (Interstellar / Hans Zimmer)

### Emotional profile
Cinematic, dramatic, urgent, expansive, tense, ambitious, awe-inspiring.

### Best for
- Dramatic storytelling
- High-stakes stories
- Major revelations
- AI/technology breakthroughs
- Business case studies
- Ambitious goals
- "This changes everything" content
- Future/vision content
- Against-the-odds stories
- Rapid escalation
- Cinematic storytelling
- Big discoveries

### Narrative arc
Setup → tension → escalation → major reveal

or

Problem → increasing stakes → breakthrough

### Strong signals
- Major stakes
- Unexpected breakthrough
- Dramatic reveal
- Large-scale technology/business story
- "Everything changed"
- "Nobody saw this coming"
- Significant consequences
- Strong escalation

### Avoid
- Casual talking-head content
- Simple tutorials
- Light comedy
- Romantic/personal content
- Simple listicles
- Calm educational explanations
- Gratitude-focused content

IMPORTANT:
Do not choose this track just because the video is about AI or technology. The content must also have a cinematic/dramatic narrative.

---

# Track 3 — Feeling Blue

### Emotional profile
Calm, slightly melancholic, reflective, spacious, understated. General-purpose bed.

The file is `Feeling Blue.mp3`. Do not treat it as the same warm-gratitude profile as Track 1.

### Best for
- Positive storytelling
- General creator content
- Light emotional content
- Reflective content
- Uplifting content
- Simple personal stories
- Calm educational content
- Positive conclusions

Do NOT assume it has the same emotional profile as Track 1.

---

# DECISION TREE

## Step 1
Is the reel primarily gratitude, appreciation, milestone, reflection, or emotional payoff?

YES → Track 1

NO → Continue.

## Step 2
Is there strong dramatic escalation, tension, high stakes, or a major reveal?

YES → Track 2

NO → Continue.

## Step 3
Is the reel primarily positive, calm, reflective, uplifting, or general-purpose?

YES → Track 3

NO → Continue.

## Step 4
Does the story have a strong emotional ending or gratitude payoff?

YES → Track 1

NO → Continue.

## Step 5
Does the story progressively build toward a consequential reveal?

YES → Track 2

NO → Track 3

---

# EMOTIONAL ARC > TOPIC

Do NOT classify music only by subject.

Example:

### AI video
"AI is going to completely transform medicine."

Dramatic + escalating stakes → Track 2

Calm educational explanation → Track 3

Personal founder journey → Track 1 or Track 3 depending on ending

### Business story
"Startup went from ₹0 to ₹10 crore."

Dramatic growth story → Track 2

Founder emotional journey → Track 1

Straightforward case study → Track 3

### Personal story
"I failed my first startup."

Sad/reflection-focused → Track 1 or Track 3

Comeback with strong escalation → Track 2

Ends with gratitude → Track 1

---

# MUSIC SCORING

Conceptually calculate:

music_score =
    emotional_match
    + narrative_arc_match
    + pacing_match
    + ending_match
    + intensity_match
    + audience_feeling_match
    - topic_only_penalty
    - repetition_penalty

Select the highest-scoring track.

If the top two tracks are very close, prefer the less dramatic track.

---

# STARTING HEURISTICS

## Track 1
Gratitude +5
Milestone +4
Reflection +4
Personal journey +4
Emotional ending +5
Positive story +2
Dramatic escalation -2
Fast tutorial -4
Comedy -4

## Track 2
Dramatic escalation +5
High stakes +5
Major reveal +5
Cinematic storytelling +5
Technology breakthrough +3
Business case study +2
Ambition +3
Calm tutorial -4
Comedy -5
Gratitude -3
Casual talking head -3

## Track 3
Positive/general content +4
Calm educational +4
Reflective +3
Uplifting +4
Light storytelling +4
Personal story +2
Major dramatic reveal -2
High-stakes cinematic story -3
Dark/negative content -2

These are starting heuristics, not absolute rules.

---

# ONE-TRACK-PER-REEL RULE

For a normal 30–90 second reel:

Prefer ONE background music track for the entire reel.

Do NOT switch tracks every time the emotional tone changes slightly.

Only change tracks when there is a major narrative transformation.

If switching tracks:
- use a smooth crossfade
- avoid an abrupt music cut
- preserve dialogue clarity

---

# MUSIC VOLUME

Dialogue always has priority.

Starting point:

- Background music: approximately -24 dB to -18 dB under normal speech
- During dialogue pauses: music may rise slightly
- During emotional moments: music may rise modestly
- During important speech: duck music

Never allow music to mask speech.

---

# FINAL RULE

The AI should NOT think:

"This is an AI video, so use Cornfield Chase."

It should think:

"This is an AI video with escalating stakes and a major reveal, therefore Cornfield Chase is appropriate."

Final decision must be based on:

EMOTION + STORY ARC + PACING + INTENSITY + ENDING

not merely the topic.
