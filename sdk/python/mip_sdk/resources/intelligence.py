"""Consolidate + Learn — Phase 4 tasks 2/3 (ADR-0006). Small enough for one
module; each resource is a handful of lines.
"""

from __future__ import annotations

from mip_sdk._http import Transport
from mip_sdk.models.memory import MemoryObject
from mip_sdk.models.requests import ConsolidateRequest, LearnRequest


class ConsolidateResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def consolidate(self, request: ConsolidateRequest) -> MemoryObject:
        data = self._transport.request(
            "POST", "/v1/consolidate", json=request.model_dump(mode="json", exclude_none=True)
        )
        return MemoryObject.model_validate(data)


class LearnResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def learn(self, request: LearnRequest, *, idempotency_key: str | None = None) -> MemoryObject:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        data = self._transport.request(
            "POST",
            "/v1/learn",
            json=request.model_dump(mode="json", exclude_none=True),
            headers=headers,
        )
        return MemoryObject.model_validate(data)
