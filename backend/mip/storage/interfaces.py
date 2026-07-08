"""Storage ports — engines depend only on these ABCs, never on concrete adapters.

Storage independence rule (03-system-architecture.md): no code outside
mip/storage/ may import sqlite3 or reference SQL.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from mip.core.model import MemoryObject
from mip.core.states import MemoryState
from mip.events.types import MemoryEvent


class MemoryRecord(BaseModel):
    """Projection row: current lifecycle summary of one memory."""

    model_config = ConfigDict(frozen=True)

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


class VersionInfo(BaseModel):
    """Immutable version-history entry (INV-VER-004: predecessor link)."""

    model_config = ConfigDict(frozen=True)

    version: int
    previous_version: int | None
    created_at: datetime


class IdempotencyRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_hash: str
    status_code: int
    response_json: str


class SearchHit(BaseModel):
    """One keyword-index match; higher score is better (ADR-0004)."""

    model_config = ConfigDict(frozen=True)

    memory_id: str
    score: float


class VectorHit(BaseModel):
    """One vector-index match; distance is raw L2 distance, lower is closer."""

    model_config = ConfigDict(frozen=True)

    memory_id: str
    distance: float


class TransactionManagerABC(ABC):
    """Atomic write scope shared by event appends and projection updates (INV-CONCUR-003)."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager[None]:
        """Open (or join) an atomic transaction; rollback on any exception."""

    @abstractmethod
    def ping(self) -> bool:
        """Liveness check for /v1/health."""


class EventStoreABC(ABC):
    """Append-only event log. Events are never updated or deleted."""

    @abstractmethod
    def append(self, event: MemoryEvent) -> MemoryEvent:
        """Persist the event and return it with its assigned monotonic sequence."""

    @abstractmethod
    def events_for(self, memory_id: str) -> list[MemoryEvent]: ...

    @abstractmethod
    def all_events(self) -> list[MemoryEvent]:
        """Every event in global sequence order (replay input)."""

    @abstractmethod
    def count(self) -> int: ...


class MemoryRepositoryABC(ABC):
    """Projection of the event log: current records + immutable version snapshots."""

    @abstractmethod
    def create(self, memory: MemoryObject) -> None:
        """Insert record + version 1 snapshot; raise MEM-3003 on duplicate id."""

    @abstractmethod
    def get_record(self, memory_id: str) -> MemoryRecord | None: ...

    @abstractmethod
    def get_object(self, memory_id: str, version: int | None = None) -> MemoryObject | None:
        """Version snapshot; current version gets the live lifecycle overlaid."""

    @abstractmethod
    def publish_version(
        self, memory: MemoryObject, previous_version: int, published_at: datetime
    ) -> None:
        """Insert version N+1 snapshot and make it current (never overwrites)."""

    @abstractmethod
    def set_state(self, memory_id: str, state: MemoryState, changed_at: datetime) -> None: ...

    @abstractmethod
    def list_records(
        self,
        *,
        namespace: str | None,
        state: MemoryState | None,
        limit: int,
        after_memory_id: str | None,
    ) -> tuple[list[MemoryRecord], bool]:
        """Filtered page ordered by memory_id; second element = more pages exist."""

    @abstractmethod
    def list_versions(self, memory_id: str) -> list[VersionInfo]: ...

    @abstractmethod
    def clear_all(self) -> None:
        """Wipe projections (rebuild only — events are untouched)."""

    @abstractmethod
    def dump_state(self) -> dict[str, Any]:
        """Deterministic full dump for replay-identity verification (INV-CONS-004)."""


class IdempotencyStoreABC(ABC):
    @abstractmethod
    def lookup(self, key: str, endpoint: str) -> IdempotencyRecord | None: ...

    @abstractmethod
    def store(
        self,
        key: str,
        endpoint: str,
        request_hash: str,
        status_code: int,
        response_json: str,
        created_at: datetime,
    ) -> None: ...


class SearchIndexABC(ABC):
    """Keyword full-text index — a regenerable projection, never the source of truth."""

    @abstractmethod
    def index(
        self,
        *,
        memory_id: str,
        namespace: str,
        title: str,
        summary: str,
        description: str,
        keywords: str,
    ) -> None:
        """Upsert the searchable text for one memory."""

    @abstractmethod
    def search(self, query: str, *, namespace: str | None, limit: int) -> list[SearchHit]:
        """Ranked keyword matches (best first); at most `limit` results."""

    @abstractmethod
    def clear_all(self) -> None:
        """Wipe the index (rebuild only)."""


class VectorIndexABC(ABC):
    """Semantic vector index — a regenerable projection, never the source of truth."""

    @abstractmethod
    def upsert(self, *, memory_id: str, embedding: tuple[float, ...]) -> None: ...

    @abstractmethod
    def search(self, embedding: tuple[float, ...], *, limit: int) -> list[VectorHit]:
        """Nearest neighbors by L2 distance (closest first); at most `limit` results."""

    @abstractmethod
    def clear_all(self) -> None:
        """Wipe the index (rebuild only)."""
