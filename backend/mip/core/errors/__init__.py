"""Structured error hierarchy bound to the append-only MEM-* code registry.

The registry (05-api-design.md) is append-only: codes are never renumbered or
removed. The API layer is the only place these become HTTP responses.

Public surface only — `from mip.core import errors; errors.memory_not_found(...)`
and `from mip.core.errors import ValidationError` both resolve here regardless
of how the implementation is split across `base.py`/`factories.py`.
"""

from __future__ import annotations

from mip.core.errors.base import (
    DOCUMENTATION_URL_BASE,
    ConcurrencyError,
    ErrorCategory,
    IdentityError,
    LifecycleError,
    MIPError,
    SecurityError,
    StorageError,
    ValidationError,
)
from mip.core.errors.factories import (
    consolidation_target_not_active,
    duplicate_memory_id,
    idempotency_key_reuse,
    illegal_transition,
    import_bundle_invalid,
    internal_failure,
    invalid_api_key,
    invalid_consolidation_request,
    invalid_request,
    memory_deleted,
    memory_not_found,
    missing_api_key,
    missing_precondition,
    missing_semantic_element,
    namespace_forbidden,
    namespace_required,
    operation_not_allowed,
    rate_limit_exceeded,
    storage_failure,
    transition_in_progress,
    unresolved_relationship_target,
    unsupported_api_version,
    unsupported_search_mode,
    validation_failed,
    version_conflict,
    version_not_found,
)

__all__ = [
    "DOCUMENTATION_URL_BASE",
    "ConcurrencyError",
    "ErrorCategory",
    "IdentityError",
    "LifecycleError",
    "MIPError",
    "SecurityError",
    "StorageError",
    "ValidationError",
    "consolidation_target_not_active",
    "duplicate_memory_id",
    "idempotency_key_reuse",
    "illegal_transition",
    "import_bundle_invalid",
    "internal_failure",
    "invalid_api_key",
    "invalid_consolidation_request",
    "invalid_request",
    "memory_deleted",
    "memory_not_found",
    "missing_api_key",
    "missing_precondition",
    "missing_semantic_element",
    "namespace_forbidden",
    "namespace_required",
    "operation_not_allowed",
    "rate_limit_exceeded",
    "storage_failure",
    "transition_in_progress",
    "unresolved_relationship_target",
    "unsupported_api_version",
    "unsupported_search_mode",
    "validation_failed",
    "version_conflict",
    "version_not_found",
]
