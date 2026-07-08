"""Consolidate + Learn resource tests (Phase 4 tasks 2/3, mock transport)."""

from __future__ import annotations

import json

import httpx

from mip_sdk.models.memory import Semantics
from mip_sdk.models.requests import ConsolidateRequest, LearnRequest
from tests.conftest import MakeClient, envelope
from tests.factories import MEMORY_ID, sample_memory_dict


def test_consolidate_sends_primary_and_duplicates(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/consolidate"
        body = json.loads(request.content)
        assert body == {"primary_memory_id": MEMORY_ID, "duplicate_memory_ids": ["dup-1"]}
        memory = sample_memory_dict()
        memory["lifecycle"] = {**memory["lifecycle"], "consolidation_count": 1}
        return httpx.Response(200, json=envelope(memory))

    client = make_client(handler)
    result = client.consolidate.consolidate(
        ConsolidateRequest(primary_memory_id=MEMORY_ID, duplicate_memory_ids=("dup-1",))
    )
    assert result.lifecycle.consolidation_count == 1


def test_learn_sends_derived_semantics_and_idempotency_key(make_client: MakeClient) -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        body = json.loads(request.content)
        assert body["memory_id"] == MEMORY_ID
        assert body["derived"]["concepts"] == ["replication"]
        return httpx.Response(200, json=envelope(sample_memory_dict()))

    client = make_client(handler)
    client.learn.learn(
        LearnRequest(
            memory_id=MEMORY_ID,
            derived=Semantics(concepts=("replication",)),
            reason="pattern observed",
        ),
        idempotency_key="learn-key-1",
    )
    assert seen_headers["idempotency-key"] == "learn-key-1"
