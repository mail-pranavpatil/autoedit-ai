from __future__ import annotations

import logging

import httpx

from autoedit.image_ranking.types import ImageRanker, RankResult

logger = logging.getLogger("autoedit")

JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"


class JinaRankerError(RuntimeError):
    """Raised when Jina returns a response we cannot use."""


class JinaImageRanker(ImageRanker):
    name = "jina"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def rank(self, query: str, candidates: list[dict]) -> RankResult:
        # Jina 400s the whole batch if ONE image URL is unfetchable. Drop the
        # named URL and retry a few times so a couple of dead links don't cost us
        # the rerank entirely.
        candidates = list(candidates)
        data = None
        for _ in range(4):
            payload = {
                "model": self._model,
                "query": query,
                "documents": [{"image": c["url"]} for c in candidates],
                "return_documents": False,
            }
            try:
                data = self._call_jina(payload)
                break
            except httpx.HTTPStatusError as exc:
                body = exc.response.text if exc.response is not None else ""
                bad = None
                marker = "Failed to load image from "
                if exc.response is not None and exc.response.status_code == 400 and marker in body:
                    bad = body.split(marker, 1)[1].split('"', 1)[0].strip()
                if not bad:
                    raise
                before = len(candidates)
                candidates = [c for c in candidates if c["url"] != bad]
                if not candidates or len(candidates) == before or len(candidates) < 2:
                    raise
        if data is None:
            raise JinaRankerError("rerank failed after dropping unfetchable images")

        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list) or not results:
            raise JinaRankerError("missing results array")

        order = []
        for row in results:
            if not isinstance(row, dict):
                raise JinaRankerError("malformed result row")
            idx = row.get("index")
            score = row.get("relevance_score")
            if not isinstance(idx, int) or not 0 <= idx < len(candidates):
                raise JinaRankerError("result index out of range")
            if not isinstance(score, (int, float)):
                raise JinaRankerError("missing relevance_score")
            order.append((idx, float(score)))

        order.sort(key=lambda pair: pair[1], reverse=True)

        ranked: list[dict] = []
        scores: list[float] = []
        debug: list[dict] = []
        for original_index, score in order:
            cand = candidates[original_index]
            meta = dict(cand.get("metadata") or {})
            meta["jina_score"] = score
            ranked.append({**cand, "metadata": meta})
            scores.append(score)
            debug.append(
                {
                    "imageId": cand.get("external_id"),
                    "jinaScore": score,
                    "originalIndex": original_index,
                    "source": (cand.get("metadata") or {}).get("photographer"),
                }
            )

        return RankResult(
            ranked=ranked,
            scores=scores,
            provider="jina",
            used_fallback=False,
            reason=None,
            debug=debug,
        )

    def _call_jina(self, payload: dict) -> dict:
        """Single POST to Jina. Isolated so tests can monkeypatch it.

        Never logs the API key or the Authorization header.
        """
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                JINA_RERANK_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
