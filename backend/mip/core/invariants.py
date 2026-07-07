"""INV-* checks — the formal activation preconditions of 30-memory/04-memory-invariants.md.

A Memory Object may only become Active when every condition holds; violations
are returned as structured entries so callers can raise MEM-1xxx errors
(FR-INV-003: no public API commits data that violates an invariant).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mip.core.model import MemoryObject


def activation_violations(memory: MemoryObject) -> list[dict[str, Any]]:
    """Return every violated activation precondition (empty list = compliant).

    Field-level shape/range rules (INV-INT-003, INV-TRUST-002) are enforced by
    the pydantic model itself; this checks the cross-field rules on top.
    """
    violations: list[dict[str, Any]] = []

    if not memory.semantics.has_semantic_element:
        violations.append(
            {
                "invariant": "INV-SEM-001",
                "field": "semantics",
                "message": "at least one semantic element is required",
            }
        )
    if not memory.trust.provenance.source.strip():
        violations.append(
            {
                "invariant": "INV-TRUST-001",
                "field": "trust.provenance.source",
                "message": "provenance source must be non-empty",
            }
        )
    if memory.lifecycle.version < 1:
        violations.append(
            {
                "invariant": "INV-VER-001",
                "field": "lifecycle.version",
                "message": "version must be >= 1",
            }
        )
    if not memory.audit.created_by.strip():
        violations.append(
            {
                "invariant": "INV-CONS-002",
                "field": "audit.created_by",
                "message": "audit trail must be initialized",
            }
        )
    seen_relationship_ids = set()
    for relationship in memory.relationships:
        if relationship.relationship_id in seen_relationship_ids:
            violations.append(
                {
                    "invariant": "INV-REL-002",
                    "field": "relationships",
                    "message": f"duplicate relationship_id {relationship.relationship_id}",
                }
            )
        seen_relationship_ids.add(relationship.relationship_id)
    return violations
