"""Learn (Phase 4 task 3, ADR-0006): update derived semantic knowledge and,
optionally, mature the trust evidence chain — in one version bump, one audit
event. Reuses `MemoryManager.update_memory` exclusively, so Learn can never
touch anything Update itself couldn't (evidence is appended, never replaced).
"""

from __future__ import annotations

from typing import Any

from mip.core import errors
from mip.core.model import MemoryObject
from mip.core.sections import Semantics
from mip.core.specs import UpdateMemorySpec
from mip.core.states import MemoryState
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.trust.maturation import mature_evidence
from mip.engines.trust.scoring import TrustEngine

_SEMANTIC_TUPLE_FIELDS = (
    "entities",
    "concepts",
    "activities",
    "events",
    "locations",
    "topics",
    "timestamps",
    "keywords",
)


class LearnEngine:
    def __init__(self, *, manager: MemoryManager, trust: TrustEngine) -> None:
        self._manager = manager
        self._trust = trust

    def learn(
        self,
        memory_id: str,
        *,
        derived: Semantics | None,
        new_evidence: tuple[dict[str, Any], ...],
        verifier: str | None,
        reason: str,
        actor: str | None,
        request_id: str,
        trace_id: str,
    ) -> MemoryObject:
        if derived is None and not new_evidence:
            raise errors.invalid_request(
                [
                    {
                        "field": "derived",
                        "message": "at least one of derived/new_evidence is required",
                    }
                ]
            )
        memory = self._manager.get_memory(memory_id)
        if memory.state is not MemoryState.ACTIVE:
            raise errors.operation_not_allowed("Learn", memory.state.value)

        updates: dict[str, Any] = {"update_reason": f"learn: {reason}", "updated_by": actor}
        if derived is not None:
            updates["semantics"] = _union_semantics(memory.semantics, derived)
        if new_evidence:
            matured = mature_evidence(memory.trust, new_evidence=new_evidence, verifier=verifier)
            updates["evidence"] = matured.evidence
            updates["source_count"] = matured.source_count
            updates["verification_status"] = matured.verification_status
            updates["confidence"] = self._trust.derive_confidence(matured)

        spec = UpdateMemorySpec.model_validate(updates)
        return self._manager.update_memory(
            memory_id,
            spec,
            expected_version=memory.version,
            request_id=request_id,
            trace_id=trace_id,
        )


def _union_semantics(current: Semantics, derived: Semantics) -> Semantics:
    """Non-destructive union — same strategy as semantic/enrichment.py's keyword
    merge (INV-SEM-002: derived meaning supplements, never invalidates, evidence).
    """
    updates: dict[str, Any] = {}
    for field in _SEMANTIC_TUPLE_FIELDS:
        derived_values = getattr(derived, field)
        if not derived_values:
            continue
        merged = list(getattr(current, field))
        seen = set(merged)
        for value in derived_values:
            if value not in seen:
                merged.append(value)
                seen.add(value)
        updates[field] = tuple(merged)
    if derived.sentiment is not None:
        updates["sentiment"] = derived.sentiment
    if derived.intent is not None:
        updates["intent"] = derived.intent
    return current.model_copy(update=updates) if updates else current
