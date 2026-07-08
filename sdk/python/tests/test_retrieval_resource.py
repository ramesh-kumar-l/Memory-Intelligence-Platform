from __future__ import annotations

import json

import httpx

from tests.conftest import MakeClient, envelope
from tests.factories import MEMORY_ID, sample_memory_dict


def test_search_returns_typed_response(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/search"
        body = json.loads(request.content)
        assert body["query"] == "onboarding"
        assert body["mode"] == "hybrid"
        return httpx.Response(
            200,
            json=envelope(
                {
                    "query": "onboarding",
                    "mode": "hybrid",
                    "items": [
                        {
                            "memory_id": MEMORY_ID,
                            "score": 0.87,
                            "explanation": {
                                "mode": "hybrid",
                                "keyword_score": 0.9,
                                "semantic_score": 0.8,
                            },
                        }
                    ],
                    "complete": True,
                    "continuation_token": None,
                }
            ),
        )

    client = make_client(handler)
    response = client.search.search(query="onboarding")
    assert response.mode == "hybrid"
    assert len(response.items) == 1
    assert response.items[0].score == 0.87
    assert response.items[0].explanation.keyword_score == 0.9


def test_search_unsupported_mode_raises_validation_error(make_client: MakeClient) -> None:
    from mip_sdk.errors import ValidationError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "MEM-1007",
                    "category": "Validation",
                    "message": "Requested search mode is not supported",
                    "details": {
                        "requested": "bogus",
                        "supported": ["keyword", "semantic", "hybrid"],
                    },
                    "recoverable": False,
                    "documentation_url": "https://example.invalid/errors#MEM-1007",
                },
                "request_id": "req-err",
            },
        )

    client = make_client(handler)
    try:
        client.search.search(query="x", mode="bogus")
        raise AssertionError("expected ValidationError")
    except ValidationError as exc:
        assert exc.code == "MEM-1007"
        assert exc.details["requested"] == "bogus"


def test_explain_returns_typed_explanation(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/explain"
        return httpx.Response(
            200,
            json=envelope(
                {
                    "memory_id": MEMORY_ID,
                    "confidence": 0.8,
                    "freshness": 0.95,
                    "verification_status": "Unknown",
                    "source_count": 1,
                    "provenance": {
                        "source": "test-suite",
                        "method": None,
                        "location": None,
                        "captured_at": None,
                        "agent": None,
                    },
                    "evidence": [],
                    "ranking": {
                        "mode": "hybrid",
                        "score": 0.87,
                        "keyword_score": 0.9,
                        "semantic_score": 0.8,
                        "matched": True,
                    },
                }
            ),
        )

    client = make_client(handler)
    explanation = client.explain.explain(memory_id=MEMORY_ID, query="onboarding")
    assert explanation.confidence == 0.8
    assert explanation.ranking is not None
    assert explanation.ranking.matched is True


def test_build_context_returns_typed_package(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/context"
        return httpx.Response(
            200,
            json=envelope(
                {
                    "query": "onboarding",
                    "namespace": "demo",
                    "mode": "hybrid",
                    "items": [
                        {
                            "memory": sample_memory_dict(),
                            "relevance_score": 0.87,
                            "importance_score": 0.5,
                            "blended_score": 0.76,
                        }
                    ],
                    "complete": True,
                    "total_candidates": 1,
                    "continuation_token": None,
                }
            ),
        )

    client = make_client(handler)
    package = client.context.build(query="onboarding", namespace="demo")
    assert package.total_candidates == 1
    assert package.items[0].memory.memory_id == MEMORY_ID
    assert package.items[0].blended_score == 0.76
