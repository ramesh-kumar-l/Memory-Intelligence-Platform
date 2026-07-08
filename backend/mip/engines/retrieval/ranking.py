"""Ranking math for keyword/semantic/hybrid search (ADR-0004). Every formula
here is small and explicit so a ranking explanation is always reconstructable.
"""

from __future__ import annotations

from mip.storage.interfaces import SearchHit


def normalize_keyword_scores(hits: list[SearchHit]) -> dict[str, float]:
    """Min-max normalize raw (higher-is-better) keyword scores to [0, 1]."""
    if not hits:
        return {}
    values = [hit.score for hit in hits]
    low, high = min(values), max(values)
    if high == low:
        return {hit.memory_id: 1.0 for hit in hits}
    return {hit.memory_id: (hit.score - low) / (high - low) for hit in hits}


def semantic_similarity(distance: float) -> float:
    """Convert L2 distance (0 = identical, unbounded above) to a (0, 1] similarity."""
    return 1.0 / (1.0 + max(0.0, distance))


def combine_hybrid(keyword_score: float, semantic_score: float, keyword_weight: float) -> float:
    """Weighted linear fusion of the two normalized scores (both already in [0, 1])."""
    return keyword_weight * keyword_score + (1.0 - keyword_weight) * semantic_score
