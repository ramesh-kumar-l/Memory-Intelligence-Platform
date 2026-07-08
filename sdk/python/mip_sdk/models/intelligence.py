"""Response models for Phase 4 — graph relationships, Export/Import
(ADR-0006), mirrored from `backend/mip/storage/interfaces.py` and the Phase 4
API routes.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

TOLERANT = ConfigDict(extra="ignore")


class GraphEdge(BaseModel):
    model_config = TOLERANT

    relationship_id: str
    source_memory_id: str
    target_memory_id: str
    type: str
    direction: str
    confidence: float


class RelationshipsView(BaseModel):
    """`GET /v1/memories/{id}/relationships` response — every edge touching
    one memory, outbound and inbound.
    """

    model_config = TOLERANT

    memory_id: str
    relationships: tuple[GraphEdge, ...]


class ImportSkip(BaseModel):
    model_config = TOLERANT

    memory_id: str
    reason: str


class ImportRejection(BaseModel):
    model_config = TOLERANT

    memory_id: str | None
    violations: tuple[dict[str, Any], ...]


class ImportReport(BaseModel):
    model_config = TOLERANT

    imported: tuple[str, ...]
    skipped: tuple[ImportSkip, ...]
    rejected: tuple[ImportRejection, ...]


class ExportBundle(BaseModel):
    """The full Export payload — pass straight to `client.portability.import_()`."""

    model_config = TOLERANT

    schema_version: str
    exported_at: str
    namespace: str | None = None
    memory_count: int
    memories: tuple[dict[str, Any], ...]
