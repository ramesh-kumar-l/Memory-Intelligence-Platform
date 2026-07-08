"""Response models mirroring `MemoryObject.to_public_dict()` (backend/mip/core).

Field names and enum values mirror `30-memory/02-memory-schema.md` exactly, per
`21-coding-standards.md` ("names mirror spec vocabulary, never invent
synonyms"). `extra="ignore"` because minor API versions only add fields
(05-api-design.md versioning policy) — the SDK must tolerate unknown fields.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TOLERANT = ConfigDict(extra="ignore")


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


class MemoryState(StrEnum):
    CREATED = "Created"
    VALIDATING = "Validating"
    VALIDATION_FAILED = "ValidationFailed"
    VALIDATED = "Validated"
    ENRICHING = "Enriching"
    INDEXED = "Indexed"
    GRAPH_LINKED = "GraphLinked"
    ACTIVE = "Active"
    UPDATING = "Updating"
    ARCHIVED = "Archived"
    DELETED = "Deleted"


class Header(BaseModel):
    model_config = TOLERANT

    schema_version: str
    object_type: ObjectType
    encoding_version: str
    checksum: str | None = None


class Identity(BaseModel):
    model_config = TOLERANT

    memory_id: UUID
    namespace: str
    owner_id: str
    tenant_id: str | None = None
    parent_id: UUID | None = None
    root_episode_id: UUID | None = None


class Content(BaseModel):
    model_config = TOLERANT

    title: str
    summary: str = ""
    description: str = ""
    language: str = "en"
    attachments: tuple[str, ...] = ()
    media_refs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


class Semantics(BaseModel):
    model_config = TOLERANT

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


class Relationship(BaseModel):
    model_config = TOLERANT

    relationship_id: UUID
    target_memory_id: UUID
    type: RelationshipType
    direction: RelationshipDirection = RelationshipDirection.OUTBOUND
    confidence: float = 1.0
    created_at: datetime
    unresolved: bool = False


class Context(BaseModel):
    model_config = TOLERANT

    importance_score: float = 0.5
    recency_score: float = 1.0
    access_frequency: int = 0
    last_accessed: datetime | None = None
    relevance_tags: tuple[str, ...] = ()
    goals: tuple[str, ...] = ()


class Provenance(BaseModel):
    model_config = TOLERANT

    source: str
    method: str | None = None
    location: str | None = None
    captured_at: datetime | None = None
    agent: str | None = None


class Trust(BaseModel):
    model_config = TOLERANT

    confidence: float
    freshness: float = 1.0
    provenance: Provenance
    evidence: tuple[dict[str, Any], ...] = ()
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    source_count: int = 1
    explanation: str = ""


class Lifecycle(BaseModel):
    model_config = TOLERANT

    version: int
    state: MemoryState
    created_at: datetime
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    consolidation_count: int = 0


class AuditMetadata(BaseModel):
    model_config = TOLERANT

    created_by: str
    updated_by: str | None = None
    update_reason: str | None = None
    change_set: str | None = None
    trace_id: str | None = None
    request_id: str | None = None


class MemoryObject(BaseModel):
    """Client-side view of a Memory Object — as returned by the public API
    (Section 9 Storage Metadata is never sent over the wire, so it has no
    field here).
    """

    model_config = TOLERANT

    memory_id: str
    header: Header
    identity: Identity
    content: Content
    semantics: Semantics = Field(default_factory=Semantics)
    relationships: tuple[Relationship, ...] = ()
    context: Context = Field(default_factory=Context)
    trust: Trust
    lifecycle: Lifecycle
    extensions: dict[str, Any] = Field(default_factory=dict)
    audit: AuditMetadata


class MemoryRecord(BaseModel):
    """Lifecycle-summary projection row returned by `GET /v1/memories` (list) —
    deliberately lighter than `MemoryObject`; fetch a memory_id individually
    via `.get()` for the full object (mirrors `storage/interfaces.py`).
    """

    model_config = TOLERANT

    memory_id: str
    namespace: str
    owner_id: str
    object_type: str
    title: str
    state: MemoryState
    current_version: int
    created_at: datetime
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    consolidation_count: int = 0


class VersionInfo(BaseModel):
    """Immutable version-history entry returned by `.../versions` (list)."""

    model_config = TOLERANT

    version: int
    previous_version: int | None = None
    created_at: datetime
