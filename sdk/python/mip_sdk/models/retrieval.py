"""Response models for Search / Explain / BuildContext (Phase 2 contract,
mirrored from `mip/api/v1/search.py`, `explain.py`, `context.py`, and
`mip/engines/retrieval/explain.py`).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from mip_sdk.models.memory import MemoryObject

TOLERANT = ConfigDict(extra="ignore")


class Page[T](BaseModel):
    """A single page of a continuation-token-paginated list (05-api-design.md
    — offset pagination is prohibited by the contract; only this pattern).
    """

    model_config = TOLERANT

    items: tuple[T, ...]
    complete: bool
    continuation_token: str | None = None


class SearchItemExplanation(BaseModel):
    model_config = TOLERANT

    mode: str
    keyword_score: float | None = None
    semantic_score: float | None = None


class SearchItem(BaseModel):
    model_config = TOLERANT

    memory_id: str
    score: float
    explanation: SearchItemExplanation


class SearchResponse(BaseModel):
    model_config = TOLERANT

    query: str
    mode: str
    items: tuple[SearchItem, ...]
    complete: bool
    continuation_token: str | None = None


class RankingExplanation(BaseModel):
    model_config = TOLERANT

    mode: str
    score: float
    keyword_score: float | None = None
    semantic_score: float | None = None
    matched: bool


class Explanation(BaseModel):
    """Direct mirror of `POST /v1/explain`'s response body — the payload the
    console's ExplainPanel renders (18-ui-design-system.md).
    """

    model_config = TOLERANT

    memory_id: str
    confidence: float
    freshness: float
    verification_status: str
    source_count: int
    provenance: dict[str, Any]
    evidence: tuple[dict[str, Any], ...]
    ranking: RankingExplanation | None = None


class ContextItem(BaseModel):
    model_config = TOLERANT

    memory: MemoryObject
    relevance_score: float
    importance_score: float
    blended_score: float


class ContextPackage(BaseModel):
    model_config = TOLERANT

    query: str
    namespace: str | None = None
    mode: str
    items: tuple[ContextItem, ...]
    complete: bool
    total_candidates: int
    continuation_token: str | None = None
