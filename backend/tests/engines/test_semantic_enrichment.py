"""Semantic Engine: keyword derivation and additive enrichment (Phase 2 task 6)."""

from __future__ import annotations

from mip.core.sections import Content, Semantics
from mip.engines.semantic.engine import SemanticEngine
from mip.engines.semantic.enrichment import derive_keywords, enrich_semantics
from mip.engines.validation.engine import ValidationEngine
from tests.factories import create_spec


def test_derive_keywords_ranks_by_frequency_then_alphabetically() -> None:
    content = Content(title="alpha alpha beta", summary="beta gamma", description="")
    assert derive_keywords(content)[:3] == ("alpha", "beta", "gamma")


def test_derive_keywords_drops_stopwords_and_short_tokens() -> None:
    content = Content(title="the and for a it is", summary="", description="")
    assert derive_keywords(content) == ()


def test_enrich_semantics_preserves_explicit_keywords_and_appends_derived() -> None:
    semantics = Semantics(keywords=("explicit",))
    content = Content(title="revenue growth analysis", summary="", description="")
    enriched = enrich_semantics(semantics, content)
    assert enriched.keywords[0] == "explicit"
    assert "revenue" in enriched.keywords
    assert enriched.entities == semantics.entities  # other fields untouched


def test_enrich_semantics_never_duplicates_existing_keyword() -> None:
    semantics = Semantics(keywords=("revenue",))
    content = Content(title="revenue revenue revenue", summary="", description="")
    enriched = enrich_semantics(semantics, content)
    assert enriched.keywords.count("revenue") == 1


def test_semantic_engine_enriches_a_real_memory_object(validation: ValidationEngine) -> None:
    memory = validation.build_memory(
        create_spec(title="revenue growth analysis", semantics=Semantics(keywords=("explicit",))),
        request_id="r",
        trace_id="t",
    )
    enriched = SemanticEngine().enrich(memory)
    assert "explicit" in enriched.semantics.keywords
    assert "revenue" in enriched.semantics.keywords
    assert enriched.identity == memory.identity  # only semantics changes


def test_semantic_engine_is_a_no_op_when_nothing_new_to_derive(
    validation: ValidationEngine,
) -> None:
    memory = validation.build_memory(
        create_spec(
            title="ab cd",
            summary="",
            description="",
            semantics=Semantics(keywords=("only",)),
        ),
        request_id="r",
        trace_id="t",
    )
    enriched = SemanticEngine().enrich(memory)
    assert enriched is memory
