"""Normative state-machine suite: all 13 legal transitions succeed and map to
events; the full illegal matrix is rejected with MEM-2xxx (FR-LIFE-002).
Never allowed to be red or skipped.
"""

from __future__ import annotations

import pytest

from mip.core.errors import LifecycleError
from mip.core.states import LEGAL_TRANSITIONS, MemoryState, assert_legal, is_legal
from mip.engines.memory_manager.engine import MemoryManager
from mip.events.types import TRANSITION_EVENTS, EventType
from mip.storage.sqlite.event_store import SqliteEventStore
from tests.factories import create_spec

_ALL_PAIRS = [(a, b) for a in MemoryState for b in MemoryState]
_ILLEGAL = [pair for pair in _ALL_PAIRS if pair not in LEGAL_TRANSITIONS]


def test_exactly_thirteen_legal_transitions() -> None:
    assert len(LEGAL_TRANSITIONS) == 13


@pytest.mark.parametrize(
    ("from_state", "to_state"),
    sorted(LEGAL_TRANSITIONS),
    ids=lambda value: value.value if isinstance(value, MemoryState) else str(value),
)
def test_legal_transitions_accepted(from_state: MemoryState, to_state: MemoryState) -> None:
    assert is_legal(from_state, to_state)
    assert_legal(from_state, to_state)  # must not raise
    assert (from_state, to_state) in TRANSITION_EVENTS  # every transition emits an event


@pytest.mark.parametrize(
    ("from_state", "to_state"),
    _ILLEGAL,
    ids=lambda value: value.value if isinstance(value, MemoryState) else str(value),
)
def test_illegal_transitions_rejected(from_state: MemoryState, to_state: MemoryState) -> None:
    assert not is_legal(from_state, to_state)
    with pytest.raises(LifecycleError) as exc_info:
        assert_legal(from_state, to_state)
    assert exc_info.value.code == "MEM-2001"
    assert exc_info.value.details == {"from": from_state.value, "to": to_state.value}


def test_transition_event_map_is_a_bijection() -> None:
    assert set(TRANSITION_EVENTS) == set(LEGAL_TRANSITIONS)
    assert len(set(TRANSITION_EVENTS.values())) == len(TRANSITION_EVENTS)


def test_deleted_is_terminal_in_the_table() -> None:
    assert all(source is not MemoryState.DELETED for source, _ in LEGAL_TRANSITIONS)


def test_creation_pipeline_emits_one_event_per_transition(
    manager: MemoryManager, event_store: SqliteEventStore
) -> None:
    """FR-LIFE-001/003: Created first, then the full pipeline to Active."""
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    assert memory.state is MemoryState.ACTIVE
    events = event_store.events_for(memory.memory_id)
    assert [event.event_type for event in events] == [
        EventType.MEMORY_CREATED,
        EventType.MEMORY_VALIDATION_STARTED,
        EventType.MEMORY_VALIDATED,
        EventType.MEMORY_ENRICHMENT_STARTED,
        EventType.MEMORY_INDEXED,
        EventType.MEMORY_GRAPH_LINKED,
        EventType.MEMORY_ACTIVATED,
    ]
    sequences = [event.sequence for event in events if event.sequence is not None]
    assert len(sequences) == len(events)
    assert sequences == sorted(sequences)  # monotonic event ordering
