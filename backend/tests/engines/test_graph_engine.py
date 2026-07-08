"""Knowledge Engine — relationship graph (Phase 4 task 1, ADR-0006). Exit
criterion: the graph is regenerable from Memory Objects alone.
"""

from __future__ import annotations

from uuid import UUID

from mip.core.sections import RelationshipType
from mip.core.specs import RelationshipSpec, UpdateMemorySpec
from mip.engines.knowledge.graph import GraphEngine
from mip.engines.memory_manager.engine import MemoryManager
from tests.factories import create_spec


def _create(manager: MemoryManager, **overrides: object) -> str:
    memory = manager.create_memory(create_spec(**overrides), request_id="r", trace_id="t")
    return memory.memory_id


def _link(manager: MemoryManager, source_id: str, target_id: str) -> None:
    manager.update_memory(
        source_id,
        UpdateMemorySpec(
            relationships=(
                RelationshipSpec(
                    target_memory_id=UUID(target_id), type=RelationshipType.REFERENCES
                ),
            )
        ),
        expected_version=1,
        request_id="r2",
        trace_id="t2",
    )


def test_index_memory_creates_outbound_edge(manager: MemoryManager, graph: GraphEngine) -> None:
    a = _create(manager, title="a")
    b = _create(manager, title="b")
    _link(manager, a, b)
    edges = graph.relationships_for(a)
    assert len(edges) == 1
    assert edges[0].source_memory_id == a
    assert edges[0].target_memory_id == b


def test_relationships_for_finds_inbound_edges_too(
    manager: MemoryManager, graph: GraphEngine
) -> None:
    a = _create(manager, title="a")
    b = _create(manager, title="b")
    _link(manager, a, b)
    edges = graph.relationships_for(b)  # b is only the target, never the source
    assert len(edges) == 1
    assert edges[0].source_memory_id == a


def test_neighbor_hops_bfs_distance(manager: MemoryManager, graph: GraphEngine) -> None:
    a = _create(manager, title="a")
    b = _create(manager, title="b")
    c = _create(manager, title="c")
    _link(manager, a, b)
    _link(manager, b, c)
    assert graph.neighbor_hops(a, max_hops=3) == {b: 1, c: 2}


def test_neighbor_hops_respects_max_hops(manager: MemoryManager, graph: GraphEngine) -> None:
    a = _create(manager, title="a")
    b = _create(manager, title="b")
    c = _create(manager, title="c")
    _link(manager, a, b)
    _link(manager, b, c)
    assert graph.neighbor_hops(a, max_hops=1) == {b: 1}


def test_neighbor_hops_of_isolated_memory_is_empty(
    manager: MemoryManager, graph: GraphEngine
) -> None:
    isolated = _create(manager, title="isolated")
    assert graph.neighbor_hops(isolated, max_hops=3) == {}


def test_rebuild_repopulates_from_repository(manager: MemoryManager, graph: GraphEngine) -> None:
    a = _create(manager, title="a")
    b = _create(manager, title="b")
    _create(manager, title="c")
    _link(manager, a, b)
    graph.clear()
    assert graph.relationships_for(a) == []
    count = graph.rebuild()
    assert count == 3  # every live memory is re-indexed, even with zero edges
    assert len(graph.relationships_for(a)) == 1
