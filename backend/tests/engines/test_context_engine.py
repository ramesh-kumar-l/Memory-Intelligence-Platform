"""Context Engine: BuildContext / Context Package (Phase 2 task 5)."""

from __future__ import annotations

from mip.core.sections import Context
from mip.engines.context.engine import ContextEngine
from mip.engines.memory_manager.engine import MemoryManager
from tests.factories import create_spec


def test_build_context_returns_ranked_items_with_memory_content(
    manager: MemoryManager, context_engine: ContextEngine
) -> None:
    manager.create_memory(
        create_spec(title="Quarterly revenue growth in the cloud division", namespace="ns-ctx"),
        request_id="r",
        trace_id="t",
    )
    package = context_engine.build_context(
        "revenue cloud", namespace="ns-ctx", mode="hybrid", limit=10, offset=0
    )
    assert package["query"] == "revenue cloud"
    assert package["complete"] is True
    assert len(package["items"]) == 1
    item = package["items"][0]
    assert item["memory"]["content"]["title"].startswith("Quarterly revenue")
    assert 0.0 <= item["blended_score"] <= 1.0


def test_build_context_favors_higher_importance_when_relevance_ties(
    manager: MemoryManager, context_engine: ContextEngine
) -> None:
    low = manager.create_memory(
        create_spec(
            title="Widget alpha report",
            namespace="ns-ctx2",
            context=Context(importance_score=0.1),
        ),
        request_id="r",
        trace_id="t",
    )
    high = manager.create_memory(
        create_spec(
            title="Widget alpha report",
            namespace="ns-ctx2",
            context=Context(importance_score=0.9),
        ),
        request_id="r",
        trace_id="t",
    )
    package = context_engine.build_context(
        "widget alpha", namespace="ns-ctx2", mode="keyword", limit=10, offset=0
    )
    ids_in_order = [item["memory"]["memory_id"] for item in package["items"]]
    assert ids_in_order.index(high.memory_id) < ids_in_order.index(low.memory_id)


def test_build_context_reports_partial_when_more_results_exist(
    manager: MemoryManager, context_engine: ContextEngine
) -> None:
    for i in range(3):
        manager.create_memory(
            create_spec(title=f"Context page item {i}", namespace="ns-ctx3"),
            request_id="r",
            trace_id="t",
        )
    package = context_engine.build_context(
        "context page item", namespace="ns-ctx3", mode="keyword", limit=2, offset=0
    )
    assert package["complete"] is False
    assert len(package["items"]) == 2
