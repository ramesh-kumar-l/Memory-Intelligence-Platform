"""Projection maintenance — the single place events become state.

Live writes and full rebuilds both go through apply_event, so replay produces
identical projections by construction (INV-CONS-004, FR-LIFE-004).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mip.core.model import MemoryObject
from mip.core.states import MemoryState
from mip.events.types import EventType, MemoryEvent
from mip.storage.interfaces import EventStoreABC, MemoryRepositoryABC


def apply_event(repository: MemoryRepositoryABC, event: MemoryEvent) -> None:
    """Apply one immutable event to the projection. Must stay deterministic:
    every value written derives from the event alone, never from wall-clock time.
    """
    if event.event_type in (EventType.MEMORY_CREATED, EventType.MEMORY_IMPORTED):
        memory = MemoryObject.model_validate(event.payload["memory"])
        repository.create(memory)
    elif event.event_type is EventType.MEMORY_UPDATED:
        memory = MemoryObject.model_validate(event.payload["memory"])
        repository.publish_version(
            memory,
            previous_version=int(event.payload["previous_version"]),
            published_at=event.created_at,
        )
    elif event.event_type is EventType.MEMORY_VERSION_IMPORTED:
        # Fidelity requires the *exported* timestamps, not "now" — unlike a live
        # Update, this event's own created_at is only "when the import ran."
        memory = MemoryObject.model_validate(event.payload["memory"])
        repository.publish_version(
            memory,
            previous_version=int(event.payload["previous_version"]),
            published_at=memory.lifecycle.updated_at or event.created_at,
        )
        # publish_version always lands on Active; restore the exported state verbatim.
        state_timestamp = _terminal_state_timestamp(memory) or event.created_at
        repository.set_state(event.memory_id, memory.state, state_timestamp)
    elif event.event_type is EventType.MEMORY_CONSOLIDATED:
        repository.record_consolidation(event.memory_id, event.created_at)
    else:
        to_state = MemoryState(event.payload["to_state"])
        repository.set_state(event.memory_id, to_state, event.created_at)


def _terminal_state_timestamp(memory: MemoryObject) -> datetime | None:
    """The exported timestamp that matches `memory.lifecycle.state`, so
    reimporting an Archived/Deleted memory restores its original stamp
    instead of stamping "when the import ran" (ADR-0006 fidelity target).
    """
    if memory.state is MemoryState.ARCHIVED:
        return memory.lifecycle.archived_at
    if memory.state is MemoryState.DELETED:
        return memory.lifecycle.deleted_at
    return None


def rebuild(event_store: EventStoreABC, repository: MemoryRepositoryABC) -> dict[str, Any]:
    """Rebuild all projections from the event log and report replay identity."""
    before = repository.dump_state()
    repository.clear_all()
    replayed = 0
    for event in event_store.all_events():
        apply_event(repository, event)
        replayed += 1
    after = repository.dump_state()
    return {
        "events_replayed": replayed,
        "memories": len(after["memories"]),
        "identical": before == after,
    }
