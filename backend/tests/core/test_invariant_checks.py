"""Direct coverage of every activation-precondition branch in
mip/core/invariants.py, plus the pydantic-error translation path.

Invalid states are manufactured with model_copy(update=...), which bypasses
field validation on purpose — exactly the corruption the invariant layer must
still catch (defense in depth, FR-INV-004).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pydantic
import pytest

from mip.core.errors import ValidationError
from mip.core.invariants import activation_violations
from mip.core.model import MemoryObject
from mip.core.sections import Relationship, RelationshipType
from mip.core.specs import CreateMemorySpec
from mip.engines.validation.engine import ValidationEngine, translate_pydantic_error
from tests.factories import create_spec


@pytest.fixture
def memory(validation: ValidationEngine) -> MemoryObject:
    return validation.build_memory(create_spec(), request_id="r", trace_id="t")


def _invariants_of(memory: MemoryObject) -> list[str]:
    return [violation["invariant"] for violation in activation_violations(memory)]


def test_inv_trust_001_blank_provenance_source_detected(memory: MemoryObject) -> None:
    corrupted = memory.model_copy(
        update={
            "trust": memory.trust.model_copy(
                update={"provenance": memory.trust.provenance.model_copy(update={"source": " "})}
            )
        }
    )
    assert "INV-TRUST-001" in _invariants_of(corrupted)


def test_inv_ver_001_version_below_one_detected(memory: MemoryObject) -> None:
    corrupted = memory.model_copy(
        update={"lifecycle": memory.lifecycle.model_copy(update={"version": 0})}
    )
    assert "INV-VER-001" in _invariants_of(corrupted)


def test_inv_cons_002_blank_audit_actor_detected(memory: MemoryObject) -> None:
    corrupted = memory.model_copy(
        update={"audit": memory.audit.model_copy(update={"created_by": "  "})}
    )
    assert "INV-CONS-002" in _invariants_of(corrupted)


def test_inv_rel_002_duplicate_relationship_ids_detected(memory: MemoryObject) -> None:
    shared_id = uuid4()
    duplicate = Relationship(
        relationship_id=shared_id,
        target_memory_id=uuid4(),
        type=RelationshipType.REFERENCES,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        unresolved=True,
    )
    corrupted = memory.model_copy(update={"relationships": (duplicate, duplicate)})
    assert "INV-REL-002" in _invariants_of(corrupted)


def test_check_activation_raises_structured_error(
    validation: ValidationEngine, memory: MemoryObject
) -> None:
    corrupted = memory.model_copy(
        update={
            "lifecycle": memory.lifecycle.model_copy(update={"version": 0}),
            "audit": memory.audit.model_copy(update={"created_by": ""}),
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        validation.check_activation(corrupted)
    assert exc_info.value.code == "MEM-1001"
    flagged = {v["invariant"] for v in exc_info.value.details["violations"]}
    assert flagged == {"INV-VER-001", "INV-CONS-002"}


def test_translate_pydantic_error_produces_mem_1001() -> None:
    try:
        CreateMemorySpec.model_validate({"namespace": "", "owner_id": "o", "title": "t"})
    except pydantic.ValidationError as exc:
        translated = translate_pydantic_error(exc)
    assert translated.code == "MEM-1001"
    fields = {violation["field"] for violation in translated.details["violations"]}
    assert "namespace" in fields
