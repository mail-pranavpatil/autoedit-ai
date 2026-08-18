from __future__ import annotations

import logging
import re

from autoedit.edit_schema import EditPlan, EditSegment, merge_style_profile, plan_duration

logger = logging.getLogger("autoedit")

STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "this",
    "that",
    "it",
    "is",
    "are",
    "was",
    "be",
    "i",
    "we",
    "you",
    "my",
    "our",
    "so",
    "just",
    "like",
    "really",
    "very",
    "um",
    "uh",
    "gonna",
    "going",
    "about",
    "from",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "not",
    "if",
    "then",
    "than",
    "as",
    "at",
    "by",
}

MIN_TALK_BETWEEN_BROLL = 1.2
MIN_BROLL = 2.0
MAX_BROLL = 3.0


def cadence_seconds(style: dict | None) -> float:
    profile = merge_style_profile(style)
    raw = profile.get("visual_cadence_seconds")
    freq = str(profile.get("broll_frequency") or "medium")
    fallback = {"high": 2.0, "low": 3.5}.get(freq, 2.5)
    try:
        value = float(raw if raw is not None else fallback)
    except (TypeError, ValueError):
        value = fallback
    return min(4.0, max(1.6, value))


def words_from_transcript(transcript: dict | None) -> list[dict]:
    words: list[dict] = []
    for seg in (transcript or {}).get("segments") or []:
        raw = seg.get("words") or []
        if raw:
            for item in raw:
                text = str(item.get("text") or item.get("word") or "").strip()
                if not text:
                    continue
                words.append(
                    {
                        "text": text,
                        "start": float(item.get("start") or 0),
                        "end": float(item.get("end") or 0),
                    }
                )
            continue
        text = str(seg.get("text") or "").strip()
        if text:
            words.append(
                {
                    "text": text,
                    "start": float(seg.get("start") or 0),
                    "end": float(seg.get("end") or 0),
                }
            )
    return words


def query_from_window(transcript: dict | None, start: float, end: float) -> str:
    picked: list[str] = []
    for word in words_from_transcript(transcript):
        if word["end"] < start or word["start"] > end:
            continue
        token = re.sub(r"[^a-zA-Z0-9]+", "", word["text"]).lower()
        if not token or token in STOPWORDS or len(token) < 3:
            continue
        if token not in picked:
            picked.append(token)
        if len(picked) >= 6:
            break
    query = " ".join(picked[:6]).strip() or "vertical lifestyle b-roll"
    return query[:80]


def insert_broll_window(segments: list[EditSegment], start: float, end: float, query: str) -> list[EditSegment]:
    start = round(start, 3)
    end = round(end, 3)
    if end - start < 1.6:
        return segments
    rebuilt: list[EditSegment] = []
    placed = False
    for seg in segments:
        if seg.end <= start + 0.02 or seg.start >= end - 0.02:
            rebuilt.append(seg)
            continue
        if seg.start < start - 0.02:
            rebuilt.append(seg.model_copy(update={"end": start}))
        if not placed:
            rebuilt.append(
                EditSegment(
                    start=start,
                    end=end,
                    visual="broll",
                    broll_query=query,
                    broll_type="video",
                    effect="fade_in",
                    sfx=None,
                )
            )
            placed = True
        if seg.end > end + 0.02:
            rebuilt.append(seg.model_copy(update={"start": end, "visual": "talking_head"}))
    if not placed:
        rebuilt.append(
            EditSegment(
                start=start,
                end=end,
                visual="broll",
                broll_query=query,
                broll_type="video",
                effect="fade_in",
                sfx=None,
            )
        )
    rebuilt.sort(key=lambda s: s.start)
    return [s for s in rebuilt if s.end - s.start >= 0.15]


def _occupied(plan: EditPlan) -> list[tuple[float, float]]:
    return [(s.start, s.end) for s in plan.segments if s.visual == "broll"]


def _uncovered_runs(plan: EditPlan, duration: float) -> list[tuple[float, float]]:
    occupied = sorted(_occupied(plan))
    runs: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in occupied:
        if start > cursor + 0.05:
            runs.append((cursor, start))
        cursor = max(cursor, end)
    if duration > cursor + 0.05:
        runs.append((cursor, duration))
    return runs


def enforce_visual_cadence(plan: EditPlan, transcript: dict | None, style: dict | None) -> EditPlan:
    cadence = cadence_seconds(style)
    max_gap = cadence + 0.4
    duration = plan_duration(plan)
    if duration < 4:
        return plan
    working = plan.model_copy(update={"segments": list(plan.segments)})

    for _ in range(24):
        runs = [r for r in _uncovered_runs(working, duration) if r[1] - r[0] > max_gap]
        if not runs:
            break
        start, end = runs[0]
        pad = MIN_TALK_BETWEEN_BROLL if start > 0.05 else 0.15
        insert_start = start + pad
        room = end - insert_start
        if room < MIN_BROLL:
            break
        insert_dur = min(MAX_BROLL, max(MIN_BROLL, cadence))
        if insert_start + insert_dur + MIN_TALK_BETWEEN_BROLL > end:
            insert_dur = max(MIN_BROLL, end - insert_start - MIN_TALK_BETWEEN_BROLL)
        insert_end = insert_start + insert_dur
        if insert_end > end:
            insert_end = end
        if insert_end - insert_start < MIN_BROLL:
            break
        query = query_from_window(transcript, insert_start, insert_end)
        segments = insert_broll_window(working.segments, insert_start, insert_end, query)
        working = working.model_copy(update={"segments": segments})

    return working
