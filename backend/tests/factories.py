"""Canonical valid Memory Object inputs (20-testing-strategy.md fixtures rule)."""

from __future__ import annotations

from typing import Any

from mip.core.sections import Provenance, Semantics
from mip.core.specs import CreateMemorySpec


def create_spec(**overrides: Any) -> CreateMemorySpec:
    """A canonical valid CreateMemorySpec; override any field per test."""
    base: dict[str, Any] = {
        "namespace": "default",
        "owner_id": "engineer-1",
        "title": "SQLite WAL mode enables concurrent readers",
        "summary": "WAL journal mode allows readers during a write.",
        "semantics": Semantics(keywords=("sqlite", "wal"), concepts=("durability",)),
        "provenance": Provenance(source="unit-test", method="manual"),
        "confidence": 0.9,
    }
    base.update(overrides)
    return CreateMemorySpec.model_validate(base)


def create_payload(**overrides: Any) -> dict[str, Any]:
    """A canonical valid POST /v1/memories JSON body."""
    base: dict[str, Any] = {
        "namespace": "default",
        "owner_id": "engineer-1",
        "title": "SQLite WAL mode enables concurrent readers",
        "summary": "WAL journal mode allows readers during a write.",
        "semantics": {"keywords": ["sqlite", "wal"], "concepts": ["durability"]},
        "provenance": {"source": "api-test", "method": "manual"},
        "confidence": 0.9,
    }
    base.update(overrides)
    return base
