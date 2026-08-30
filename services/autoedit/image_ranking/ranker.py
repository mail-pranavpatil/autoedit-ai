from __future__ import annotations

import hashlib
import logging

from autoedit.config import get_settings
from autoedit.image_ranking.jina import JinaImageRanker
from autoedit.image_ranking.types import ImageRanker, RankResult
from autoedit.image_ranking.validation import prepare_candidates

logger = logging.getLogger("autoedit")

# Process-level cache of ranked candidate lists. A worker handles one video per
# task, so this mostly de-dupes repeated (query, candidate-set) pairs within a
# single render. Keyed by model + query + sorted URLs, value is the ranked list.
_CACHE: dict[str, list[dict]] = {}


def get_image_ranker(settings=None) -> ImageRanker | None:
    settings = settings or get_settings()
    if not settings.jina_api_key:
        return None
    return JinaImageRanker(
        api_key=settings.jina_api_key,
        model=settings.jina_model,
        timeout=settings.jina_timeout_seconds,
    )


def _cache_key(model: str, query: str, urls: list[str]) -> str:
    blob = "\n".join([model, query.strip().lower(), *sorted(urls)])
    return "jina:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def rank_candidates_detailed(
    query: str,
    candidates: list[dict],
    *,
    asset_type: str,
    scene_id,
    settings=None,
) -> RankResult:
    """Rank ``candidates`` for ``query``; never raises.

    Returns a :class:`RankResult`. On any problem (feature off, no key, too few
    candidates, HTTP/timeout/parse failure, unexpected exception) it returns the
    original list untouched with ``used_fallback=True`` so the caller's existing
    selection logic runs exactly as before.
    """
    settings = settings or get_settings()

    if not settings.enable_jina_reranker:
        return RankResult(ranked=candidates, used_fallback=True, reason="disabled")

    if asset_type != "image" or len(candidates) < 2:
        return RankResult(ranked=candidates, used_fallback=True, reason="not_applicable")

    try:
        ranker = get_image_ranker(settings)
        if ranker is None:
            return _fallback(candidates, scene_id, "no_api_key")

        kept, leftovers = prepare_candidates(candidates, settings.jina_max_candidates)
        if len(kept) < 2:
            return _fallback(candidates, scene_id, "too_few_candidates")

        key = _cache_key(settings.jina_model, query, [c["url"] for c in kept])
        cached = _CACHE.get(key)
        if cached is not None:
            ordered = cached
            result = RankResult(ranked=ordered, provider=ranker.name, reason="cache_hit")
        else:
            result = ranker.rank(query, kept)
            ordered = result.ranked
            _CACHE[key] = ordered

        top_score = 0.0
        if ordered:
            top_score = float((ordered[0].get("metadata") or {}).get("jina_score") or 0.0)
        logger.info(
            "[JINA_RERANKER] scene=%s candidates=%d kept=%d status=success top_score=%.3f",
            scene_id,
            len(candidates),
            len(kept),
            top_score,
        )

        merged = list(ordered) + list(leftovers)
        return RankResult(
            ranked=merged,
            scores=result.scores,
            provider=ranker.name,
            used_fallback=False,
            reason=result.reason,
            debug=result.debug,
        )
    except Exception as exc:  # noqa: BLE001 - reranker must never break rendering
        return _fallback(candidates, scene_id, type(exc).__name__)


def rank_candidates(
    query: str,
    candidates: list[dict],
    *,
    asset_type: str,
    scene_id,
    settings=None,
) -> list[dict]:
    """Thin wrapper used by the pipeline: returns just the (re)ordered list."""
    return rank_candidates_detailed(
        query,
        candidates,
        asset_type=asset_type,
        scene_id=scene_id,
        settings=settings,
    ).ranked


def _fallback(candidates: list[dict], scene_id, reason: str) -> RankResult:
    logger.warning("[JINA_RERANKER] scene=%s status=fallback reason=%s", scene_id, reason)
    return RankResult(ranked=candidates, used_fallback=True, reason=reason)
