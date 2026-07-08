"""Request models mirroring `backend/mip/api/v1/schemas.py` and
`retrieval_schemas.py`. `extra="forbid"` — same strictness as the server so
a caller finds out about a typo locally instead of via a 422.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from mip_sdk.models.memory import (
    Context,
    ObjectType,
    RelationshipDirection,
    RelationshipType,
    Semantics,
    VerificationStatus,
)

STRICT = ConfigDict(extra="forbid")


class ProvenanceInput(BaseModel):
    model_config = STRICT

    source: str = Field(min_length=1)
    method: str | None = None
    location: str | None = None
    captured_at: str | None = None
    agent: str | None = None


class RelationshipInput(BaseModel):
    model_config = STRICT

    target_memory_id: UUID
    type: RelationshipType
    direction: RelationshipDirection = RelationshipDirection.OUTBOUND
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    unresolved: bool = False


class CreateMemoryRequest(BaseModel):
    model_config = STRICT

    namespace: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    object_type: ObjectType = ObjectType.EXPERIENCE
    title: str = Field(min_length=1)
    summary: str = ""
    description: str = ""
    language: str = "en"
    semantics: Semantics = Field(default_factory=Semantics)
    relationships: tuple[RelationshipInput, ...] = ()
    context: Context = Field(default_factory=Context)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: ProvenanceInput
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    evidence: tuple[dict[str, Any], ...] = ()
    extensions: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class UpdateMemoryRequest(BaseModel):
    model_config = STRICT

    title: str | None = None
    summary: str | None = None
    description: str | None = None
    language: str | None = None
    semantics: Semantics | None = None
    relationships: tuple[RelationshipInput, ...] | None = None
    context: Context | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    freshness: float | None = Field(default=None, ge=0.0, le=1.0)
    verification_status: VerificationStatus | None = None
    evidence: tuple[dict[str, Any], ...] | None = None
    source_count: int | None = Field(default=None, ge=0)
    extensions: dict[str, Any] | None = None
    update_reason: str | None = None
    updated_by: str | None = None


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


class ConsolidateRequest(BaseModel):
    """Phase 4 task 2 (ADR-0006): merge duplicates via relationships."""

    model_config = STRICT

    primary_memory_id: str
    duplicate_memory_ids: tuple[str, ...]


class LearnRequest(BaseModel):
    """Phase 4 task 3 (ADR-0006): derived semantics + trust maturation."""

    model_config = STRICT

    memory_id: str
    derived: Semantics | None = None
    new_evidence: tuple[dict[str, Any], ...] = ()
    verifier: str | None = None
    reason: str = Field(min_length=1)
    actor: str | None = None


class ExportRequest(BaseModel):
    model_config = STRICT

    namespace: str | None = None
