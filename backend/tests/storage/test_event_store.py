"""Event store + transaction manager: append-only ordering, lossless round
trips, atomic rollback.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from mip.core.errors import MIPError, StorageError
from mip.events.types import EventType, MemoryEvent
from mip.storage.sqlite.database import Database
from mip.storage.sqlite.event_store import SqliteEventStore


def _event(memory_id: str = "m-1", **overrides: object) -> MemoryEvent:
    defaults: dict[str, object] = {
        "memory_id": memory_id,
        "event_type": EventType.MEMORY_VALIDATION_STARTED,
        "payload": {"from_state": "Created", "to_state": "Validating"},
        "actor": "tester",
        "trace_id": "trace-1",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return MemoryEvent.model_validate(defaults)


def test_append_assigns_monotonic_sequence(event_store: SqliteEventStore) -> None:
    first = event_store.append(_event())
    second = event_store.append(_event())
    assert first.sequence is not None and second.sequence is not None
    assert second.sequence > first.sequence


def test_events_round_trip_losslessly(event_store: SqliteEventStore) -> None:
    original = _event(payload={"from_state": "Created", "to_state": "Validating", "n": 1})
    stored = event_store.append(original)
    loaded = event_store.events_for("m-1")[0]
    assert loaded == stored
    assert loaded.event_id == original.event_id
    assert loaded.payload == original.payload


def test_events_for_filters_and_orders(event_store: SqliteEventStore) -> None:
    event_store.append(_event("m-1"))
    event_store.append(_event("m-2"))
    event_store.append(_event("m-1"))
    events = event_store.events_for("m-1")
    assert [e.memory_id for e in events] == ["m-1", "m-1"]
    assert event_store.count() == 3
    all_sequences = [e.sequence for e in event_store.all_events() if e.sequence is not None]
    assert len(all_sequences) == 3
    assert all_sequences == sorted(all_sequences)


def test_duplicate_event_id_rejected(event_store: SqliteEventStore) -> None:
    event = _event()
    event_store.append(event)
    with pytest.raises(StorageError):
        event_store.append(event)  # same event_id — events are immutable and unique


def test_transaction_rolls_back_on_error(db: Database, event_store: SqliteEventStore) -> None:
    class Boom(Exception):
        pass

    with pytest.raises(Boom), db.transaction():
        event_store.append(_event())
        raise Boom()
    assert event_store.count() == 0  # INV-CONCUR-003: atomic or nothing


def test_nested_transactions_join_the_outer_scope(
    db: Database, event_store: SqliteEventStore
) -> None:
    with db.transaction(), db.transaction():
        event_store.append(_event())
    assert event_store.count() == 1


def test_ping_reports_liveness(db: Database) -> None:
    assert db.ping() is True
    db.close()
    assert db.ping() is False


def test_mip_errors_pass_through_untranslated(db: Database) -> None:
    sentinel = MIPError("MEM-9999", "sentinel", http_status=418)
    with pytest.raises(MIPError) as exc_info, db.transaction():
        raise sentinel
    assert exc_info.value is sentinel  # never re-wrapped as MEM-6001
