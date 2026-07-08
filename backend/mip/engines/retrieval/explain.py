"""Explain: build the explainability payload for one memory (Phase 2 task 4,
FR-API-007). Evidence/confidence/freshness/provenance are always available;
a ranking explanation is added only when the caller supplies a query.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mip.core.model import MemoryObject
from mip.engines.retrieval.engine import RetrievalEngine
from mip.engines.trust.scoring import TrustEngine

#: How many top candidates we scan to find this memory's own score for a given
#: query — a pragmatic bound, not the same as the full search fetch window.
_EXPLAIN_CANDIDATE_SCAN = 200


def build_explanation(
    memory: MemoryObject,
    *,
    trust: TrustEngine,
    retrieval: RetrievalEngine,
    query: str | None,
    mode: str,
    now: datetime,
) -> dict[str, Any]:
    freshness = trust.dynamic_freshness(
        created_at=memory.lifecycle.created_at, updated_at=memory.lifecycle.updated_at, now=now
    )
    payload: dict[str, Any] = {
        "memory_id": memory.memory_id,
        "confidence": memory.trust.confidence,
        "freshness": freshness,
        "verification_status": memory.trust.verification_status.value,
        "source_count": memory.trust.source_count,
        "provenance": memory.trust.provenance.model_dump(mode="json"),
        "evidence": list(memory.trust.evidence),
        "ranking": None,
    }
    if query:
        payload["ranking"] = _ranking_explanation(
            memory, retrieval=retrieval, query=query, mode=mode
        )
    return payload


def _ranking_explanation(
    memory: MemoryObject, *, retrieval: RetrievalEngine, query: str, mode: str
) -> dict[str, Any]:
    results, _ = retrieval.search(
        query,
        mode=mode,
        namespace=memory.identity.namespace,
        limit=_EXPLAIN_CANDIDATE_SCAN,
        offset=0,
    )
    for result in results:
        if result.memory_id == memory.memory_id:
            return {
                "mode": mode,
                "score": result.score,
                "keyword_score": result.keyword_score,
                "semantic_score": result.semantic_score,
                "matched": True,
            }
    return {
        "mode": mode,
        "score": 0.0,
        "keyword_score": None,
        "semantic_score": None,
        "matched": False,
    }
