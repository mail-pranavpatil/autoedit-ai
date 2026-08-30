from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RankResult:
    """Outcome of a ranking attempt.

    ``ranked`` holds the candidate dicts (same shape they came in with, e.g. the
    ``PexelsSearch`` output) reordered by descending relevance. Every dict keeps
    all of its original metadata; a ``jina_score`` key is added under
    ``metadata`` when the ranker actually ran.
    """

    ranked: list[dict]
    scores: list[float] = field(default_factory=list)
    provider: str = "jina"
    used_fallback: bool = False
    reason: str | None = None
    debug: list[dict] = field(default_factory=list)


class ImageRanker(ABC):
    """Provider interface: reorder image candidates by visual relevance to a query.

    Implementations must be side-effect-free with respect to the input list and
    return a :class:`RankResult`. Raising is allowed; the orchestrator in
    ``ranker.py`` treats any exception as a signal to fall back.
    """

    name: str = "ranker"

    @abstractmethod
    def rank(self, query: str, candidates: list[dict]) -> RankResult:
        raise NotImplementedError
