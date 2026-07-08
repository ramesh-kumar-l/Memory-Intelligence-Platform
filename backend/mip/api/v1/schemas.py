"""Request DTOs for /v1. DTOs convert to transport-independent core specs so
HTTP never leaks into engines (FR-API-001). Unknown request fields are
rejected explicitly rather than silently dropped.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mip.core.sections import (
    Context,
    ObjectType,
    Provenance,
    Semantics,
    VerificationStatus,
)
from mip.core.specs import CreateMemorySpec, RelationshipSpec, UpdateMemorySpec

STRICT = ConfigDict(extra="forbid")


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
    relationships: tuple[RelationshipSpec, ...] = ()
    context: Context = Field(default_factory=Context)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: Provenance
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    evidence: tuple[dict[str, Any], ...] = ()
    extensions: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    def to_spec(self) -> CreateMemorySpec:
        return CreateMemorySpec.model_validate(self.model_dump())


class UpdateMemoryRequest(BaseModel):
    model_config = STRICT

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

    def to_spec(self) -> UpdateMemorySpec:
        return UpdateMemorySpec.model_validate(self.model_dump())
