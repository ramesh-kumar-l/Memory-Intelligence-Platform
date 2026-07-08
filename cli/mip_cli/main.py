"""CLI entry point: global options and subcommand wiring."""

from __future__ import annotations

import click
from mip_sdk.client import MIPClient

from mip_cli.commands.admin import admin
from mip_cli.commands.intelligence import consolidate, learn
from mip_cli.commands.memories import memories
from mip_cli.commands.portability import export, import_
from mip_cli.commands.retrieval import context, explain, search

DEFAULT_API_URL = "http://localhost:8000"


@click.group()
@click.option(
    "--api-url",
    envvar="MIP_API_URL",
    default=DEFAULT_API_URL,
    show_default=True,
    help="Base URL of the MIP REST API.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output raw JSON.")
@click.pass_context
def cli(ctx: click.Context, api_url: str, as_json: bool) -> None:
    """Memory Intelligence Platform command-line interface."""
    client = MIPClient(api_url)
    ctx.call_on_close(client.close)
    ctx.obj = {"client": client, "json": as_json}


cli.add_command(memories)
cli.add_command(admin)
cli.add_command(search)
cli.add_command(explain)
cli.add_command(context)
cli.add_command(consolidate)
cli.add_command(learn)
cli.add_command(export)
cli.add_command(import_)
