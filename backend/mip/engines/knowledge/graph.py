"""Knowledge Engine — relationship graph (Phase 4 task 1, ADR-0006). Maintains
a regenerable adjacency projection from each memory's `relationships` field
and serves neighbor / hop-distance queries for graph search mode.
"""

from __future__ import annotations

from collections import deque

from mip.core.model import MemoryObject
from mip.storage.interfaces import GraphEdge, GraphIndexABC, MemoryRepositoryABC

_REBUILD_PAGE_SIZE = 200


class GraphEngine:
    def __init__(self, *, graph_index: GraphIndexABC, repository: MemoryRepositoryABC) -> None:
        self._graph_index = graph_index
        self._repository = repository

    def index_memory(self, memory: MemoryObject) -> None:
        """Upsert one memory's outbound edges from its current relationships."""
        edges = tuple(
            GraphEdge(
                relationship_id=str(relationship.relationship_id),
                source_memory_id=memory.memory_id,
                target_memory_id=str(relationship.target_memory_id),
                type=relationship.type.value,
                direction=relationship.direction.value,
                confidence=relationship.confidence,
            )
            for relationship in memory.relationships
        )
        self._graph_index.index_relationships(memory.memory_id, edges)

    def clear(self) -> None:
        """Wipe the graph projection (used when a caller rebuilds indexes itself)."""
        self._graph_index.clear_all()

    def rebuild(self) -> int:
        """Clear and repopulate the graph from live (non-deleted) Memory Objects
        (ADR-0006: graph regenerable from Memory Objects alone).
        """
        self._graph_index.clear_all()
        indexed = 0
        after: str | None = None
        while True:
            records, has_more = self._repository.list_records(
                namespace=None, state=None, limit=_REBUILD_PAGE_SIZE, after_memory_id=after
            )
            for record in records:
                memory = self._repository.get_object(record.memory_id)
                if memory is not None:
                    self.index_memory(memory)
                    indexed += 1
            if not records or not has_more:
                break
            after = records[-1].memory_id
        return indexed

    def neighbor_hops(self, seed_memory_id: str, *, max_hops: int) -> dict[str, int]:
        """BFS hop-distance from seed to every reachable memory (excludes the seed).
        Edges are traversed in both directions — `Relationship` is stored on the
        source only, but graph proximity is symmetric for retrieval purposes.
        """
        visited: dict[str, int] = {}
        frontier: deque[tuple[str, int]] = deque([(seed_memory_id, 0)])
        seen = {seed_memory_id}
        while frontier:
            current_id, hop = frontier.popleft()
            if hop >= max_hops:
                continue
            for edge in self._graph_index.edges_touching(current_id):
                neighbor_id = (
                    edge.target_memory_id
                    if edge.source_memory_id == current_id
                    else edge.source_memory_id
                )
                if neighbor_id in seen:
                    continue
                seen.add(neighbor_id)
                visited[neighbor_id] = hop + 1
                frontier.append((neighbor_id, hop + 1))
        return visited

    def relationships_for(self, memory_id: str) -> list[GraphEdge]:
        """All edges touching one memory (both outbound and inbound)."""
        return self._graph_index.edges_touching(memory_id)
