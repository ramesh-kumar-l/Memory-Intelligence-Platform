"""The 11 canonical Memory Object sections (30-memory/02-memory-schema.md).

All models are frozen — immutability by construction; updates build new
instances/versions. Unknown input fields are ignored (FR-SCHEMA-003 tolerance);
explicit extensions live in MemoryObject.extensions.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

FROZEN = ConfigDict(frozen=True, extra="ignore")


class ObjectType(StrEnum):
    EXPERIENCE = "Experience"
    EPISODE = "Episode"
    SEMANTIC = "Semantic"
    RELATIONSHIP = "Relationship"
    CONTEXT = "Context"
    WORKING = "Working"
    LEARNED = "Learned"
    SYSTEM = "System"


class VerificationStatus(StrEnum):
    UNKNOWN = "Unknown"
    UNVERIFIED = "Unverified"
    PARTIALLY_VERIFIED = "PartiallyVerified"
    VERIFIED = "Verified"
    DISPUTED = "Disputed"


class RelationshipType(StrEnum):
    CONTAINS = "contains"
    REFERENCES = "references"
    DUPLICATE_OF = "duplicate_of"
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"
    OCCURRED_BEFORE = "occurred_before"
    OCCURRED_AFTER = "occurred_after"
    CAUSED_BY = "caused_by"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"


class RelationshipDirection(StrEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
    BIDIRECTIONAL = "bidirectional"


class Header(BaseModel):
    """Section 1 — serialization and compatibility metadata."""

    model_config = FROZEN

    schema_version: str = Field(min_length=1)
    object_type: ObjectType
    encoding_version: str = Field(min_length=1)
    checksum: str | None = None


class Identity(BaseModel):
    """Section 2 — immutable identity (INV-ID-001/002)."""

    model_config = FROZEN

    memory_id: UUID
    namespace: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    tenant_id: str | None = None
    parent_id: UUID | None = None
    root_episode_id: UUID | None = None


class Content(BaseModel):
    """Section 3 — human-readable knowledge. Title is required and non-empty."""

    model_config = FROZEN

    title: str = Field(min_length=1)
    summary: str = ""
    description: str = ""
    language: str = "en"
    attachments: tuple[str, ...] = ()
    media_refs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


class Semantics(BaseModel):
    """Section 4 — machine-readable understanding."""

    model_config = FROZEN

    entities: tuple[str, ...] = ()
    concepts: tuple[str, ...] = ()
    activities: tuple[str, ...] = ()
    events: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    timestamps: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    sentiment: dict[str, Any] | None = None
    intent: dict[str, Any] | None = None

    @property
    def has_semantic_element(self) -> bool:
        """INV-SEM-001: at least one semantic element must be present."""
        return any(
            (
                self.entities,
                self.concepts,
                self.activities,
                self.events,
                self.locations,
                self.topics,
                self.timestamps,
                self.keywords,
            )
        )


class Relationship(BaseModel):
    """Section 5 — typed link to another memory (INV-REL-001/002)."""

    model_config = FROZEN

    relationship_id: UUID
    target_memory_id: UUID
    type: RelationshipType
    direction: RelationshipDirection = RelationshipDirection.OUTBOUND
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime
    unresolved: bool = False


class Context(BaseModel):
    """Section 6 — retrieval context. Mutable by design (not part of version identity)."""

    model_config = FROZEN

    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    recency_score: float = Field(default=1.0, ge=0.0, le=1.0)
    access_frequency: int = Field(default=0, ge=0)
    last_accessed: datetime | None = None
    relevance_tags: tuple[str, ...] = ()
    goals: tuple[str, ...] = ()


class Provenance(BaseModel):
    """Where the memory came from — required for activation (INV-TRUST-001)."""

    model_config = FROZEN

    source: str = Field(min_length=1)
    method: str | None = None
    location: str | None = None
    captured_at: datetime | None = None
    agent: str | None = None


class Trust(BaseModel):
    """Section 7 — confidence and explainability. Scores are derived; evidence is truth."""

    model_config = FROZEN

    confidence: float = Field(ge=0.0, le=1.0)
    freshness: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: Provenance
    evidence: tuple[dict[str, Any], ...] = ()
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    source_count: int = Field(default=1, ge=0)
    explanation: str = ""


class StorageMetadata(BaseModel):
    """Section 9 — persistence hints. Never exposed through the public API."""

    model_config = FROZEN

    storage_engine: str = "sqlite"
    partition: str | None = None
    shard: str | None = None
    vector_id: str | None = None
    graph_node_id: str | None = None
    blob_refs: tuple[str, ...] = ()


class AuditMetadata(BaseModel):
    """Section 11 — replayability and debugging. Append-only history."""

    model_config = FROZEN

    created_by: str = Field(min_length=1)
    updated_by: str | None = None
    update_reason: str | None = None
    change_set: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
