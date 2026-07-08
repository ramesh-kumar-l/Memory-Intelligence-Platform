"""`mip search|explain|context` — the Phase 2 canonical operations."""

from __future__ import annotations

import click

from mip_cli.decorators import handle_api_errors
from mip_cli.formatting import print_json, print_table


@click.command("search")
@click.argument("query")
@click.option("--mode", type=click.Choice(["keyword", "semantic", "hybrid"]), default="hybrid")
@click.option("--namespace", default=None)
@click.option("--limit", type=int, default=None)
@click.option("--continuation-token", default=None)
@click.pass_context
@handle_api_errors
def search(
    ctx: click.Context,
    query: str,
    mode: str,
    namespace: str | None,
    limit: int | None,
    continuation_token: str | None,
) -> None:
    """Search Memory Objects (keyword/semantic/hybrid); every result carries
    its own score breakdown — explainable by construction.
    """
    response = ctx.obj["client"].search.search(
        query=query,
        mode=mode,
        namespace=namespace,
        limit=limit,
        continuation_token=continuation_token,
    )
    if ctx.obj["json"]:
        print_json(response)
        return
    rows = [
        {
            "memory_id": item.memory_id,
            "score": round(item.score, 4),
            "keyword": item.explanation.keyword_score,
            "semantic": item.explanation.semantic_score,
        }
        for item in response.items
    ]
    print_table(rows, ["memory_id", "score", "keyword", "semantic"])
    if not response.complete:
        click.echo(f"\n(more results: --continuation-token {response.continuation_token})")


@click.command("explain")
@click.argument("memory_id")
@click.option("--query", default=None, help="Include a ranking explanation for this query.")
@click.option("--mode", type=click.Choice(["keyword", "semantic", "hybrid"]), default="hybrid")
@click.pass_context
@handle_api_errors
def explain(ctx: click.Context, memory_id: str, query: str | None, mode: str) -> None:
    """Explain a Memory Object: evidence, confidence, freshness, provenance,
    and — with --query — why it would or wouldn't rank for that query.
    """
    explanation = ctx.obj["client"].explain.explain(memory_id=memory_id, query=query, mode=mode)
    print_json(explanation)


@click.command("context")
@click.argument("query")
@click.option("--namespace", default=None)
@click.option("--mode", type=click.Choice(["keyword", "semantic", "hybrid"]), default="hybrid")
@click.option("--limit", type=int, default=None)
@click.option("--continuation-token", default=None)
@click.pass_context
@handle_api_errors
def context(
    ctx: click.Context,
    query: str,
    namespace: str | None,
    mode: str,
    limit: int | None,
    continuation_token: str | None,
) -> None:
    """Build a task-specific Context Package (relevance blended with each
    memory's own importance score).
    """
    package = ctx.obj["client"].context.build(
        query=query,
        namespace=namespace,
        mode=mode,
        limit=limit,
        continuation_token=continuation_token,
    )
    if ctx.obj["json"]:
        print_json(package)
        return
    rows = [
        {
            "memory_id": item.memory.memory_id,
            "title": item.memory.content.title,
            "relevance": round(item.relevance_score, 4),
            "importance": round(item.importance_score, 4),
            "blended": round(item.blended_score, 4),
        }
        for item in package.items
    ]
    print_table(rows, ["memory_id", "title", "relevance", "importance", "blended"])
