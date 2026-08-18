from __future__ import annotations

import re
from dataclasses import dataclass

MusicId = str

THANK_YOU = "thank_you"
CORNFIELD = "cornfield_chase"
FEELING_BLUE = "feeling_blue"

MUSIC_IDS = (THANK_YOU, CORNFIELD, FEELING_BLUE)

LEGACY_MUSIC_MAP = {
    "energetic": FEELING_BLUE,
    "technology": FEELING_BLUE,
    "cinematic": CORNFIELD,
    "motivational": THANK_YOU,
    "chill": FEELING_BLUE,
}


@dataclass(frozen=True)
class MusicTrack:
    id: str
    file: str
    label: str
    role: str


TRACKS: tuple[MusicTrack, ...] = (
    MusicTrack(
        id=THANK_YOU,
        file="THANK YOU - INSTRUMENTAL - Tyler, The Creator.mp3",
        label="Thank You (Instrumental)",
        role="gratitude / warm / emotional payoff",
    ),
    MusicTrack(
        id=CORNFIELD,
        file="Cornfield Chase.mp3",
        label="Cornfield Chase",
        role="cinematic / dramatic / high stakes",
    ),
    MusicTrack(
        id=FEELING_BLUE,
        file="Feeling Blue.mp3",
        label="Feeling Blue",
        role="calm / reflective / general-purpose",
    ),
)

TRACK_BY_ID = {t.id: t for t in TRACKS}

GRATITUDE = re.compile(
    r"\b(thank you|thanks|grateful|gratitude|appreciate|appreciation|milestone|followers|"
    r"community|behind the scenes|bts|proud of|means the world|couldn't have)\b",
    re.I,
)
MILESTONE = re.compile(r"\b(milestone|anniversary|one year|1m|subscribers?|launched|shipped)\b", re.I)
REFLECTION = re.compile(r"\b(looking back|reflect|journey|grew|growth|learned|lesson)\b", re.I)
PERSONAL = re.compile(r"\b(i failed|my story|personal|founder|my first|i started)\b", re.I)
EMOTIONAL_END = re.compile(r"\b(thank you|love you|grateful|we did it|finally made it)\b", re.I)
POSITIVE = re.compile(r"\b(happy|excited|good news|win|success|celebrate)\b", re.I)
DRAMATIC = re.compile(
    r"\b(this changes everything|nobody saw|breaking|crisis|collapse|war|urgent|"
    r"high stakes?|against the odds|escalat)\b",
    re.I,
)
REVEAL = re.compile(
    r"\b(the secret|here's why|the truth|turns out|reveal|breakthrough|discovered|"
    r"nobody told|huge problem)\b",
    re.I,
)
CINEMATIC = re.compile(r"\b(cinematic|epic|dramatic|interstellar|ambitious|vision)\b", re.I)
TECH_BREAK = re.compile(r"\b(breakthrough|transform|revolutioniz|agi|unprecedented)\b", re.I)
BUSINESS = re.compile(r"\b(startup|revenue|crore|million|valuation|case study)\b", re.I)
AMBITION = re.compile(r"\b(ambition|dominate|scale|take over|the future of)\b", re.I)
TUTORIAL = re.compile(r"\b(how to|tutorial|step by step|click here|in this video i('ll| will) show)\b", re.I)
COMEDY = re.compile(r"\b(joke|funny|lol|comedy|skit|meme)\b", re.I)
EDUCATIONAL = re.compile(r"\b(explain|explained|learn|lesson|history of|what is)\b", re.I)
UPLIFT = re.compile(r"\b(uplift|hope|inspire|you can|keep going)\b", re.I)
DARK = re.compile(r"\b(death|tragic|dark|depress|suicide|disaster)\b", re.I)


def coerce_music_id(value: str | None) -> str:
    raw = str(value or "").strip()
    if raw in TRACK_BY_ID:
        return raw
    if raw in LEGACY_MUSIC_MAP:
        return LEGACY_MUSIC_MAP[raw]
    return FEELING_BLUE


def _score(text: str, tone: str) -> dict[str, int]:
    blob = f"{tone}\n{text}"
    scores = {THANK_YOU: 0, CORNFIELD: 0, FEELING_BLUE: 1}

    if GRATITUDE.search(blob):
        scores[THANK_YOU] += 5
        scores[CORNFIELD] -= 3
    if MILESTONE.search(blob):
        scores[THANK_YOU] += 4
    if REFLECTION.search(blob):
        scores[THANK_YOU] += 4
        scores[FEELING_BLUE] += 3
    if PERSONAL.search(blob):
        scores[THANK_YOU] += 4
        scores[FEELING_BLUE] += 2
    if EMOTIONAL_END.search(blob):
        scores[THANK_YOU] += 5
    if POSITIVE.search(blob):
        scores[THANK_YOU] += 2
        scores[FEELING_BLUE] += 4

    if DRAMATIC.search(blob):
        scores[CORNFIELD] += 5
        scores[THANK_YOU] -= 2
        scores[FEELING_BLUE] -= 3
    if REVEAL.search(blob):
        scores[CORNFIELD] += 5
        scores[FEELING_BLUE] -= 2
    if CINEMATIC.search(blob) or "cinematic" in tone.lower() or "dramatic" in tone.lower():
        scores[CORNFIELD] += 5
    if TECH_BREAK.search(blob):
        scores[CORNFIELD] += 3
    if BUSINESS.search(blob):
        scores[CORNFIELD] += 2
    if AMBITION.search(blob):
        scores[CORNFIELD] += 3

    if TUTORIAL.search(blob) or "tutorial" in tone.lower():
        scores[THANK_YOU] -= 4
        scores[CORNFIELD] -= 4
        scores[FEELING_BLUE] += 4
    if COMEDY.search(blob) or "comedy" in tone.lower() or "funny" in tone.lower():
        scores[THANK_YOU] -= 4
        scores[CORNFIELD] -= 5
        scores[FEELING_BLUE] += 2
    if EDUCATIONAL.search(blob) or "educational" in tone.lower() or "calm" in tone.lower():
        scores[FEELING_BLUE] += 4
        scores[CORNFIELD] -= 4
    if UPLIFT.search(blob):
        scores[FEELING_BLUE] += 4
    if DARK.search(blob):
        scores[FEELING_BLUE] -= 2

    if "grateful" in tone.lower() or "warm" in tone.lower():
        scores[THANK_YOU] += 3
    return scores


def choose_track(summary: str = "", tone: str = "", transcript: str = "") -> str:
    """Pick one track for the whole reel from emotion + arc, not topic alone."""
    text = f"{summary}\n{transcript}"
    scores = _score(text, tone or "")
    ranked = sorted(MUSIC_IDS, key=lambda k: scores[k], reverse=True)
    top, second = ranked[0], ranked[1]
    if scores[top] - scores[second] <= 1:
        # Close call: prefer the less dramatic track.
        if CORNFIELD in {top, second}:
            return second if top == CORNFIELD else top
        if THANK_YOU in {top, second} and FEELING_BLUE in {top, second}:
            return FEELING_BLUE
    return top
