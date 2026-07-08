"""Request DTOs for Consolidate / Learn / Export / Import (Phase 4, FR-API-001)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mip.core.sections import Semantics

STRICT = ConfigDict(extra="forbid")


class ConsolidateRequest(BaseModel):
    model_config = STRICT

    primary_memory_id: str = Field(min_length=1)
    duplicate_memory_ids: tuple[str, ...] = Field(min_length=1)


class LearnRequest(BaseModel):
    model_config = STRICT

    memory_id: str = Field(min_length=1)
    derived: Semantics | None = None
    new_evidence: tuple[dict[str, Any], ...] = ()
    verifier: str | None = None
    reason: str = Field(min_length=1)
    actor: str | None = None


class ExportRequest(BaseModel):
    model_config = STRICT

    namespace: str | None = None


class ImportRequest(BaseModel):
    """Accepts an Export bundle verbatim; only `memories` drives the pipeline —
    `schema_version`/`exported_at`/`namespace`/`memory_count` are informational.
    """

    model_config = ConfigDict(extra="ignore")

    memories: list[dict[str, Any]] = Field(default_factory=list)
