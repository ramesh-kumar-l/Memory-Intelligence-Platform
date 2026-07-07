"""Replay suite: rebuilding projections from the event log must reproduce
identical state (INV-CONS-004, FR-LIFE-004, Phase 1 acceptance criterion).
"""

from __future__ import annotations

from mip.core.specs import UpdateMemorySpec
from mip.core.states import MemoryState
from mip.engines.memory_manager.engine import MemoryManager
from mip.storage.sqlite.event_store import SqliteEventStore
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository
from tests.factories import create_spec


def _build_history(manager: MemoryManager) -> tuple[str, str, str]:
    """Exercise every Phase 1 operation: create x3, update, archive+restore, delete."""
    m1 = manager.create_memory(create_spec(title="First"), request_id="r1", trace_id="t1")
    m2 = manager.create_memory(create_spec(title="Second"), request_id="r2", trace_id="t2")
    m3 = manager.create_memory(create_spec(title="Third"), request_id="r3", trace_id="t3")
    manager.update_memory(
        m1.memory_id,
        UpdateMemorySpec(title="First, revised", update_reason="clarity"),
        expected_version=1,
        request_id="r4",
        trace_id="t4",
    )
    manager.archive_memory(m2.memory_id, actor="tester", trace_id="t5")
    manager.restore_memory(m2.memory_id, actor="tester", trace_id="t6")
    manager.delete_memory(m3.memory_id, actor="tester", trace_id="t7")
    return m1.memory_id, m2.memory_id, m3.memory_id


def test_replay_reproduces_identical_state(
    manager: MemoryManager,
    repo: SqliteMemoryRepository,
    event_store: SqliteEventStore,
) -> None:
    m1_id, m2_id, m3_id = _build_history(manager)
    before = repo.dump_state()
    event_count = event_store.count()

    report = manager.rebuild_projections()

    assert report["identical"] is True
    assert report["events_replayed"] == event_count
    assert report["memories"] == 3
    assert repo.dump_state() == before

    # Spot-check the projections survived with full fidelity.
    m1 = manager.get_memory(m1_id)
    assert m1.version == 2
    assert m1.content.title == "First, revised"
    assert m1.state is MemoryState.ACTIVE
    assert manager.get_memory(m2_id).state is MemoryState.ACTIVE
    m3_record = repo.get_record(m3_id)
    assert m3_record is not None
    assert m3_record.state is MemoryState.DELETED  # tombstone retained (ADR-0003)


def test_rebuild_is_idempotent(manager: MemoryManager) -> None:
    _build_history(manager)
    first = manager.rebuild_projections()
    second = manager.rebuild_projections()
    assert first["identical"] is True
    assert second == first


def test_events_are_never_mutated_by_rebuild(
    manager: MemoryManager, event_store: SqliteEventStore
) -> None:
    _build_history(manager)
    before = [(e.sequence, e.event_id, e.event_type) for e in event_store.all_events()]
    manager.rebuild_projections()
    after = [(e.sequence, e.event_id, e.event_type) for e in event_store.all_events()]
    assert after == before  # append-only log untouched by projection rebuild
