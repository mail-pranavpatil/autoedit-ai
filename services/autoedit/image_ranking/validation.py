from __future__ import annotations

from urllib.parse import urlparse

_ALLOWED_SCHEMES = {"http", "https"}


def _usable_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return False
    return parsed.scheme in _ALLOWED_SCHEMES and bool(parsed.netloc)


def prepare_candidates(
    candidates: list[dict],
    max_candidates: int,
) -> tuple[list[dict], list[dict]]:
    """Split raw search candidates into ``(kept, leftovers)`` for reranking.

    ``kept`` is what we send to Jina: image candidates with a usable http(s)
    URL, de-duplicated by exact URL (first occurrence wins), original order
    preserved, truncated to ``max_candidates``.

    ``leftovers`` is everything else — rejected candidates plus the overflow
    past ``max_candidates`` — kept so the caller can append them and never drop
    a candidate the existing pipeline would have considered.
    """
    kept: list[dict] = []
    leftovers: list[dict] = []
    seen: set[str] = set()

    for cand in candidates:
        url = cand.get("url") if isinstance(cand, dict) else None
        if cand.get("asset_type") != "image" or not _usable_url(url):
            leftovers.append(cand)
            continue
        url = url.strip()
        if url in seen:
            leftovers.append(cand)
            continue
        seen.add(url)
        if len(kept) < max(max_candidates, 0):
            kept.append(cand)
        else:
            leftovers.append(cand)

    return kept, leftovers
