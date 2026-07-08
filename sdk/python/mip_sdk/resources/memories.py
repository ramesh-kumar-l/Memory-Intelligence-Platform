"""CreateMemory/GetMemory/UpdateMemory/DeleteMemory/Archive/Restore/List —
the Phase 1 canonical operations (05-api-design.md).
"""

from __future__ import annotations

from typing import Any

from mip_sdk._http import Transport
from mip_sdk.models.memory import MemoryObject, MemoryRecord, MemoryState, VersionInfo
from mip_sdk.models.requests import CreateMemoryRequest, UpdateMemoryRequest
from mip_sdk.models.retrieval import Page


class MemoriesResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def create(
        self, request: CreateMemoryRequest, *, idempotency_key: str | None = None
    ) -> MemoryObject:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        data = self._transport.request(
            "POST",
            "/v1/memories",
            json=request.model_dump(mode="json", exclude_none=True),
            headers=headers,
        )
        return MemoryObject.model_validate(data)

    def get(self, memory_id: str, *, version: int | None = None) -> MemoryObject:
        params = {"version": version} if version is not None else None
        data = self._transport.request("GET", f"/v1/memories/{memory_id}", params=params)
        return MemoryObject.model_validate(data)

    def list_versions(self, memory_id: str) -> tuple[VersionInfo, ...]:
        """Version history (lightweight `VersionInfo` rows, not full Memory
        Objects — fetch a specific version via `.get(memory_id, version=N)`.
        """
        data = self._transport.request("GET", f"/v1/memories/{memory_id}/versions")
        return tuple(VersionInfo.model_validate(v) for v in data["versions"])

    def list(
        self,
        *,
        namespace: str | None = None,
        state: MemoryState | None = None,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> Page[MemoryRecord]:
        """Filtered read of lifecycle-summary records (not full Memory
        Objects — this is a projection listing, not Search; storage/interfaces.py
        `MemoryRecord`). Fetch a specific memory_id via `.get()` for the full object.
        """
        params: dict[str, Any] = {
            "namespace": namespace,
            "state": state.value if state else None,
            "limit": limit,
            "continuation_token": continuation_token,
        }
        data = self._transport.request(
            "GET", "/v1/memories", params={k: v for k, v in params.items() if v is not None}
        )
        return Page[MemoryRecord](
            items=tuple(MemoryRecord.model_validate(item) for item in data["items"]),
            complete=data["complete"],
            continuation_token=data["continuation_token"],
        )

    def update(
        self,
        memory_id: str,
        request: UpdateMemoryRequest,
        *,
        expected_version: int,
        idempotency_key: str | None = None,
    ) -> MemoryObject:
        headers = {"If-Match": str(expected_version)}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        data = self._transport.request(
            "PATCH",
            f"/v1/memories/{memory_id}",
            json=request.model_dump(mode="json", exclude_none=True),
            headers=headers,
        )
        return MemoryObject.model_validate(data)

    def delete(self, memory_id: str) -> dict[str, Any]:
        result: dict[str, Any] = self._transport.request("DELETE", f"/v1/memories/{memory_id}")
        return result

    def archive(self, memory_id: str) -> MemoryObject:
        data = self._transport.request("POST", f"/v1/memories/{memory_id}/archive")
        return MemoryObject.model_validate(data)

    def restore(self, memory_id: str) -> MemoryObject:
        data = self._transport.request("POST", f"/v1/memories/{memory_id}/restore")
        return MemoryObject.model_validate(data)
