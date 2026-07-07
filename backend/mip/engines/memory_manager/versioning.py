"""Version N+1 construction — updates never mutate, they build a new object
(FR-LIFE-006, INV-VER-002).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mip.core.model import MemoryObject
from mip.core.specs import UpdateMemorySpec
from mip.core.states import MemoryState
from mip.engines.validation.engine import build_relationships


def build_next_version(
    current: MemoryObject,
    spec: UpdateMemorySpec,
    *,
    now: datetime,
    request_id: str,
    trace_id: str,
) -> MemoryObject:
    """Apply partial changes on top of the current version. Identity, header,
    and creation timestamp are immutable (INV-ID-001/003); absent spec fields
    keep their prior values.
    """
    content_changes = _present(
        title=spec.title,
        summary=spec.summary,
        description=spec.description,
        language=spec.language,
    )
    trust_changes = _present(
        confidence=spec.confidence,
        freshness=spec.freshness,
        verification_status=spec.verification_status,
        evidence=spec.evidence,
    )
    updates: dict[str, Any] = {
        "content": current.content.model_copy(update=content_changes),
        "trust": current.trust.model_copy(update=trust_changes),
        "lifecycle": current.lifecycle.model_copy(
            update={
                "version": current.version + 1,
                "state": MemoryState.ACTIVE,
                "updated_at": now,
            }
        ),
        "audit": current.audit.model_copy(
            update={
                "updated_by": spec.updated_by or current.identity.owner_id,
                "update_reason": spec.update_reason,
                "request_id": request_id,
                "trace_id": trace_id,
            }
        ),
    }
    if spec.semantics is not None:
        updates["semantics"] = spec.semantics
    if spec.relationships is not None:
        updates["relationships"] = build_relationships(spec.relationships, created_at=now)
    if spec.context is not None:
        updates["context"] = spec.context
    if spec.extensions is not None:
        updates["extensions"] = dict(spec.extensions)
    return current.model_copy(update=updates)


def _present(**candidates: Any) -> dict[str, Any]:
    return {key: value for key, value in candidates.items() if value is not None}
