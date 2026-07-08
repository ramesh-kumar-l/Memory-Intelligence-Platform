"""Consolidate (Phase 4 task 2, ADR-0006). Exit criterion: consolidation
never loses history — duplicates are archived and versioned, never deleted.
"""

from __future__ import annotations

import pytest

from mip.core import errors
from mip.core.sections import RelationshipType
from mip.core.states import MemoryState
from mip.engines.knowledge.consolidate import ConsolidateEngine
from mip.engines.memory_manager.engine import MemoryManager
from tests.factories import create_spec


def _create(manager: MemoryManager, **overrides: object) -> str:
    memory = manager.create_memory(create_spec(**overrides), request_id="r", trace_id="t")
    return memory.memory_id


def test_consolidate_archives_duplicate_and_adds_relationship(
    manager: MemoryManager, consolidate_engine: ConsolidateEngine
) -> None:
    primary = _create(manager, title="primary")
    duplicate = _create(manager, title="duplicate")
    merged = consolidate_engine.consolidate(
        primary_memory_id=primary,
        duplicate_memory_ids=(duplicate,),
        actor="tester",
        request_id="r1",
        trace_id="t1",
    )
    assert merged.memory_id == primary
    assert merged.lifecycle.consolidation_count == 1

    duplicate_memory = manager.get_memory(duplicate)
    assert duplicate_memory.state is MemoryState.ARCHIVED
    assert duplicate_memory.relationships[-1].type is RelationshipType.DUPLICATE_OF
    assert str(duplicate_memory.relationships[-1].target_memory_id) == primary


def test_consolidate_preserves_duplicate_history(
    manager: MemoryManager, consolidate_engine: ConsolidateEngine
) -> None:
    primary = _create(manager, title="primary")
    duplicate = _create(manager, title="duplicate original title")
    consolidate_engine.consolidate(
        primary_memory_id=primary,
        duplicate_memory_ids=(duplicate,),
        actor="tester",
        request_id="r1",
        trace_id="t1",
    )
    v1 = manager.get_memory(duplicate, version=1)
    assert v1.content.title == "duplicate original title"
    versions = [v.version for v in manager.list_versions(duplicate)]
    assert versions == [1, 2]  # a version was added, nothing was removed


def test_consolidate_multiple_duplicates_increments_count(
    manager: MemoryManager, consolidate_engine: ConsolidateEngine
) -> None:
    primary = _create(manager, title="primary")
    dup1 = _create(manager, title="dup1")
    dup2 = _create(manager, title="dup2")
    merged = consolidate_engine.consolidate(
        primary_memory_id=primary,
        duplicate_memory_ids=(dup1, dup2),
        actor="tester",
        request_id="r1",
        trace_id="t1",
    )
    assert merged.lifecycle.consolidation_count == 2


def test_consolidate_rejects_self_merge(
    manager: MemoryManager, consolidate_engine: ConsolidateEngine
) -> None:
    primary = _create(manager, title="primary")
    with pytest.raises(errors.ValidationError) as exc_info:
        consolidate_engine.consolidate(
            primary_memory_id=primary,
            duplicate_memory_ids=(primary,),
            actor="tester",
            request_id="r1",
            trace_id="t1",
        )
    assert exc_info.value.code == "MEM-1008"


def test_consolidate_rejects_repeated_duplicate_ids(
    manager: MemoryManager, consolidate_engine: ConsolidateEngine
) -> None:
    primary = _create(manager, title="primary")
    dup = _create(manager, title="dup")
    with pytest.raises(errors.ValidationError) as exc_info:
        consolidate_engine.consolidate(
            primary_memory_id=primary,
            duplicate_memory_ids=(dup, dup),
            actor="tester",
            request_id="r1",
            trace_id="t1",
        )
    assert exc_info.value.code == "MEM-1008"


def test_consolidate_rejects_non_active_duplicate(
    manager: MemoryManager, consolidate_engine: ConsolidateEngine
) -> None:
    primary = _create(manager, title="primary")
    duplicate = _create(manager, title="duplicate")
    manager.archive_memory(duplicate, actor="tester", trace_id="t")
    with pytest.raises(errors.LifecycleError) as exc_info:
        consolidate_engine.consolidate(
            primary_memory_id=primary,
            duplicate_memory_ids=(duplicate,),
            actor="tester",
            request_id="r1",
            trace_id="t1",
        )
    assert exc_info.value.code == "MEM-2005"


def test_consolidate_unknown_primary_is_not_found(
    manager: MemoryManager, consolidate_engine: ConsolidateEngine
) -> None:
    duplicate = _create(manager, title="duplicate")
    with pytest.raises(errors.IdentityError) as exc_info:
        consolidate_engine.consolidate(
            primary_memory_id="does-not-exist",
            duplicate_memory_ids=(duplicate,),
            actor="tester",
            request_id="r1",
            trace_id="t1",
        )
    assert exc_info.value.code == "MEM-3001"
