"""Official Python SDK for the Memory Intelligence Platform (MIP) REST API.

Thin typed client over `/v1` (05-api-design.md, FR-API-001) — no engine or
storage logic lives here; every call is a plain HTTP request.
"""

from __future__ import annotations

from mip_sdk.client import MIPClient
from mip_sdk.errors import (
    ConcurrencyError,
    IdentityError,
    LifecycleError,
    MIPAPIError,
    MIPConnectionError,
    SecurityError,
    StorageError,
    SyncError,
    TrustError,
    ValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "ConcurrencyError",
    "IdentityError",
    "LifecycleError",
    "MIPAPIError",
    "MIPClient",
    "MIPConnectionError",
    "SecurityError",
    "StorageError",
    "SyncError",
    "TrustError",
    "ValidationError",
    "__version__",
]
