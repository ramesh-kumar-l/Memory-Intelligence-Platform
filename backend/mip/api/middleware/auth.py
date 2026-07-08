"""API-key authentication + namespace/ownership enforcement (ADR-0007).

Lightweight by design: static config-mapped keys, no accounts/sessions/RBAC —
full identity/auth remains out of MIP's scope, owned by the future Semantic
Control Plane (08-roadmap.md). Disabled by default; MIP stays zero-config and
offline-first until an operator opts in via `MIP_AUTH_ENABLED`.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from mip.core import errors

_BEARER_PREFIX = "Bearer "


@dataclass(frozen=True)
class Principal:
    """The calling API key and the namespaces it may touch. `"*"` means
    unrestricted (used for anonymous access when auth is disabled)."""

    key_id: str
    namespaces: tuple[str, ...]

    def allows(self, namespace: str) -> bool:
        return "*" in self.namespaces or namespace in self.namespaces


_ANONYMOUS = Principal(key_id="anonymous", namespaces=("*",))


def _extract_key(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if header and header.startswith(_BEARER_PREFIX):
        return header[len(_BEARER_PREFIX) :].strip() or None
    return request.headers.get("X-API-Key") or None


async def require_principal(request: Request) -> Principal:
    """FastAPI dependency: resolves and attaches the calling `Principal` to
    `request.state.principal`. A no-op when auth is disabled (the default).
    """
    settings = request.app.state.settings
    if not settings.auth_enabled:
        request.state.principal = _ANONYMOUS
        return _ANONYMOUS
    key = _extract_key(request)
    if key is None:
        raise errors.missing_api_key()
    namespaces = settings.api_keys.get(key)
    if namespaces is None:
        raise errors.invalid_api_key()
    principal = Principal(key_id=key, namespaces=tuple(namespaces))
    request.state.principal = principal
    return principal


def get_principal(request: Request) -> Principal:
    principal: Principal | None = getattr(request.state, "principal", None)
    return principal or _ANONYMOUS


def ensure_namespace_allowed(request: Request, namespace: str) -> None:
    """Ownership/namespace-isolation gate for per-memory operations
    (03-system-architecture.md: 'MIP enforces ownership and namespace
    isolation only')."""
    if not get_principal(request).allows(namespace):
        raise errors.namespace_forbidden(namespace)


def resolve_scoped_namespace(request: Request, namespace: str | None) -> str | None:
    """For list/search-style reads: validates an explicit namespace, or — for
    a key scoped to exactly one namespace — defaults to it. A key scoped to
    several namespaces must name one explicitly; no cross-namespace fan-out.
    """
    principal = get_principal(request)
    if namespace is not None:
        ensure_namespace_allowed(request, namespace)
        return namespace
    if "*" in principal.namespaces:
        return None
    if len(principal.namespaces) == 1:
        return principal.namespaces[0]
    raise errors.namespace_required()
