"""`handle_api_errors` — shared by `main.py` and every command module. Lives in
its own module so command modules don't have to import from `main` (which in
turn imports the command modules), avoiding a circular import.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from mip_sdk.errors import MIPAPIError, MIPConnectionError

from mip_cli.formatting import print_api_error, print_connection_error


def handle_api_errors[F: Callable[..., Any]](fn: F) -> F:
    """Every command is wrapped so a MEM-* error prints once, cleanly, and
    exits non-zero — instead of a raw traceback.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except MIPConnectionError as exc:
            print_connection_error(exc)
            raise SystemExit(1) from exc
        except MIPAPIError as exc:
            print_api_error(exc)
            raise SystemExit(1) from exc

    return wrapper  # type: ignore[return-value]
