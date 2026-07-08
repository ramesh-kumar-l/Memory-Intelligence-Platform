"""`MIPClient` — the SDK entry point. One client per base URL; resources are
thin wrappers sharing a single connection-pooled transport.
"""

from __future__ import annotations

from types import TracebackType

import httpx

from mip_sdk._http import DEFAULT_API_VERSION, DEFAULT_TIMEOUT_SECONDS, Transport
from mip_sdk.resources.admin import AdminResource
from mip_sdk.resources.intelligence import ConsolidateResource, LearnResource
from mip_sdk.resources.memories import MemoriesResource
from mip_sdk.resources.portability import PortabilityResource
from mip_sdk.resources.retrieval import ContextResource, ExplainResource, SearchResource


class MIPClient:
    """Synchronous client for the MIP REST API.

    >>> with MIPClient("http://localhost:8000") as client:
    ...     result = client.search.search(query="onboarding")
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_version: str = DEFAULT_API_VERSION,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        api_key: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._transport = Transport(
            base_url,
            api_version=api_version,
            timeout=timeout,
            api_key=api_key,
            client=http_client,
        )
        self.memories = MemoriesResource(self._transport)
        self.search = SearchResource(self._transport)
        self.explain = ExplainResource(self._transport)
        self.context = ContextResource(self._transport)
        self.admin = AdminResource(self._transport)
        self.consolidate = ConsolidateResource(self._transport)
        self.learn = LearnResource(self._transport)
        self.portability = PortabilityResource(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> MIPClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
