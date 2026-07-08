"""Internal ranked-result shape passed from the Retrieval Engine to the API layer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RankedResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    memory_id: str
    score: float
    keyword_score: float | None = None
    semantic_score: float | None = None
