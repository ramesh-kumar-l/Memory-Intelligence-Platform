"""Concurrency invariant suite (INV-CONCUR-*): no silent overwrites, atomic
writes, one transition at a time per memory.
"""

from __future__ import annotations

import pytest

from mip.core.errors import ConcurrencyError, ValidationError
from mip.core.sections import Semantics
from mip.core.specs import UpdateMemorySpec
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.memory_manager.locks import LockRegistry
from mip.storage.sqlite.event_store import SqliteEventStore
from tests.factories import create_spec


def test_inv_concur_001_stale_version_never_overwrites(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(title="original"), request_id="r", trace_id="t")
    manager.update_memory(
        memory.memory_id,
        UpdateMemorySpec(title="writer A"),
        expected_version=1,
        request_id="rA",
        trace_id="tA",
    )
    # Writer B still believes version is 1 — must be rejected, not merged.
    with pytest.raises(ConcurrencyError) as exc_info:
        manager.update_memory(
            memory.memory_id,
            UpdateMemorySpec(title="writer B"),
            expected_version=1,
            request_id="rB",
            trace_id="tB",
        )
    assert exc_info.value.code == "MEM-4001"
    current = manager.get_memory(memory.memory_id)
    assert current.content.title == "writer A"
    assert current.version == 2


def test_inv_concur_003_failed_update_rolls_back_atomically(
    manager: MemoryManager, event_store: SqliteEventStore
) -> None:
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    events_before = event_store.count()
    # Emptying semantics violates INV-SEM-001 → the whole update (including the
    # already-emitted Updating transition) must roll back.
    with pytest.raises(ValidationError):
        manager.update_memory(
            memory.memory_id,
            UpdateMemorySpec(semantics=Semantics()),
            expected_version=1,
            request_id="r2",
            trace_id="t2",
        )
    assert event_store.count() == events_before  # no partial commit (INV-CONS-001)
    current = manager.get_memory(memory.memory_id)
    assert current.version == 1
    assert current.state.value == "Active"


def test_inv_concur_004_one_transition_at_a_time(
    manager: MemoryManager, locks: LockRegistry
) -> None:
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    # Holding the lock simulates a transition already running elsewhere.
    with (
        locks.acquire(memory.memory_id, timeout=1.0),
        pytest.raises(ConcurrencyError) as exc_info,
    ):
        manager.archive_memory(memory.memory_id, actor="a", trace_id="t2")
    assert exc_info.value.code == "MEM-4004"
    assert exc_info.value.recoverable is True
