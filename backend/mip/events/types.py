"""Lifecycle event types — one immutable event per transition (INV-CONS-003).

The seven canonical names from the state machine spec are included verbatim;
the remaining types additively name the other transitions so every legal
transition maps to exactly one event type (deterministic replay, FR-LIFE-004).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from mip.core.states import MemoryState


class EventType(StrEnum):
    MEMORY_CREATED = "MemoryCreated"
    MEMORY_VALIDATION_STARTED = "MemoryValidationStarted"
    MEMORY_VALIDATED = "MemoryValidated"
    MEMORY_VALIDATION_FAILED = "MemoryValidationFailed"
    MEMORY_VALIDATION_RETRIED = "MemoryValidationRetried"
    MEMORY_ENRICHMENT_STARTED = "MemoryEnrichmentStarted"
    MEMORY_INDEXED = "MemoryIndexed"
    MEMORY_GRAPH_LINKED = "MemoryGraphLinked"
    MEMORY_ACTIVATED = "MemoryActivated"
    MEMORY_UPDATE_STARTED = "MemoryUpdateStarted"
    MEMORY_UPDATED = "MemoryUpdated"
    MEMORY_ARCHIVED = "MemoryArchived"
    MEMORY_RESTORED = "MemoryRestored"
    MEMORY_DELETED = "MemoryDeleted"


#: Bijection: legal transition → event type (13 entries, mirrors LEGAL_TRANSITIONS).
TRANSITION_EVENTS: dict[tuple[MemoryState, MemoryState], EventType] = {
    (MemoryState.CREATED, MemoryState.VALIDATING): EventType.MEMORY_VALIDATION_STARTED,
    (MemoryState.VALIDATING, MemoryState.VALIDATED): EventType.MEMORY_VALIDATED,
    (MemoryState.VALIDATING, MemoryState.VALIDATION_FAILED): EventType.MEMORY_VALIDATION_FAILED,
    (MemoryState.VALIDATION_FAILED, MemoryState.VALIDATING): EventType.MEMORY_VALIDATION_RETRIED,
    (MemoryState.VALIDATED, MemoryState.ENRICHING): EventType.MEMORY_ENRICHMENT_STARTED,
    (MemoryState.ENRICHING, MemoryState.INDEXED): EventType.MEMORY_INDEXED,
    (MemoryState.INDEXED, MemoryState.GRAPH_LINKED): EventType.MEMORY_GRAPH_LINKED,
    (MemoryState.GRAPH_LINKED, MemoryState.ACTIVE): EventType.MEMORY_ACTIVATED,
    (MemoryState.ACTIVE, MemoryState.UPDATING): EventType.MEMORY_UPDATE_STARTED,
    (MemoryState.UPDATING, MemoryState.ACTIVE): EventType.MEMORY_UPDATED,
    (MemoryState.ACTIVE, MemoryState.ARCHIVED): EventType.MEMORY_ARCHIVED,
    (MemoryState.ARCHIVED, MemoryState.ACTIVE): EventType.MEMORY_RESTORED,
    (MemoryState.ACTIVE, MemoryState.DELETED): EventType.MEMORY_DELETED,
}


class MemoryEvent(BaseModel):
    """Immutable, append-only lifecycle event. `sequence` is assigned on append."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    memory_id: str
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    actor: str
    trace_id: str
    created_at: datetime
    sequence: int | None = None


def transition_event(
    *,
    memory_id: str,
    from_state: MemoryState,
    to_state: MemoryState,
    actor: str,
    trace_id: str,
    created_at: datetime,
    extra_payload: dict[str, Any] | None = None,
) -> MemoryEvent:
    """Build the event for a legal transition; payload always records from/to."""
    payload: dict[str, Any] = {"from_state": from_state.value, "to_state": to_state.value}
    if extra_payload:
        payload.update(extra_payload)
    return MemoryEvent(
        memory_id=memory_id,
        event_type=TRANSITION_EVENTS[(from_state, to_state)],
        payload=payload,
        actor=actor,
        trace_id=trace_id,
        created_at=created_at,
    )
