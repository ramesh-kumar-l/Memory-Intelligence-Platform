"""Search / Explain / BuildContext — the Phase 2 canonical operations
(05-api-design.md). Three small resources in one module; none exceeds a
handful of lines each.
"""

from __future__ import annotations

from typing import Any

from mip_sdk._http import Transport
from mip_sdk.models.requests import ContextRequest, ExplainRequest, SearchRequest
from mip_sdk.models.retrieval import ContextPackage, Explanation, SearchResponse


class SearchResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def search(self, request: SearchRequest | None = None, **kwargs: Any) -> SearchResponse:
        request = request or SearchRequest(**kwargs)
        data = self._transport.request(
            "POST", "/v1/search", json=request.model_dump(mode="json", exclude_none=True)
        )
        return SearchResponse.model_validate(data)


class ExplainResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def explain(self, request: ExplainRequest | None = None, **kwargs: Any) -> Explanation:
        request = request or ExplainRequest(**kwargs)
        data = self._transport.request(
            "POST", "/v1/explain", json=request.model_dump(mode="json", exclude_none=True)
        )
        return Explanation.model_validate(data)


class ContextResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def build(self, request: ContextRequest | None = None, **kwargs: Any) -> ContextPackage:
        request = request or ContextRequest(**kwargs)
        data = self._transport.request(
            "POST", "/v1/context", json=request.model_dump(mode="json", exclude_none=True)
        )
        return ContextPackage.model_validate(data)
