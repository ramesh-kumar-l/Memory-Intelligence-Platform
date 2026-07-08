"""SqliteVecVectorIndex: semantic vector index adapter (ADR-0004)."""

from __future__ import annotations

from mip.storage.sqlite.vector_index import SqliteVecVectorIndex

_DIM = 32


def _vec(*hot_indices: int) -> tuple[float, ...]:
    values = [0.0] * _DIM
    for index in hot_indices:
        values[index] = 1.0
    return tuple(values)


def test_upsert_and_search_returns_nearest_first(vector_index: SqliteVecVectorIndex) -> None:
    vector_index.upsert(memory_id="a", embedding=_vec(0))
    vector_index.upsert(memory_id="b", embedding=_vec(1))
    vector_index.upsert(memory_id="c", embedding=_vec(0, 1))
    hits = vector_index.search(_vec(0), limit=3)
    assert hits[0].memory_id == "a"
    assert hits[0].distance == 0.0


def test_reupsert_same_memory_id_replaces_vector(vector_index: SqliteVecVectorIndex) -> None:
    vector_index.upsert(memory_id="a", embedding=_vec(0))
    vector_index.upsert(memory_id="a", embedding=_vec(1))
    hits = vector_index.search(_vec(1), limit=5)
    assert len(hits) == 1
    assert hits[0].memory_id == "a"
    assert hits[0].distance == 0.0


def test_clear_all_empties_the_index(vector_index: SqliteVecVectorIndex) -> None:
    vector_index.upsert(memory_id="a", embedding=_vec(0))
    vector_index.clear_all()
    assert vector_index.search(_vec(0), limit=5) == []


def test_search_limit_is_respected(vector_index: SqliteVecVectorIndex) -> None:
    for i in range(5):
        vector_index.upsert(memory_id=f"m{i}", embedding=_vec(i % _DIM))
    hits = vector_index.search(_vec(0), limit=2)
    assert len(hits) == 2
