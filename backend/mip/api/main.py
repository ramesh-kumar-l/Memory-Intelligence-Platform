"""ASGI entry point: `uvicorn mip.api.main:app`."""

from __future__ import annotations

from mip.api.app import create_app

app = create_app()
