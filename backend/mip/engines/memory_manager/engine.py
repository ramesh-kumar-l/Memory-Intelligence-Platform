"""Memory Manager — the lifecycle kernel. Every state change goes through here:
lock → legal-transition check → append event → apply to projection, all inside
one atomic transaction (INV-CONS-001/003, INV-CONCUR-003/004).
"""

from __future__ import annotations

import logging
from typing import Any

from mip.core import errors
from mip.core.clock import Clock
from mip.core.model import MemoryObject
from mip.core.specs import CreateMemorySpec, UpdateMemorySpec
from mip.core.states import CREATION_PIPELINE, MemoryState, assert_legal
from mip.engines.memory_manager.locks import LockRegistry
from mip.engines.memory_manager.versioning import build_next_version
from mip.engines.retrieval.engine import RetrievalEngine
from mip.engines.semantic.engine import SemanticEngine
from mip.engines.trust.scoring import TrustEngine
from mip.engines.validation.engine import ValidationEngine
from mip.events.projector import apply_event, rebuild
from mip.events.types import EventType, MemoryEvent, transition_event
from mip.storage.interfaces import (
    EventStoreABC,
    MemoryRecord,
    MemoryRepositoryABC,
    TransactionManagerABC,
    VersionInfo,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(
        self,
        *,
        event_store: EventStoreABC,
        repository: MemoryRepositoryABC,
        transactions: TransactionManagerABC,
        locks: LockRegistry,
        validation: ValidationEngine,
        semantic: SemanticEngine,
        trust: TrustEngine,
        indexer: RetrievalEngine,
        clock: Clock,
        lock_timeout: float = 10.0,
    ) -> None:
        self._events = event_store
        self._repo = repository
        self._tx = transactions
        self._locks = locks
        self._validation = validation
        self._semantic = semantic
        self._trust = trust
        self._indexer = indexer
        self._clock = clock
        self._lock_timeout = lock_timeout

    # ------------------------------------------------------------------ commands

    def create_memory(
        self, spec: CreateMemorySpec, *, request_id: str, trace_id: str
    ) -> MemoryObject:
        """CreateMemory: build v1, verify activation preconditions, then run the
        full pipeline Created → … → Active with one event per hop (FR-LIFE-003).
        Nothing is persisted if any check fails.
        """
        memory = self._validation.build_memory(spec, request_id=request_id, trace_id=trace_id)
        self._validation.check_activation(memory)
        self._check_relationship_targets(memory)
        # Enrichment runs only after activation preconditions pass: it augments
        # already-valid content for searchability, never rescues invalid input
        # (INV-SEM-001 must still be satisfied by the caller, per Phase 1 contract).
        memory = self._enrich(memory)
        actor = memory.audit.created_by
        memory_id = memory.memory_id
        with self._locks.acquire(memory_id, self._lock_timeout), self._tx.transaction():
            created = MemoryEvent(
                memory_id=memory_id,
                event_type=EventType.MEMORY_CREATED,
                payload={"memory": memory.model_dump(mode="json")},
                actor=actor,
                trace_id=trace_id,
                created_at=memory.lifecycle.created_at,
            )
            self._events.append(created)
            apply_event(self._repo, created)
            for from_state, to_state in CREATION_PIPELINE:
                self._emit(memory_id, from_state, to_state, actor=actor, trace_id=trace_id)
            self._indexer.index_memory(memory)
        logger.info("memory created", extra={"memory_id": memory_id, "request_id": request_id})
        return self._require_object(memory_id)

    def update_memory(
        self,
        memory_id: str,
        spec: UpdateMemorySpec,
        *,
        expected_version: int,
        request_id: str,
        trace_id: str,
    ) -> MemoryObject:
        """UpdateMemory: optimistic concurrency via expected_version (If-Match);
        creates version N+1, never overwrites (INV-CONCUR-001, FR-LIFE-006).
        """
        with self._locks.acquire(memory_id, self._lock_timeout), self._tx.transaction():
            record = self._require_live_record(memory_id)
            if record.state is not MemoryState.ACTIVE:
                raise errors.operation_not_allowed("UpdateMemory", record.state.value)
            if expected_version != record.current_version:
                raise errors.version_conflict(expected_version, record.current_version)
            current = self._require_object(memory_id)
            actor = spec.updated_by or record.owner_id
            self._emit(
                memory_id, MemoryState.ACTIVE, MemoryState.UPDATING, actor=actor, trace_id=trace_id
            )
            new_version = build_next_version(
                current, spec, now=self._clock.now(), request_id=request_id, trace_id=trace_id
            )
            self._validation.check_activation(new_version)
            self._check_relationship_targets(new_version)
            new_version = self._enrich(new_version)  # additive only, see create_memory
            self._emit(
                memory_id,
                MemoryState.UPDATING,
                MemoryState.ACTIVE,
                actor=actor,
                trace_id=trace_id,
                extra_payload={
                    "memory": new_version.model_dump(mode="json"),
                    "previous_version": current.version,
                },
            )
            self._indexer.index_memory(new_version)
        logger.info("memory updated", extra={"memory_id": memory_id, "request_id": request_id})
        return self._require_object(memory_id)

    def archive_memory(self, memory_id: str, *, actor: str, trace_id: str) -> MemoryObject:
        """Archive is idempotent: archiving an Archived memory is a no-op success."""
        with self._locks.acquire(memory_id, self._lock_timeout), self._tx.transaction():
            record = self._require_live_record(memory_id)
            if record.state is not MemoryState.ARCHIVED:
                self._emit(
                    memory_id, record.state, MemoryState.ARCHIVED, actor=actor, trace_id=trace_id
                )
        return self._require_object(memory_id)

    def restore_memory(self, memory_id: str, *, actor: str, trace_id: str) -> MemoryObject:
        """Restore is idempotent: restoring an Active memory is a no-op success."""
        with self._locks.acquire(memory_id, self._lock_timeout), self._tx.transaction():
            record = self._require_live_record(memory_id)
            if record.state is MemoryState.ARCHIVED:
                self._emit(
                    memory_id,
                    MemoryState.ARCHIVED,
                    MemoryState.ACTIVE,
                    actor=actor,
                    trace_id=trace_id,
                )
            elif record.state is not MemoryState.ACTIVE:
                raise errors.operation_not_allowed("Restore", record.state.value)
        return self._require_object(memory_id)

    def delete_memory(self, memory_id: str, *, actor: str, trace_id: str) -> dict[str, Any]:
        """DeleteMemory is idempotent (FR-API-005); Deleted is terminal and kept
        as a tombstone (ADR-0003). Only Active → Deleted is legal.
        """
        with self._locks.acquire(memory_id, self._lock_timeout), self._tx.transaction():
            record = self._repo.get_record(memory_id)
            if record is None:
                raise errors.memory_not_found(memory_id)
            if record.state is not MemoryState.DELETED:
                self._emit(
                    memory_id, record.state, MemoryState.DELETED, actor=actor, trace_id=trace_id
                )
                record = self._repo.get_record(memory_id)
        if record is None:  # pragma: no cover - tombstone row is retained by design
            raise errors.internal_failure()
        deleted_at = record.deleted_at.isoformat() if record.deleted_at else None
        return {
            "memory_id": memory_id,
            "state": MemoryState.DELETED.value,
            "deleted_at": deleted_at,
        }

    # ------------------------------------------------------------------ queries

    def get_memory(self, memory_id: str, version: int | None = None) -> MemoryObject:
        record = self._require_live_record(memory_id)
        wanted = record.current_version if version is None else version
        memory = self._repo.get_object(memory_id, None if version is None else wanted)
        if memory is None:
            raise errors.version_not_found(memory_id, wanted)
        return memory

    def list_memories(
        self,
        *,
        namespace: str | None,
        state: MemoryState | None,
        limit: int,
        after_memory_id: str | None,
    ) -> tuple[list[MemoryRecord], bool]:
        return self._repo.list_records(
            namespace=namespace, state=state, limit=limit, after_memory_id=after_memory_id
        )

    def list_versions(self, memory_id: str) -> list[VersionInfo]:
        self._require_live_record(memory_id)
        return self._repo.list_versions(memory_id)

    def rebuild_projections(self) -> dict[str, Any]:
        """Admin: replay the full event log, then re-derive search/vector
        indexes from the resulting Memory Objects (ADR-0004); report must
        come back identical for the event-sourced projections.
        """
        with self._tx.transaction():
            report = rebuild(self._events, self._repo)
            report["indexed_memories"] = self._indexer.rebuild_indexes()
        logger.info("projections rebuilt", extra={"report": report})
        return report

    # ------------------------------------------------------------------ internals

    def _enrich(self, memory: MemoryObject) -> MemoryObject:
        """Real semantic enrichment + basic trust scoring (Phase 2 tasks 6-7),
        applied before persistence so the stored version already reflects it.
        """
        enriched = self._semantic.enrich(memory)
        confidence = self._trust.derive_confidence(enriched.trust)
        return enriched.model_copy(
            update={"trust": enriched.trust.model_copy(update={"confidence": confidence})}
        )

    def _emit(
        self,
        memory_id: str,
        from_state: MemoryState,
        to_state: MemoryState,
        *,
        actor: str,
        trace_id: str,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        """Single choke point for transitions: legality check (FR-LIFE-002),
        immutable event append, then projection apply — same order everywhere.
        """
        assert_legal(from_state, to_state)
        event = transition_event(
            memory_id=memory_id,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            trace_id=trace_id,
            created_at=self._clock.now(),
            extra_payload=extra_payload,
        )
        self._events.append(event)
        apply_event(self._repo, event)

    def _require_live_record(self, memory_id: str) -> MemoryRecord:
        record = self._repo.get_record(memory_id)
        if record is None:
            raise errors.memory_not_found(memory_id)
        if record.state is MemoryState.DELETED:
            deleted_at = record.deleted_at.isoformat() if record.deleted_at else None
            raise errors.memory_deleted(memory_id, deleted_at)
        return record

    def _require_object(self, memory_id: str) -> MemoryObject:
        memory = self._repo.get_object(memory_id)
        if memory is None:  # pragma: no cover - projection/version rows are written atomically
            raise errors.internal_failure()
        return memory

    def _check_relationship_targets(self, memory: MemoryObject) -> None:
        """INV-REL-001: targets must exist (and not be deleted) unless unresolved."""
        for relationship in memory.relationships:
            if relationship.unresolved:
                continue
            target_id = str(relationship.target_memory_id)
            target = self._repo.get_record(target_id)
            if target is None or target.state is MemoryState.DELETED:
                raise errors.unresolved_relationship_target(target_id)
