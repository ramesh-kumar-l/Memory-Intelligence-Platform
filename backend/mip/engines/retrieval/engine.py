"""Retrieval Engine: maintains the keyword/vector indexes and serves ranked
search (Phase 2 tasks 1-3). Indexes are regenerable projections (ADR-0004) —
`rebuild_indexes` reconstructs them from the current Memory Objects alone.
"""

from __future__ import annotations

from mip.core import errors
from mip.core.model import MemoryObject
from mip.core.states import MemoryState
from mip.engines.knowledge.graph import GraphEngine
from mip.engines.retrieval import ranking
from mip.engines.retrieval.models import RankedResult
from mip.providers.embeddings import EmbeddingProviderABC
from mip.storage.interfaces import MemoryRepositoryABC, SearchIndexABC, VectorIndexABC

SUPPORTED_MODES: tuple[str, ...] = ("keyword", "semantic", "hybrid", "graph")

_MIN_CANDIDATE_FETCH = 50
_MAX_CANDIDATE_FETCH = 500
_REBUILD_PAGE_SIZE = 200
_GRAPH_MAX_HOPS = 3


class RetrievalEngine:
    def __init__(
        self,
        *,
        search_index: SearchIndexABC,
        vector_index: VectorIndexABC,
        embeddings: EmbeddingProviderABC,
        repository: MemoryRepositoryABC,
        graph: GraphEngine,
        hybrid_keyword_weight: float = 0.5,
    ) -> None:
        self._search_index = search_index
        self._vector_index = vector_index
        self._embeddings = embeddings
        self._repository = repository
        self._graph = graph
        self._keyword_weight = hybrid_keyword_weight

    def index_memory(self, memory: MemoryObject) -> None:
        """Upsert one memory into every index from its current content
        (search, vector, and graph — ADR-0006 keeps this the single choke point).
        """
        keywords_text = " ".join(memory.semantics.keywords)
        self._search_index.index(
            memory_id=memory.memory_id,
            namespace=memory.identity.namespace,
            title=memory.content.title,
            summary=memory.content.summary,
            description=memory.content.description,
            keywords=keywords_text,
        )
        embedding = self._embeddings.embed(_searchable_text(memory, keywords_text))
        self._vector_index.upsert(memory_id=memory.memory_id, embedding=embedding)
        self._graph.index_memory(memory)

    def rebuild_indexes(self) -> int:
        """Clear and repopulate every index from live (non-deleted) Memory
        Objects. Deterministic: same content always re-embeds identically.
        """
        self._search_index.clear_all()
        self._vector_index.clear_all()
        self._graph.clear()
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

    def search(
        self, query: str, *, mode: str, namespace: str | None, limit: int, offset: int
    ) -> tuple[list[RankedResult], bool]:
        """Rank Active memories by the requested mode; only Active memories are
        returned (Archived is "removed from active retrieval", Deleted is tombstoned).

        Mode "graph" treats `query` as the seed memory_id (ADR-0006) rather than
        free text — no separate seed field, so pagination/continuation-token
        handling stays identical across all four modes.
        """
        if mode not in SUPPORTED_MODES:
            raise errors.unsupported_search_mode(mode, SUPPORTED_MODES)
        if mode == "graph":
            return self._search_graph(query, namespace=namespace, limit=limit, offset=offset)
        fetch_size = min(_MAX_CANDIDATE_FETCH, max(_MIN_CANDIDATE_FETCH, offset + limit + 1))

        keyword_norm: dict[str, float] = {}
        semantic_by_id: dict[str, float] = {}
        if mode in ("keyword", "hybrid"):
            hits = self._search_index.search(query, namespace=namespace, limit=fetch_size)
            keyword_norm = ranking.normalize_keyword_scores(hits)
        if mode in ("semantic", "hybrid"):
            embedding = self._embeddings.embed(query)
            vector_hits = self._vector_index.search(embedding, limit=fetch_size)
            semantic_by_id = {
                hit.memory_id: ranking.semantic_similarity(hit.distance) for hit in vector_hits
            }

        results = self._rank_candidates(
            set(keyword_norm) | set(semantic_by_id), keyword_norm, semantic_by_id, mode, namespace
        )
        results.sort(key=lambda result: (-result.score, result.memory_id))
        has_more = len(results) > offset + limit
        return results[offset : offset + limit], has_more

    def _search_graph(
        self, seed_memory_id: str, *, namespace: str | None, limit: int, offset: int
    ) -> tuple[list[RankedResult], bool]:
        """Score = 1 / hop_distance from the seed (hop 1 = 1.0, hop 2 = 0.5, ...);
        an explicit, explainable formula, not a learned path-quality score.
        """
        hops = self._graph.neighbor_hops(seed_memory_id, max_hops=_GRAPH_MAX_HOPS)
        results: list[RankedResult] = []
        for memory_id, hop in hops.items():
            record = self._repository.get_record(memory_id)
            if record is None or record.state is not MemoryState.ACTIVE:
                continue
            if namespace is not None and record.namespace != namespace:
                continue
            results.append(RankedResult(memory_id=memory_id, score=round(1.0 / hop, 4)))
        results.sort(key=lambda result: (-result.score, result.memory_id))
        has_more = len(results) > offset + limit
        return results[offset : offset + limit], has_more

    def _rank_candidates(
        self,
        candidate_ids: set[str],
        keyword_norm: dict[str, float],
        semantic_by_id: dict[str, float],
        mode: str,
        namespace: str | None,
    ) -> list[RankedResult]:
        results: list[RankedResult] = []
        for memory_id in candidate_ids:
            record = self._repository.get_record(memory_id)
            if record is None or record.state is not MemoryState.ACTIVE:
                continue
            if namespace is not None and record.namespace != namespace:
                continue
            keyword_score = keyword_norm.get(memory_id)
            semantic_score = semantic_by_id.get(memory_id)
            if mode == "keyword":
                score = keyword_score or 0.0
            elif mode == "semantic":
                score = semantic_score or 0.0
            else:
                score = ranking.combine_hybrid(
                    keyword_score or 0.0, semantic_score or 0.0, self._keyword_weight
                )
            results.append(
                RankedResult(
                    memory_id=memory_id,
                    score=score,
                    keyword_score=keyword_score,
                    semantic_score=semantic_score,
                )
            )
        return results


def _searchable_text(memory: MemoryObject, keywords_text: str) -> str:
    return " ".join(
        (memory.content.title, memory.content.summary, memory.content.description, keywords_text)
    )
