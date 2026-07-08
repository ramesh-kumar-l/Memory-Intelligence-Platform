"""Runnable Python SDK quickstart.

Prereqs: a running MIP backend (see backend/README.md), and `mip-sdk` installed
(`pip install -e sdk/python` from the repo root).

Usage: python examples/python/quickstart.py [base_url]
"""

from __future__ import annotations

import sys

from mip_sdk import ConcurrencyError, MIPClient
from mip_sdk.models.memory import Semantics
from mip_sdk.models.requests import CreateMemoryRequest, ProvenanceInput, UpdateMemoryRequest


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    with MIPClient(base_url) as client:
        health = client.admin.health()
        print(f"backend status: {health['status']}")

        memory = client.memories.create(
            CreateMemoryRequest(
                namespace="demo",
                owner_id="user-1",
                title="Q3 onboarding notes",
                summary="Key steps for new hires.",
                semantics=Semantics(keywords=("onboarding", "notes")),
                provenance=ProvenanceInput(source="quickstart-example"),
            )
        )
        print(f"created {memory.memory_id} (version {memory.lifecycle.version})")

        results = client.search.search(query="onboarding", mode="hybrid")
        print(f"search found {len(results.items)} result(s)")
        for item in results.items:
            print(f"  {item.memory_id} score={item.score:.4f}")

        explanation = client.explain.explain(memory_id=memory.memory_id, query="onboarding")
        print(f"confidence={explanation.confidence:.2f} freshness={explanation.freshness:.2f}")

        updated = client.memories.update(
            memory.memory_id,
            UpdateMemoryRequest(title="Q3 onboarding notes (revised)"),
            expected_version=1,
        )
        print(f"updated to version {updated.lifecycle.version}: {updated.content.title!r}")

        try:
            client.memories.update(
                memory.memory_id,
                UpdateMemoryRequest(title="stale update"),
                expected_version=1,
            )
        except ConcurrencyError as exc:
            print(f"expected conflict: {exc.code} {exc.details}")

        archived = client.memories.archive(memory.memory_id)
        print(f"archived (state={archived.lifecycle.state.value})")
        restored = client.memories.restore(memory.memory_id)
        print(f"restored (state={restored.lifecycle.state.value})")

        # Delete is only legal from Active (INV-STATE-002) — restore first.
        client.memories.delete(memory.memory_id)
        print("deleted the demo memory")


if __name__ == "__main__":
    main()
