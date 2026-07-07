"""Lifecycle states and the legal-transition table.

Authoritative source: 30-memory/03-memory-state-machine.md (11 states, 13 legal
transitions — ADR-0003). All other transitions are illegal and rejected.
"""

from __future__ import annotations

from enum import StrEnum

from mip.core import errors


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


#: The 13 legal transitions — exactly the table in the state machine spec.
LEGAL_TRANSITIONS: frozenset[tuple[MemoryState, MemoryState]] = frozenset(
    {
        (MemoryState.CREATED, MemoryState.VALIDATING),
        (MemoryState.VALIDATING, MemoryState.VALIDATED),
        (MemoryState.VALIDATING, MemoryState.VALIDATION_FAILED),
        (MemoryState.VALIDATION_FAILED, MemoryState.VALIDATING),
        (MemoryState.VALIDATED, MemoryState.ENRICHING),
        (MemoryState.ENRICHING, MemoryState.INDEXED),
        (MemoryState.INDEXED, MemoryState.GRAPH_LINKED),
        (MemoryState.GRAPH_LINKED, MemoryState.ACTIVE),
        (MemoryState.ACTIVE, MemoryState.UPDATING),
        (MemoryState.UPDATING, MemoryState.ACTIVE),
        (MemoryState.ACTIVE, MemoryState.ARCHIVED),
        (MemoryState.ARCHIVED, MemoryState.ACTIVE),
        (MemoryState.ACTIVE, MemoryState.DELETED),
    }
)

#: Deleted is terminal (INV-STATE-003, FR-LIFE-005).
TERMINAL_STATES: frozenset[MemoryState] = frozenset({MemoryState.DELETED})

#: The Phase 1 creation pipeline: Created → … → Active, one event per hop.
CREATION_PIPELINE: tuple[tuple[MemoryState, MemoryState], ...] = (
    (MemoryState.CREATED, MemoryState.VALIDATING),
    (MemoryState.VALIDATING, MemoryState.VALIDATED),
    (MemoryState.VALIDATED, MemoryState.ENRICHING),
    (MemoryState.ENRICHING, MemoryState.INDEXED),
    (MemoryState.INDEXED, MemoryState.GRAPH_LINKED),
    (MemoryState.GRAPH_LINKED, MemoryState.ACTIVE),
)


def is_legal(from_state: MemoryState, to_state: MemoryState) -> bool:
    return (from_state, to_state) in LEGAL_TRANSITIONS


def assert_legal(from_state: MemoryState, to_state: MemoryState) -> None:
    """Raise MEM-2001 unless the transition appears in the legal table (FR-LIFE-002)."""
    if not is_legal(from_state, to_state):
        raise errors.illegal_transition(from_state.value, to_state.value)
