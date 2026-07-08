"""`mip admin ...` — health, version, and projection rebuild."""

from __future__ import annotations

import click

from mip_cli.decorators import handle_api_errors
from mip_cli.formatting import print_json


@click.group()
def admin() -> None:
    """Operational commands: health, version, rebuild."""


@admin.command("health")
@click.pass_context
@handle_api_errors
def health(ctx: click.Context) -> None:
    """Check API/storage liveness."""
    print_json(ctx.obj["client"].admin.health())


@admin.command("version")
@click.pass_context
@handle_api_errors
def version(ctx: click.Context) -> None:
    """Show service version and supported API versions."""
    print_json(ctx.obj["client"].admin.version())


@admin.command("rebuild")
@click.pass_context
@handle_api_errors
def rebuild(ctx: click.Context) -> None:
    """Rebuild all projections (memories, search index, vector index) from
    the event log — proves replayability.
    """
    print_json(ctx.obj["client"].admin.rebuild_projections())
