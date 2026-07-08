"""Request DTOs for Search / Explain / BuildContext (Phase 2, FR-API-001)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

STRICT = ConfigDict(extra="forbid")


class SearchRequest(BaseModel):
    model_config = STRICT

    query: str | None = Field(default=None, min_length=1)
    mode: str = "hybrid"
    namespace: str | None = None
    limit: int | None = None
    continuation_token: str | None = None


class ExplainRequest(BaseModel):
    model_config = STRICT

    memory_id: str
    query: str | None = None
    mode: str = "hybrid"


class ContextRequest(BaseModel):
    model_config = STRICT

    query: str | None = Field(default=None, min_length=1)
    namespace: str | None = None
    mode: str = "hybrid"
    limit: int | None = None
    continuation_token: str | None = None
