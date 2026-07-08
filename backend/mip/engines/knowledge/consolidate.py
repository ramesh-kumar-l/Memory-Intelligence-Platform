"""Consolidate (Phase 4 task 2, ADR-0006): merge duplicate memories via
relationships. Pure orchestration over `MemoryManager.update_memory` (adds a
`duplicate_of` relationship, a new version) and `MemoryManager.archive_memory`
(existing, idempotent) — nothing is deleted, so history is never lost.
"""

from __future__ import annotations

from uuid import UUID

from mip.core import errors
from mip.core.clock import Clock
from mip.core.model import MemoryObject
from mip.core.sections import Relationship, RelationshipType
from mip.core.specs import RelationshipSpec, UpdateMemorySpec
from mip.core.states import MemoryState
from mip.engines.memory_manager.engine import MemoryManager
from mip.events.projector import apply_event
from mip.events.types import consolidation_event
from mip.storage.interfaces import EventStoreABC, MemoryRepositoryABC, TransactionManagerABC


class ConsolidateEngine:
    def __init__(
        self,
        *,
        manager: MemoryManager,
        event_store: EventStoreABC,
        repository: MemoryRepositoryABC,
        transactions: TransactionManagerABC,
        clock: Clock,
    ) -> None:
        self._manager = manager
        self._events = event_store
        self._repo = repository
        self._tx = transactions
        self._clock = clock

    def consolidate(
        self,
        *,
        primary_memory_id: str,
        duplicate_memory_ids: tuple[str, ...],
        actor: str,
        request_id: str,
        trace_id: str,
    ) -> MemoryObject:
        self._validate_request(primary_memory_id, duplicate_memory_ids)
        primary = self._manager.get_memory(primary_memory_id)
        if primary.state is not MemoryState.ACTIVE:
            raise errors.consolidation_target_not_active(primary_memory_id, primary.state.value)

        merged: list[str] = []
        for duplicate_id in duplicate_memory_ids:
            duplicate = self._manager.get_memory(duplicate_id)
            if duplicate.state is not MemoryState.ACTIVE:
                raise errors.consolidation_target_not_active(duplicate_id, duplicate.state.value)
            self._mark_duplicate(
                duplicate,
                primary_memory_id=primary_memory_id,
                actor=actor,
                request_id=request_id,
                trace_id=trace_id,
            )
            self._manager.archive_memory(duplicate_id, actor=actor, trace_id=trace_id)
            merged.append(duplicate_id)

        with self._tx.transaction():
            for duplicate_id in merged:
                event = consolidation_event(
                    primary_memory_id=primary_memory_id,
                    duplicate_memory_id=duplicate_id,
                    actor=actor,
                    trace_id=trace_id,
                    created_at=self._clock.now(),
                )
                self._events.append(event)
                apply_event(self._repo, event)
        return self._manager.get_memory(primary_memory_id)

    def _mark_duplicate(
        self,
        duplicate: MemoryObject,
        *,
        primary_memory_id: str,
        actor: str,
        request_id: str,
        trace_id: str,
    ) -> None:
        already_marked = any(
            relationship.type is RelationshipType.DUPLICATE_OF
            and str(relationship.target_memory_id) == primary_memory_id
            for relationship in duplicate.relationships
        )
        if already_marked:
            return
        new_relationship = RelationshipSpec(
            target_memory_id=UUID(primary_memory_id), type=RelationshipType.DUPLICATE_OF
        )
        relationships = (*(_to_spec(r) for r in duplicate.relationships), new_relationship)
        self._manager.update_memory(
            duplicate.memory_id,
            UpdateMemorySpec(
                relationships=relationships,
                updated_by=actor,
                update_reason=f"consolidate: merged into {primary_memory_id}",
            ),
            expected_version=duplicate.version,
            request_id=request_id,
            trace_id=trace_id,
        )

    def _validate_request(
        self, primary_memory_id: str, duplicate_memory_ids: tuple[str, ...]
    ) -> None:
        if not duplicate_memory_ids:
            raise errors.invalid_consolidation_request("duplicate_memory_ids must be non-empty")
        if len(set(duplicate_memory_ids)) != len(duplicate_memory_ids):
            raise errors.invalid_consolidation_request("duplicate_memory_ids must not repeat")
        if primary_memory_id in duplicate_memory_ids:
            raise errors.invalid_consolidation_request(
                "primary_memory_id cannot be its own duplicate"
            )


def _to_spec(relationship: Relationship) -> RelationshipSpec:
    return RelationshipSpec(
        target_memory_id=relationship.target_memory_id,
        type=relationship.type,
        direction=relationship.direction,
        confidence=relationship.confidence,
        unresolved=relationship.unresolved,
    )
