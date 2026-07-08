"""`mip consolidate|learn` — Phase 4 tasks 2/3 (ADR-0006)."""

from __future__ import annotations

import json

import click
from mip_sdk.models.memory import Semantics
from mip_sdk.models.requests import ConsolidateRequest, LearnRequest

from mip_cli.commands.memories import _print_memory
from mip_cli.decorators import handle_api_errors


@click.command("consolidate")
@click.option("--primary", "primary_memory_id", required=True, help="Memory to merge into.")
@click.option(
    "--duplicate",
    "duplicate_memory_ids",
    multiple=True,
    required=True,
    help="Repeatable: --duplicate id1 --duplicate id2",
)
@click.pass_context
@handle_api_errors
def consolidate(
    ctx: click.Context, primary_memory_id: str, duplicate_memory_ids: tuple[str, ...]
) -> None:
    """Merge duplicate Memory Objects into --primary (history preserved;
    duplicates are archived, never deleted).
    """
    request = ConsolidateRequest(
        primary_memory_id=primary_memory_id, duplicate_memory_ids=duplicate_memory_ids
    )
    memory = ctx.obj["client"].consolidate.consolidate(request)
    _print_memory(ctx, memory)


@click.command("learn")
@click.argument("memory_id")
@click.option("--concept", "concepts", multiple=True, help="Derived concept to union in.")
@click.option("--keyword", "keywords", multiple=True, help="Derived keyword to union in.")
@click.option(
    "--evidence",
    "evidence_json",
    multiple=True,
    help='New evidence entry as JSON, e.g. \'{"source": "doc-1"}\'. Repeatable.',
)
@click.option("--verifier", default=None, help="Actor recorded against new evidence entries.")
@click.option("--reason", required=True, help="Why this was learned (audit trail).")
@click.option("--idempotency-key", default=None)
@click.pass_context
@handle_api_errors
def learn(
    ctx: click.Context,
    memory_id: str,
    concepts: tuple[str, ...],
    keywords: tuple[str, ...],
    evidence_json: tuple[str, ...],
    verifier: str | None,
    reason: str,
    idempotency_key: str | None,
) -> None:
    """Update derived semantic knowledge and/or mature the trust evidence
    chain (never modifies original evidence — only appends).
    """
    derived = Semantics(concepts=concepts, keywords=keywords) if concepts or keywords else None
    new_evidence = tuple(json.loads(entry) for entry in evidence_json)
    request = LearnRequest(
        memory_id=memory_id,
        derived=derived,
        new_evidence=new_evidence,
        verifier=verifier,
        reason=reason,
    )
    memory = ctx.obj["client"].learn.learn(request, idempotency_key=idempotency_key)
    _print_memory(ctx, memory)
