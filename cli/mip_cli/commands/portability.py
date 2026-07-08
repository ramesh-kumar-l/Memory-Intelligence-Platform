"""`mip export|import` — Phase 4 task 4 (ADR-0006)."""

from __future__ import annotations

import json

import click
from mip_sdk.models.requests import ExportRequest

from mip_cli.decorators import handle_api_errors
from mip_cli.formatting import print_json


@click.command("export")
@click.option("--namespace", default=None)
@click.option(
    "--output", "output_path", type=click.Path(dir_okay=False, writable=True), default=None
)
@click.pass_context
@handle_api_errors
def export(ctx: click.Context, namespace: str | None, output_path: str | None) -> None:
    """Export Memory Objects to a portable bundle (backup/migration)."""
    bundle = ctx.obj["client"].portability.export(ExportRequest(namespace=namespace))
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(bundle.model_dump_json(indent=2))
        click.echo(f"wrote {bundle.memory_count} memories to {output_path}")
    else:
        print_json(bundle)


@click.command("import")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
@handle_api_errors
def import_(ctx: click.Context, input_path: str) -> None:
    """Import Memory Objects from a bundle produced by `mip export`."""
    with open(input_path, encoding="utf-8") as handle:
        bundle = json.load(handle)
    report = ctx.obj["client"].portability.import_(bundle)
    print_json(report)
