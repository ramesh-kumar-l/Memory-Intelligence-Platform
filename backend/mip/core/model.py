"""The canonical MemoryObject — 11 logical sections, frozen (immutable).

Memory Objects are the source of truth; everything else is a regenerable
projection. Section 8 (Lifecycle) lives here; Section 10 is `extensions`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mip.core.sections import (
    AuditMetadata,
    Content,
    Context,
    Header,
    Identity,
    Relationship,
    Semantics,
    StorageMetadata,
    Trust,
)
from mip.core.states import MemoryState


class Lifecycle(BaseModel):
    """Section 8 — version and state tracking (INV-VER-001, INV-STATE-001)."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    version: int = Field(ge=1)
    state: MemoryState
    created_at: datetime
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    consolidation_count: int = Field(default=0, ge=0)


class MemoryObject(BaseModel):
    """Canonical Memory Object per 30-memory/02-memory-schema.md (FR-SCHEMA-001)."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    header: Header
    identity: Identity
    content: Content
    semantics: Semantics = Field(default_factory=Semantics)
    relationships: tuple[Relationship, ...] = ()
    context: Context = Field(default_factory=Context)
    trust: Trust
    lifecycle: Lifecycle
    storage: StorageMetadata = Field(default_factory=StorageMetadata)
    extensions: dict[str, Any] = Field(default_factory=dict)
    audit: AuditMetadata

    @property
    def memory_id(self) -> str:
        return str(self.identity.memory_id)

    @property
    def state(self) -> MemoryState:
        return self.lifecycle.state

    @property
    def version(self) -> int:
        return self.lifecycle.version

    def with_lifecycle(self, **changes: Any) -> MemoryObject:
        """Return a copy with lifecycle fields replaced (immutability-preserving)."""
        return self.model_copy(update={"lifecycle": self.lifecycle.model_copy(update=changes)})

    def to_public_dict(self) -> dict[str, Any]:
        """API representation. Storage Metadata (Section 9) is never exposed."""
        data = self.model_dump(mode="json", exclude={"storage"})
        data["memory_id"] = self.memory_id
        return data

    def to_storage_json(self) -> str:
        """Full lossless serialization for version snapshots (FR-SCHEMA-005)."""
        return self.model_dump_json()

    @classmethod
    def from_storage_json(cls, raw: str) -> MemoryObject:
        return cls.model_validate_json(raw)
