"""MemoryManager integration: enrichment/trust scoring run on create & update,
after activation preconditions, and indexes stay current (Phase 2 tasks 6-7)."""

from __future__ import annotations

from mip.core.sections import Semantics
from mip.core.specs import UpdateMemorySpec
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.retrieval.engine import RetrievalEngine
from tests.factories import create_spec


def test_create_memory_augments_keywords_and_blends_confidence(manager: MemoryManager) -> None:
    memory = manager.create_memory(
        create_spec(
            title="Revenue grew due to strong enterprise cloud sales",
            semantics=Semantics(keywords=("explicit-tag",)),
            confidence=0.9,
        ),
        request_id="r",
        trace_id="t",
    )
    assert "explicit-tag" in memory.semantics.keywords
    assert "revenue" in memory.semantics.keywords
    # Confidence is blended with the verification-status heuristic, not the raw input.
    assert memory.trust.confidence != 0.9


def test_update_memory_reenriches_new_version(manager: MemoryManager) -> None:
    created = manager.create_memory(create_spec(title="Widget alpha"), request_id="r", trace_id="t")
    updated = manager.update_memory(
        created.memory_id,
        UpdateMemorySpec(title="Widget alpha now mentions gigafactory production"),
        expected_version=1,
        request_id="r",
        trace_id="t",
    )
    assert "gigafactory" in updated.semantics.keywords


def test_create_memory_is_immediately_searchable(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    memory = manager.create_memory(
        create_spec(title="Findable unique token platypus"), request_id="r", trace_id="t"
    )
    results, _ = retrieval.search("platypus", mode="keyword", namespace=None, limit=10, offset=0)
    assert [r.memory_id for r in results] == [memory.memory_id]


def test_update_memory_makes_new_content_searchable(
    manager: MemoryManager, retrieval: RetrievalEngine
) -> None:
    """Semantics are carried forward and enriched additively across versions
    (UpdateMemorySpec: "absent fields keep prior values") — a title-only update
    must make the new title findable; it need not remove prior derived terms.
    """
    memory = manager.create_memory(
        create_spec(title="Original wombat title"), request_id="r", trace_id="t"
    )
    manager.update_memory(
        memory.memory_id,
        UpdateMemorySpec(title="Renamed capybara title"),
        expected_version=1,
        request_id="r",
        trace_id="t",
    )
    new_results, _ = retrieval.search(
        "capybara", mode="keyword", namespace=None, limit=10, offset=0
    )
    assert [r.memory_id for r in new_results] == [memory.memory_id]


def test_rebuild_projections_reports_indexed_memories(manager: MemoryManager) -> None:
    manager.create_memory(
        create_spec(title="Rebuild target aardvark"), request_id="r", trace_id="t"
    )
    report = manager.rebuild_projections()
    assert report["indexed_memories"] == 1
    assert report["identical"] is True
