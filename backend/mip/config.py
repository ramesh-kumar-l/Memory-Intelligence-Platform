"""Service settings (pydantic-settings, MIP_* environment variables)."""

from __future__ import annotations

from pathlib import Path

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
