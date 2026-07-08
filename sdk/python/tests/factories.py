"""Builds a public-API-shaped Memory Object dict for mock-transport tests."""

from __future__ import annotations

from typing import Any

MEMORY_ID = "5f8d9a4e-1b2c-4d3e-9f0a-1234567890ab"


def sample_memory_dict(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "memory_id": MEMORY_ID,
        "header": {
            "schema_version": "1.0",
            "object_type": "Experience",
            "encoding_version": "1.0",
            "checksum": None,
        },
        "identity": {
            "memory_id": MEMORY_ID,
            "namespace": "demo",
            "owner_id": "user-1",
            "tenant_id": None,
            "parent_id": None,
            "root_episode_id": None,
        },
        "content": {
            "title": "Sample memory",
            "summary": "A short summary.",
            "description": "",
            "language": "en",
            "attachments": [],
            "media_refs": [],
            "notes": [],
        },
        "semantics": {
            "entities": [],
            "concepts": ["onboarding"],
            "activities": [],
            "events": [],
            "locations": [],
            "topics": [],
            "timestamps": [],
            "keywords": ["sample"],
            "sentiment": None,
            "intent": None,
        },
        "relationships": [],
        "context": {
            "importance_score": 0.5,
            "recency_score": 1.0,
            "access_frequency": 0,
            "last_accessed": None,
            "relevance_tags": [],
            "goals": [],
        },
        "trust": {
            "confidence": 0.8,
            "freshness": 1.0,
            "provenance": {
                "source": "test-suite",
                "method": None,
                "location": None,
                "captured_at": None,
                "agent": None,
            },
            "evidence": [],
            "verification_status": "Unknown",
            "source_count": 1,
            "explanation": "",
        },
        "lifecycle": {
            "version": 1,
            "state": "Active",
            "created_at": "2026-07-08T00:00:00Z",
            "updated_at": None,
            "archived_at": None,
            "deleted_at": None,
            "consolidation_count": 0,
        },
        "extensions": {},
        "audit": {
            "created_by": "req-1",
            "updated_by": None,
            "update_reason": None,
            "change_set": None,
            "trace_id": "trace-1",
            "request_id": "req-1",
        },
    }
    base.update(overrides)
    return base


def sample_memory_record_dict(**overrides: Any) -> dict[str, Any]:
    """Shape of an item in `GET /v1/memories` (list) — the lightweight
    `MemoryRecord` projection, distinct from the full `MemoryObject`.
    """
    base: dict[str, Any] = {
        "memory_id": MEMORY_ID,
        "namespace": "demo",
        "owner_id": "user-1",
        "object_type": "Experience",
        "title": "Sample memory",
        "state": "Active",
        "current_version": 1,
        "created_at": "2026-07-08T00:00:00Z",
        "updated_at": None,
        "archived_at": None,
        "deleted_at": None,
    }
    base.update(overrides)
    return base
