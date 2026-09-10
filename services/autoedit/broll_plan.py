"""Dense, literal, per-phrase image B-roll planning.

Two steps, run right after ``enforce_visual_cadence`` in the pipeline:

1. :func:`plan_image_queries` - one GPT call turns the ordered caption phrases
   into one literal image-search query per phrase (or ``None`` to skip).
2. :func:`build_dense_broll` - rewrites ``plan.segments`` so nearly every phrase
   gets its own full-screen image B-roll segment, while any existing
   ``broll_type == "video"`` spans (from the main planner / cadence pass) are
   left untouched.
"""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from autoedit.edit_schema import EditPlan, EditSegment, plan_duration

logger = logging.getLogger("autoedit")

_SYS = "You output strictly valid JSON: {\"queries\": [...]} and nothing else."

_PROMPT = """You choose ONE image-search query for EACH spoken phrase of a vertical
talking-head video. The image fills the screen while that phrase is spoken.

STEP 1 - name the video's subject in your head from the summary + transcript
(e.g. "Stripe acquiring OpenRouter", "making money with YouTube Playables").
STEP 2 - for every phrase, give a 2-5 word query for something a viewer should
SEE at that moment. It must be concrete and ON THAT SUBJECT.

COVERAGE IS REQUIRED: fill at least 85% of phrases with a real query. Most
phrases have no concrete noun of their own - that's expected. For those, pick a
visual from the video's subject or the current point being made:
  "he sold it for 1.5 billion"      -> "startup acquisition headline"
  "and this is the crazy part"       -> "stripe openrouter logos"
  "the same founder did it twice"    -> "tech founder portrait"
  "let me explain his strategy"      -> "business strategy whiteboard"
Prefer named companies/products (their logo, website, or UI), real photos,
screenshots, charts, headlines. NO "vector", "clipart", "illustration",
"concept", or "background" queries.

Return JSON null ONLY for a phrase that is pure filler with nothing to show
("so", "um", "you know", "right", "okay so"). Aim for at most 1 null per 6
phrases.

Output EXACTLY {n} array elements, phrase order preserved.

Video subject summary: {summary}
Tone: {tone}
Full transcript: {full_text}

Phrases (index: text):
{phrase_lines}

Return: {{"queries": ["<query or null>", ...]}}
"""


def plan_image_queries(
    phrases: list[dict],
    video_summary: str,
    tone: str,
    full_text: str,
    settings,
) -> list[str | None]:
    """One GPT call -> one image query (or None) per phrase, 1:1 and order-aligned."""
    n = len(phrases)
    if n == 0:
        return []
    texts = [_phrase_text(p) for p in phrases]
    phrase_lines = "\n".join(f"{i}: {t}" for i, t in enumerate(texts))
    prompt = _PROMPT.format(
        summary=(video_summary or "")[:600],
        tone=(tone or "")[:120],
        full_text=(full_text or "")[:8000],
        phrase_lines=phrase_lines,
        n=n,
    )
    # One call per video; a stronger model here is worth it - it follows the
    # coverage + on-subject rules far better than a mini model. Override with
    # BROLL_QUERY_MODEL if desired.
    model = getattr(settings, "broll_query_model", None) or getattr(settings, "llm_model", "gpt-4o")
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYS},
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        queries = data.get("queries") if isinstance(data, dict) else None
    except Exception as exc:  # noqa: BLE001 - never break the render over query planning
        logger.warning("plan_image_queries failed (%s); no dense image B-roll this run", exc)
        queries = None

    # Trust GPT: a null means "no good on-subject image for this line" -> that
    # phrase just shows the talking head. The old word-scraping fallback produced
    # off-topic junk ("world because", "how his") and is gone.
    out: list[str | None] = []
    for i in range(n):
        q = queries[i] if isinstance(queries, list) and i < len(queries) else None
        out.append(_clean(q) if isinstance(q, str) and q.strip() else None)
    hits = sum(1 for q in out if q)
    logger.info("[BROLL_PLAN] phrases=%d image_queries=%d", n, hits)
    return out


def _phrase_text(ph: dict) -> str:
    """Caption phrases carry ``words`` (list of {text,start,end}), not a ``text`` key."""
    if isinstance(ph, dict):
        if ph.get("text"):
            return str(ph["text"]).strip()
        words = ph.get("words") or []
        return " ".join(str(w.get("text") or w.get("word") or "") for w in words if isinstance(w, dict)).strip()
    return ""


def _clean(q: str) -> str | None:
    q = " ".join(q.split()).strip().strip("\"'").lower()
    for tok in (";", "&&", "|", "`", "$(", "../", "\n"):
        q = q.replace(tok, " ")
    q = " ".join(q.split())[:80]
    return q or None


def build_dense_broll(
    plan: EditPlan,
    phrases: list[dict],
    queries: list[str | None],
    style: dict | None = None,
    *,
    max_assets: int,
    keep_video: bool = False,
) -> EditPlan:
    """Rebuild the timeline: one full-screen image B-roll segment per phrase.

    Every phrase that has a query becomes an image B-roll segment; gaps become
    talking-head. The planner's own B-roll is discarded (dense mode is the source
    of truth) unless ``keep_video`` keeps its ``broll_type == "video"`` spans.
    """
    duration = plan_duration(plan)
    if duration < 2 or not phrases:
        return plan

    video_spans = (
        [
            (s.start, s.end)
            for s in plan.segments
            if s.visual == "broll" and s.broll_type == "video" and s.broll_query
        ]
        if keep_video
        else []
    )

    def in_video_span(a: float, b: float) -> bool:
        return any(not (b <= vs + 0.02 or a >= ve - 0.02) for vs, ve in video_spans)

    segs: list[EditSegment] = [
        s
        for s in plan.segments
        if keep_video and s.visual == "broll" and s.broll_type == "video" and s.broll_query
    ]

    image_count = 0
    for ph, query in zip(phrases, queries):
        if not query:
            continue
        start = round(max(0.0, float(ph.get("start") or 0.0) + 0.05), 3)
        end = round(min(duration, float(ph.get("end") or 0.0) - 0.05), 3)
        if end - start < 0.5 or in_video_span(start, end):
            continue
        if image_count >= max_assets:
            break
        segs.append(
            EditSegment(
                start=start,
                end=end,
                visual="broll",
                broll_type="image",
                broll_query=query,
                effect="slow_zoom_in",
                sfx=None,
            )
        )
        image_count += 1

    segs.sort(key=lambda s: s.start)

    # Fill uncovered time with talking-head so the plan spans [0, duration].
    filled: list[EditSegment] = []
    cursor = 0.0
    for s in segs:
        if s.start > cursor + 0.1:
            filled.append(EditSegment(start=round(cursor, 3), end=s.start, visual="talking_head"))
        filled.append(s)
        cursor = max(cursor, s.end)
    if duration > cursor + 0.1:
        filled.append(EditSegment(start=round(cursor, 3), end=round(duration, 3), visual="talking_head"))

    if not filled:
        return plan
    # Guarantee the timeline spans exactly [0, duration] despite phrase padding.
    if filled[0].start > 0:
        filled[0] = filled[0].model_copy(update={"start": 0.0})
    if filled[-1].end < duration:
        filled[-1] = filled[-1].model_copy(update={"end": round(duration, 3)})
    logger.info(
        "[BROLL_PLAN] built %d image + %d video B-roll segments over %.1fs",
        image_count,
        len(video_spans),
        duration,
    )
    return plan.model_copy(update={"segments": filled})
