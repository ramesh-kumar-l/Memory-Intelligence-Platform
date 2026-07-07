"""Validation Engine: assembles version-1 Memory Objects and enforces
activation preconditions (FR-SCHEMA-002, FR-INV-003).
"""

from __future__ import annotations

from uuid import uuid4

import pydantic

from mip.core import errors, invariants
from mip.core.clock import Clock
from mip.core.model import Lifecycle, MemoryObject
from mip.core.sections import (
    AuditMetadata,
    Content,
    Header,
    Identity,
    Relationship,
    Trust,
)
from mip.core.specs import CreateMemorySpec, RelationshipSpec
from mip.core.states import MemoryState


class ValidationEngine:
    def __init__(self, *, schema_version: str, encoding_version: str, clock: Clock) -> None:
        self._schema_version = schema_version
        self._encoding_version = encoding_version
        self._clock = clock

    def build_memory(
        self, spec: CreateMemorySpec, *, request_id: str, trace_id: str
    ) -> MemoryObject:
        """Assemble version 1 in state Created (FR-LIFE-001); reject invalid input
        with structured MEM-1001 violations, never a raw pydantic error.
        """
        now = self._clock.now()
        try:
            return MemoryObject(
                header=Header(
                    schema_version=self._schema_version,
                    object_type=spec.object_type,
                    encoding_version=self._encoding_version,
                ),
                identity=Identity(
                    memory_id=uuid4(), namespace=spec.namespace, owner_id=spec.owner_id
                ),
                content=Content(
                    title=spec.title,
                    summary=spec.summary,
                    description=spec.description,
                    language=spec.language,
                ),
                semantics=spec.semantics,
                relationships=build_relationships(spec.relationships, created_at=now),
                context=spec.context,
                trust=Trust(
                    confidence=spec.confidence,
                    freshness=spec.freshness,
                    provenance=spec.provenance,
                    verification_status=spec.verification_status,
                    evidence=spec.evidence,
                ),
                lifecycle=Lifecycle(version=1, state=MemoryState.CREATED, created_at=now),
                extensions=dict(spec.extensions),
                audit=AuditMetadata(
                    created_by=spec.created_by or spec.owner_id,
                    trace_id=trace_id,
                    request_id=request_id,
                ),
            )
        except pydantic.ValidationError as exc:
            raise translate_pydantic_error(exc) from exc

    def check_activation(self, memory: MemoryObject) -> None:
        """Enforce the formal activation preconditions (INV-CONS-002)."""
        violations = invariants.activation_violations(memory)
        if not violations:
            return
        if len(violations) == 1 and violations[0]["invariant"] == "INV-SEM-001":
            raise errors.missing_semantic_element()
        raise errors.validation_failed(violations)


def build_relationships(
    specs: tuple[RelationshipSpec, ...], *, created_at: object
) -> tuple[Relationship, ...]:
    """Materialize relationship specs with fresh unique ids (INV-REL-002)."""
    return tuple(
        Relationship.model_validate(
            {
                "relationship_id": uuid4(),
                "target_memory_id": spec.target_memory_id,
                "type": spec.type,
                "direction": spec.direction,
                "confidence": spec.confidence,
                "created_at": created_at,
                "unresolved": spec.unresolved,
            }
        )
        for spec in specs
    )


def translate_pydantic_error(exc: pydantic.ValidationError) -> errors.ValidationError:
    violations = [
        {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return errors.validation_failed(violations)
