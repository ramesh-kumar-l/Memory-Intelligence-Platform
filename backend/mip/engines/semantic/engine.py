"""Semantic Engine: real enrichment for the Enriching lifecycle hop (Phase 2
task 6). Pure and deterministic — safe to run before persistence.
"""

from __future__ import annotations

from mip.core.model import MemoryObject
from mip.engines.semantic.enrichment import enrich_semantics


class SemanticEngine:
    def enrich(self, memory: MemoryObject) -> MemoryObject:
        """Augment `semantics.keywords` with terms derived from the content."""
        enriched = enrich_semantics(memory.semantics, memory.content)
        if enriched == memory.semantics:
            return memory
        return memory.model_copy(update={"semantics": enriched})
