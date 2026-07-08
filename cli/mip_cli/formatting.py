"""Output formatting: JSON mode (machine-readable) or a plain aligned table
(human-readable). No table-drawing dependency — the format is deliberately
simple (boring dependencies, 21-coding-standards.md).
"""

from __future__ import annotations

import json
from typing import Any

import click
from mip_sdk.errors import MIPAPIError, MIPConnectionError
from pydantic import BaseModel


def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list | tuple):
        return [to_jsonable(item) for item in value]
    return value


def print_json(value: Any) -> None:
    click.echo(json.dumps(to_jsonable(value), indent=2, default=str))


def print_table(rows: list[dict[str, Any]], columns: list[str]) -> None:
    if not rows:
        click.echo("(no results)")
        return
    widths = {
        col: max(len(col), max(len(str(row.get(col, ""))) for row in rows)) for col in columns
    }
    header = "  ".join(col.upper().ljust(widths[col]) for col in columns)
    click.echo(header)
    click.echo("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        click.echo("  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))


def print_api_error(exc: MIPAPIError) -> None:
    click.secho(f"error: {exc.code} ({exc.category})", fg="red", err=True)
    click.echo(f"  {exc.message}", err=True)
    if exc.details:
        click.echo(f"  details: {json.dumps(exc.details)}", err=True)
    if exc.documentation_url:
        click.echo(f"  see: {exc.documentation_url}", err=True)


def print_connection_error(exc: MIPConnectionError) -> None:
    click.secho(f"connection error: {exc}", fg="red", err=True)
