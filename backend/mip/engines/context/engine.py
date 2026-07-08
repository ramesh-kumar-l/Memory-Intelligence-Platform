"""Context Engine: BuildContext (Phase 2 task 5). Assembles a task-specific
Context Package by re-weighting Retrieval Engine results with each memory's
own Context section (importance/recency) — still fully explainable per item.
"""

from __future__ import annotations

from typing import Any

from mip.core.model import MemoryObject
from mip.engines.retrieval.engine import RetrievalEngine
from mip.storage.interfaces import MemoryRepositoryABC

#: Weight given to relevance-to-query vs. the memory's own importance score.
_RELEVANCE_WEIGHT = 0.7
_IMPORTANCE_WEIGHT = 0.3


class ContextEngine:
    def __init__(self, *, retrieval: RetrievalEngine, repository: MemoryRepositoryABC) -> None:
        self._retrieval = retrieval
        self._repository = repository

    def build_context(
        self, query: str, *, namespace: str | None, mode: str, limit: int, offset: int
    ) -> dict[str, Any]:
        ranked, has_more = self._retrieval.search(
            query, mode=mode, namespace=namespace, limit=limit, offset=offset
        )
        items: list[dict[str, Any]] = []
        for result in ranked:
            memory = self._repository.get_object(result.memory_id)
            if memory is None:  # pragma: no cover - defensive, index/repo are kept in sync
                continue
            items.append(_context_item(memory, result.score))
        items.sort(key=lambda item: (-item["blended_score"], item["memory"]["memory_id"]))
        return {
            "query": query,
            "namespace": namespace,
            "mode": mode,
            "items": items,
            "complete": not has_more,
            "total_candidates": len(items),
        }


def _context_item(memory: MemoryObject, relevance_score: float) -> dict[str, Any]:
    importance = memory.context.importance_score
    blended = _RELEVANCE_WEIGHT * relevance_score + _IMPORTANCE_WEIGHT * importance
    return {
        "memory": memory.to_public_dict(),
        "relevance_score": relevance_score,
        "importance_score": importance,
        "blended_score": round(blended, 4),
    }
