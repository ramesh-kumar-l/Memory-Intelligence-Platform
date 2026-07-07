"""State invariant suite (INV-STATE-*): single state, approved transitions
only, Deleted is terminal.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from mip.core.errors import LifecycleError
from mip.core.specs import UpdateMemorySpec
from mip.core.states import MemoryState
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.validation.engine import ValidationEngine
from mip.events.projector import apply_event
from mip.events.types import EventType, MemoryEvent
from mip.storage.sqlite.database import Database
from mip.storage.sqlite.event_store import SqliteEventStore
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository
from tests.factories import create_spec


def test_inv_state_001_exactly_one_state(
    manager: MemoryManager, repo: SqliteMemoryRepository
) -> None:
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    record = repo.get_record(memory.memory_id)
    assert record is not None
    assert isinstance(record.state, MemoryState)
    assert record.state is memory.state


def test_inv_state_002_engine_rejects_illegal_transition(
    manager: MemoryManager,
    repo: SqliteMemoryRepository,
    event_store: SqliteEventStore,
    validation: ValidationEngine,
    db: Database,
) -> None:
    """Seed a memory stuck in Created (no pipeline) and try to archive it."""
    memory = validation.build_memory(create_spec(), request_id="r", trace_id="t")
    created = MemoryEvent(
        memory_id=memory.memory_id,
        event_type=EventType.MEMORY_CREATED,
        payload={"memory": memory.model_dump(mode="json")},
        actor="seeder",
        trace_id="t",
        created_at=memory.lifecycle.created_at,
    )
    with db.transaction():
        event_store.append(created)
        apply_event(repo, created)

    with pytest.raises(LifecycleError) as exc_info:
        manager.archive_memory(memory.memory_id, actor="a", trace_id="t2")
    assert exc_info.value.code == "MEM-2001"
    assert exc_info.value.details == {"from": "Created", "to": "Archived"}


def test_inv_state_003_deleted_is_terminal(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    manager.delete_memory(memory.memory_id, actor="a", trace_id="t2")

    operations: tuple[Callable[[], object], ...] = (
        lambda: manager.restore_memory(memory.memory_id, actor="a", trace_id="t3"),
        lambda: manager.archive_memory(memory.memory_id, actor="a", trace_id="t4"),
        lambda: manager.update_memory(
            memory.memory_id,
            UpdateMemorySpec(title="zombie"),
            expected_version=1,
            request_id="r5",
            trace_id="t5",
        ),
        lambda: manager.get_memory(memory.memory_id),
    )
    for operation in operations:
        with pytest.raises(LifecycleError) as exc_info:
            operation()
        assert exc_info.value.code == "MEM-2003"


def test_inv_state_003_repeated_delete_is_idempotent_success(manager: MemoryManager) -> None:
    memory = manager.create_memory(create_spec(), request_id="r", trace_id="t")
    first = manager.delete_memory(memory.memory_id, actor="a", trace_id="t2")
    second = manager.delete_memory(memory.memory_id, actor="a", trace_id="t3")
    assert second == first  # FR-API-005: repeated delete returns success
    assert second["state"] == "Deleted"
