"""Dump the FastAPI-generated OpenAPI schema to JSON for `sdk/typescript`'s
`openapi-typescript` codegen step (ADR-0005). The schema is documentation of
the REST binding, not the contract itself (05-api-design.md) — re-run this
whenever `mip/api/**` changes, then re-run `npm run generate:types` in
`sdk/typescript/`.

Usage (from backend/, with the venv active): python scripts/export_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mip.api.app import create_app

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "sdk" / "typescript" / "openapi.json"


def main() -> None:
    app = create_app()
    schema = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
