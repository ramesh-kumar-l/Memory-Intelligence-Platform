"""Schema validation: required fields, ranges, extensions, round-trips
(FR-SCHEMA-001/002/003/005, INV-INT-003, INV-TRUST-002).
"""

from __future__ import annotations

from collections.abc import Callable

import pydantic
import pytest

from mip.core.invariants import activation_violations
from mip.core.model import Lifecycle, MemoryObject
from mip.core.sections import Content, Context, Identity, Semantics, Trust
from mip.core.specs import CreateMemorySpec
from mip.engines.validation.engine import ValidationEngine
from tests.factories import create_spec


@pytest.fixture
def memory(validation: ValidationEngine) -> MemoryObject:
    return validation.build_memory(create_spec(), request_id="req-1", trace_id="trace-1")


def test_canonical_object_is_valid(memory: MemoryObject) -> None:
    assert memory.version == 1
    assert memory.state.value == "Created"
    assert activation_violations(memory) == []


def test_all_eleven_sections_present(memory: MemoryObject) -> None:
    dumped = memory.model_dump()
    for section in (
        "header",
        "identity",
        "content",
        "semantics",
        "relationships",
        "context",
        "trust",
        "lifecycle",
        "storage",
        "extensions",
        "audit",
    ):
        assert section in dumped


@pytest.mark.parametrize(
    "build_invalid",
    [
        pytest.param(lambda: Content(title=""), id="empty-title"),
        pytest.param(lambda: Identity.model_validate({"memory_id": "not-a-uuid"}), id="bad-uuid"),
        pytest.param(
            lambda: Identity.model_validate(
                {"memory_id": "0" * 32, "namespace": "", "owner_id": "o"}
            ),
            id="empty-namespace",
        ),
        pytest.param(
            lambda: Trust.model_validate({"confidence": 1.5, "provenance": {"source": "x"}}),
            id="confidence-above-range",
        ),
        pytest.param(
            lambda: Trust.model_validate({"confidence": -0.1, "provenance": {"source": "x"}}),
            id="confidence-below-range",
        ),
        pytest.param(
            lambda: Trust.model_validate(
                {"confidence": 0.5, "freshness": 2.0, "provenance": {"source": "x"}}
            ),
            id="freshness-out-of-range",
        ),
        pytest.param(
            lambda: Lifecycle.model_validate(
                {"version": 0, "state": "Created", "created_at": "2026-01-01T00:00:00Z"}
            ),
            id="version-below-one",
        ),
        pytest.param(lambda: Context(importance_score=2.0), id="importance-out-of-range"),
        pytest.param(lambda: Context(access_frequency=-1), id="negative-access-frequency"),
    ],
)
def test_invalid_required_fields_rejected(build_invalid: Callable[[], object]) -> None:
    with pytest.raises(pydantic.ValidationError):
        build_invalid()


def test_spec_requires_provenance() -> None:
    with pytest.raises(pydantic.ValidationError):
        CreateMemorySpec.model_validate({"namespace": "n", "owner_id": "o", "title": "t"})


def test_unknown_top_level_fields_ignored(memory: MemoryObject) -> None:
    data = memory.model_dump(mode="json")
    data["future_field"] = {"anything": True}  # FR-SCHEMA-003
    revalidated = MemoryObject.model_validate(data)
    assert revalidated.memory_id == memory.memory_id


def test_extensions_are_preserved(validation: ValidationEngine) -> None:
    spec = create_spec(extensions={"com.example.plugin": {"score": 3}})
    memory = validation.build_memory(spec, request_id="r", trace_id="t")
    assert memory.extensions["com.example.plugin"] == {"score": 3}


def test_storage_round_trip_is_lossless(memory: MemoryObject) -> None:
    restored = MemoryObject.from_storage_json(memory.to_storage_json())
    assert restored == memory  # FR-SCHEMA-005: serialization preserves meaning


def test_public_dict_hides_storage_metadata(memory: MemoryObject) -> None:
    public = memory.to_public_dict()
    assert "storage" not in public  # schema Section 9 must never be exposed
    assert public["memory_id"] == memory.memory_id


def test_semantic_element_detection() -> None:
    assert not Semantics().has_semantic_element
    assert Semantics(keywords=("k",)).has_semantic_element


def test_activation_violations_flag_missing_semantics(
    validation: ValidationEngine, memory: MemoryObject
) -> None:
    stripped = memory.model_copy(update={"semantics": Semantics()})
    violations = activation_violations(stripped)
    assert [v["invariant"] for v in violations] == ["INV-SEM-001"]
