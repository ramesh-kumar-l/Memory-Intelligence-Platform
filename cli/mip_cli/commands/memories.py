"""`mip memories ...` — CreateMemory/GetMemory/UpdateMemory/DeleteMemory/
Archive/Restore/List/versions (Phase 1 canonical operations).
"""

from __future__ import annotations

import click
from mip_sdk.models.memory import (
    MemoryObject,
    MemoryRecord,
    MemoryState,
    ObjectType,
    Semantics,
    VerificationStatus,
    VersionInfo,
)
from mip_sdk.models.requests import CreateMemoryRequest, ProvenanceInput, UpdateMemoryRequest
from mip_sdk.models.retrieval import Page

from mip_cli.decorators import handle_api_errors
from mip_cli.formatting import print_json, print_table


def _memory_row(memory: MemoryObject) -> dict[str, object]:
    return {
        "memory_id": memory.memory_id,
        "title": memory.content.title,
        "state": memory.lifecycle.state.value,
        "version": memory.lifecycle.version,
        "confidence": memory.trust.confidence,
    }


def _record_row(record: MemoryRecord) -> dict[str, object]:
    return {
        "memory_id": record.memory_id,
        "title": record.title,
        "state": record.state.value,
        "version": record.current_version,
    }


def _print_memory(ctx: click.Context, memory: MemoryObject) -> None:
    if ctx.obj["json"]:
        print_json(memory)
    else:
        print_table([_memory_row(memory)], ["memory_id", "title", "state", "version", "confidence"])


@click.group()
def memories() -> None:
    """Manage Memory Objects."""


@memories.command("create")
@click.option("--namespace", required=True)
@click.option("--owner", "owner_id", required=True)
@click.option("--title", required=True)
@click.option("--summary", default="")
@click.option("--description", default="")
@click.option(
    "--object-type", type=click.Choice([t.value for t in ObjectType]), default="Experience"
)
@click.option("--keyword", "keywords", multiple=True, help="Repeatable: --keyword a --keyword b")
@click.option("--concept", "concepts", multiple=True)
@click.option("--confidence", type=float, default=0.5)
@click.option("--freshness", type=float, default=1.0)
@click.option("--source", "provenance_source", required=True, help="Trust provenance source.")
@click.option(
    "--verification-status",
    type=click.Choice([v.value for v in VerificationStatus]),
    default="Unknown",
)
@click.option("--idempotency-key", default=None)
@click.pass_context
@handle_api_errors
def create(
    ctx: click.Context,
    namespace: str,
    owner_id: str,
    title: str,
    summary: str,
    description: str,
    object_type: str,
    keywords: tuple[str, ...],
    concepts: tuple[str, ...],
    confidence: float,
    freshness: float,
    provenance_source: str,
    verification_status: str,
    idempotency_key: str | None,
) -> None:
    """Create a new Memory Object."""
    request = CreateMemoryRequest(
        namespace=namespace,
        owner_id=owner_id,
        object_type=ObjectType(object_type),
        title=title,
        summary=summary,
        description=description,
        semantics=Semantics(keywords=keywords, concepts=concepts),
        confidence=confidence,
        freshness=freshness,
        provenance=ProvenanceInput(source=provenance_source),
        verification_status=VerificationStatus(verification_status),
    )
    memory = ctx.obj["client"].memories.create(request, idempotency_key=idempotency_key)
    _print_memory(ctx, memory)


@memories.command("get")
@click.argument("memory_id")
@click.option("--version", type=int, default=None)
@click.pass_context
@handle_api_errors
def get(ctx: click.Context, memory_id: str, version: int | None) -> None:
    """Fetch a Memory Object (latest active version, or --version N)."""
    memory = ctx.obj["client"].memories.get(memory_id, version=version)
    _print_memory(ctx, memory)


@memories.command("list")
@click.option("--namespace", default=None)
@click.option("--state", type=click.Choice([s.value for s in MemoryState]), default=None)
@click.option("--limit", type=int, default=None)
@click.option("--continuation-token", default=None)
@click.pass_context
@handle_api_errors
def list_command(
    ctx: click.Context,
    namespace: str | None,
    state: str | None,
    limit: int | None,
    continuation_token: str | None,
) -> None:
    """List Memory Objects (filtered read, continuation-token paginated).

    Returns lightweight lifecycle-summary records, not full Memory Objects —
    use `memories get <id>` for the full object.
    """
    page: Page[MemoryRecord] = ctx.obj["client"].memories.list(
        namespace=namespace,
        state=MemoryState(state) if state else None,
        limit=limit,
        continuation_token=continuation_token,
    )
    if ctx.obj["json"]:
        print_json(page)
    else:
        print_table(
            [_record_row(r) for r in page.items], ["memory_id", "title", "state", "version"]
        )
        if not page.complete:
            click.echo(f"\n(more results: --continuation-token {page.continuation_token})")


@memories.command("update")
@click.argument("memory_id")
@click.option("--if-match", "expected_version", type=int, required=True)
@click.option("--title", default=None)
@click.option("--summary", default=None)
@click.option("--description", default=None)
@click.option("--keyword", "keywords", multiple=True)
@click.option("--confidence", type=float, default=None)
@click.option("--update-reason", default=None)
@click.option("--idempotency-key", default=None)
@click.pass_context
@handle_api_errors
def update(
    ctx: click.Context,
    memory_id: str,
    expected_version: int,
    title: str | None,
    summary: str | None,
    description: str | None,
    keywords: tuple[str, ...],
    confidence: float | None,
    update_reason: str | None,
    idempotency_key: str | None,
) -> None:
    """Update a Memory Object, creating version N+1 (requires --if-match)."""
    request = UpdateMemoryRequest(
        title=title,
        summary=summary,
        description=description,
        semantics=Semantics(keywords=keywords) if keywords else None,
        confidence=confidence,
        update_reason=update_reason,
    )
    memory = ctx.obj["client"].memories.update(
        memory_id, request, expected_version=expected_version, idempotency_key=idempotency_key
    )
    _print_memory(ctx, memory)


@memories.command("delete")
@click.argument("memory_id")
@click.pass_context
@handle_api_errors
def delete(ctx: click.Context, memory_id: str) -> None:
    """Delete a Memory Object (idempotent; Deleted is terminal)."""
    result = ctx.obj["client"].memories.delete(memory_id)
    print_json(result)


@memories.command("archive")
@click.argument("memory_id")
@click.pass_context
@handle_api_errors
def archive(ctx: click.Context, memory_id: str) -> None:
    """Archive a Memory Object (idempotent)."""
    _print_memory(ctx, ctx.obj["client"].memories.archive(memory_id))


@memories.command("restore")
@click.argument("memory_id")
@click.pass_context
@handle_api_errors
def restore(ctx: click.Context, memory_id: str) -> None:
    """Restore an archived Memory Object (idempotent)."""
    _print_memory(ctx, ctx.obj["client"].memories.restore(memory_id))


@memories.command("versions")
@click.argument("memory_id")
@click.pass_context
@handle_api_errors
def versions(ctx: click.Context, memory_id: str) -> None:
    """List all immutable historical versions of a Memory Object."""
    result: tuple[VersionInfo, ...] = ctx.obj["client"].memories.list_versions(memory_id)
    if ctx.obj["json"]:
        print_json(list(result))
    else:
        rows = [
            {
                "version": v.version,
                "previous_version": v.previous_version,
                "created_at": v.created_at,
            }
            for v in result
        ]
        print_table(rows, ["version", "previous_version", "created_at"])
