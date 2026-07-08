"""Retrieval Engine: indexing + keyword/semantic/hybrid search (Phase 2 tasks 1-3)."""

from __future__ import annotations

import pytest

from mip.core import errors
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.retrieval.engine import RetrievalEngine
from tests.factories import create_spec


def _create(manager: MemoryManager, **overrides: object) -> str:
    memory = manager.create_memory(create_spec(**overrides), request_id="r", trace_id="t")
    return memory.memory_id


def test_keyword_search_finds_matching_content(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    memory_id = _create(manager, title="SQLite WAL mode enables concurrent readers")
    results, has_more = retrieval.search(
        "WAL concurrent", mode="keyword", namespace=None, limit=10, offset=0
    )
    assert not has_more
    assert [r.memory_id for r in results] == [memory_id]
    assert results[0].keyword_score is not None


def test_keyword_search_no_match_returns_empty(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    _create(manager)
    results, has_more = retrieval.search(
        "zzz_no_such_token", mode="keyword", namespace=None, limit=10, offset=0
    )
    assert results == []
    assert not has_more


def test_semantic_search_ranks_similar_content_first(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    close_id = _create(
        manager, title="Revenue grew due to strong enterprise cloud sales", namespace="ns-sem"
    )
    far_id = _create(manager, title="A cat sat quietly on a warm windowsill", namespace="ns-sem")
    results, _ = retrieval.search(
        "revenue growth in the enterprise cloud business",
        mode="semantic",
        namespace="ns-sem",
        limit=10,
        offset=0,
    )
    ids_in_order = [r.memory_id for r in results]
    assert ids_in_order.index(close_id) < ids_in_order.index(far_id)


def test_hybrid_combines_keyword_and_semantic_scores(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    memory_id = _create(manager, title="SQLite WAL mode enables concurrent readers")
    results, _ = retrieval.search(
        "WAL concurrent readers", mode="hybrid", namespace=None, limit=10, offset=0
    )
    hit = next(r for r in results if r.memory_id == memory_id)
    assert hit.keyword_score is not None
    assert hit.semantic_score is not None
    assert hit.score == pytest.approx(0.5 * hit.keyword_score + 0.5 * hit.semantic_score, abs=1e-9)


def test_namespace_filter_isolates_results(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    _create(manager, title="Shared keyword alpha", namespace="ns-a")
    _create(manager, title="Shared keyword alpha", namespace="ns-b")
    results, _ = retrieval.search("alpha", mode="keyword", namespace="ns-a", limit=10, offset=0)
    assert len(results) == 1


def test_archived_memories_are_excluded_from_search(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    memory_id = _create(manager, title="Archivable unique token xylophone")
    manager.archive_memory(memory_id, actor="tester", trace_id="t")
    results, _ = retrieval.search("xylophone", mode="keyword", namespace=None, limit=10, offset=0)
    assert results == []


def test_deleted_memories_are_excluded_from_search(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    memory_id = _create(manager, title="Deletable unique token marmalade")
    manager.delete_memory(memory_id, actor="tester", trace_id="t")
    results, _ = retrieval.search("marmalade", mode="keyword", namespace=None, limit=10, offset=0)
    assert results == []


def test_pagination_reports_has_more(manager: MemoryManager, retrieval: RetrievalEngine) -> None:
    for i in range(3):
        _create(manager, title=f"Paginated widget number {i}", namespace="ns-page")
    page_one, has_more = retrieval.search(
        "widget", mode="keyword", namespace="ns-page", limit=2, offset=0
    )
    assert len(page_one) == 2
    assert has_more
    page_two, has_more_two = retrieval.search(
        "widget", mode="keyword", namespace="ns-page", limit=2, offset=2
    )
    assert len(page_two) == 1
    assert not has_more_two


def test_unsupported_mode_raises_mem_1007(retrieval: RetrievalEngine) -> None:
    with pytest.raises(errors.ValidationError) as exc_info:
        retrieval.search("anything", mode="graph", namespace=None, limit=10, offset=0)
    assert exc_info.value.code == "MEM-1007"


def test_rebuild_indexes_repopulates_from_repository(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    _create(manager, title="Rebuildable unique token quokka")
    count = retrieval.rebuild_indexes()
    assert count == 1
    results, _ = retrieval.search("quokka", mode="keyword", namespace=None, limit=10, offset=0)
    assert len(results) == 1
