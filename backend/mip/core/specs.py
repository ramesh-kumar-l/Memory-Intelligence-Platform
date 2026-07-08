"""Typed inputs for domain operations (transport-independent).

API DTOs convert to these specs; engines consume only specs, keeping the
contract semantics independent of HTTP (FR-API-001).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from mip.core.sections import (
    Context,
    ObjectType,
    Provenance,
    RelationshipDirection,
    RelationshipType,
    Semantics,
    VerificationStatus,
)

FROZEN = ConfigDict(frozen=True, extra="forbid")


class RelationshipSpec(BaseModel):
    model_config = FROZEN

    target_memory_id: UUID
    type: RelationshipType
    direction: RelationshipDirection = RelationshipDirection.OUTBOUND
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    unresolved: bool = False


class CreateMemorySpec(BaseModel):
    """Everything needed to build version 1 of a Memory Object."""

    model_config = FROZEN

    namespace: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    object_type: ObjectType = ObjectType.EXPERIENCE
    title: str = Field(min_length=1)
    summary: str = ""
    description: str = ""
    language: str = "en"
    semantics: Semantics = Field(default_factory=Semantics)
    relationships: tuple[RelationshipSpec, ...] = ()
    context: Context = Field(default_factory=Context)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: Provenance
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    evidence: tuple[dict[str, Any], ...] = ()
    extensions: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class UpdateMemorySpec(BaseModel):
    """Partial changes producing version N+1. Absent fields keep prior values."""

    model_config = FROZEN

    title: str | None = None
    summary: str | None = None
    description: str | None = None
    language: str | None = None
    semantics: Semantics | None = None
    relationships: tuple[RelationshipSpec, ...] | None = None
    context: Context | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    freshness: float | None = Field(default=None, ge=0.0, le=1.0)
    verification_status: VerificationStatus | None = None
    evidence: tuple[dict[str, Any], ...] | None = None
    source_count: int | None = Field(default=None, ge=0)
    extensions: dict[str, Any] | None = None
    update_reason: str | None = None
    updated_by: str | None = None
