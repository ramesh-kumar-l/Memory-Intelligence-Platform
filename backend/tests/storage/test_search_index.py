"""Fts5SearchIndex: keyword index adapter (ADR-0004)."""

from __future__ import annotations

from mip.storage.sqlite.search_index import Fts5SearchIndex


def test_index_and_search_finds_by_title(search_index: Fts5SearchIndex) -> None:
    search_index.index(
        memory_id="m1",
        namespace="ns",
        title="Quarterly revenue report",
        summary="",
        description="",
        keywords="",
    )
    hits = search_index.search("revenue", namespace=None, limit=10)
    assert [hit.memory_id for hit in hits] == ["m1"]


def test_reindexing_same_memory_id_replaces_content(search_index: Fts5SearchIndex) -> None:
    search_index.index(
        memory_id="m1", namespace="ns", title="alpha", summary="", description="", keywords=""
    )
    search_index.index(
        memory_id="m1", namespace="ns", title="beta", summary="", description="", keywords=""
    )
    assert search_index.search("alpha", namespace=None, limit=10) == []
    assert [hit.memory_id for hit in search_index.search("beta", namespace=None, limit=10)] == [
        "m1"
    ]


def test_namespace_filter(search_index: Fts5SearchIndex) -> None:
    search_index.index(
        memory_id="a", namespace="ns-a", title="shared", summary="", description="", keywords=""
    )
    search_index.index(
        memory_id="b", namespace="ns-b", title="shared", summary="", description="", keywords=""
    )
    hits = search_index.search("shared", namespace="ns-a", limit=10)
    assert [hit.memory_id for hit in hits] == ["a"]


def test_query_with_special_characters_does_not_raise(search_index: Fts5SearchIndex) -> None:
    search_index.index(
        memory_id="m1", namespace="ns", title="alpha", summary="", description="", keywords=""
    )
    hits = search_index.search('alpha OR "quoted" NOT ^weird*', namespace=None, limit=10)
    assert isinstance(hits, list)


def test_blank_query_returns_no_hits(search_index: Fts5SearchIndex) -> None:
    search_index.index(
        memory_id="m1", namespace="ns", title="alpha", summary="", description="", keywords=""
    )
    assert search_index.search("   ", namespace=None, limit=10) == []


def test_clear_all_empties_the_index(search_index: Fts5SearchIndex) -> None:
    search_index.index(
        memory_id="m1", namespace="ns", title="alpha", summary="", description="", keywords=""
    )
    search_index.clear_all()
    assert search_index.search("alpha", namespace=None, limit=10) == []
