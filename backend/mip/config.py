"""Service settings (pydantic-settings, MIP_* environment variables)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MIPSettings(BaseSettings):
    """Runtime configuration; every value overridable via `MIP_<FIELD>`."""

    model_config = SettingsConfigDict(env_prefix="MIP_")

    db_path: Path = Path("data") / "mip.db"
    schema_version: str = "1.0"
    encoding_version: str = "1.0"
    api_versions: tuple[str, ...] = ("1.0",)
    lock_timeout_seconds: float = 10.0
    list_default_limit: int = 50
    list_max_limit: int = 200

    # Phase 2 — Retrieval & Explainability
    embedding_dimensions: int = 256
    hybrid_keyword_weight: float = 0.5
    search_default_limit: int = 20
    search_max_limit: int = 100
    context_default_limit: int = 10
    context_max_limit: int = 50
    trust_freshness_half_life_days: float = 30.0

    # Production hardening (ADR-0007) — all opt-in; defaults preserve the
    # zero-config, offline-first, single-user posture (Constitution Law 7).
    auth_enabled: bool = False
    api_keys: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 120
    cors_allowed_origins: tuple[str, ...] = ()
