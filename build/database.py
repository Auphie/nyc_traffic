from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb

try:
    from build.config import resolve_duckdb_path
except ImportError:  # pragma: no cover - supports direct script execution
    from config import resolve_duckdb_path


@contextmanager
def connect_duckdb(
    path_override: str | Path | None = None,
) -> Iterator[duckdb.DuckDBPyConnection]:
    database_path = resolve_duckdb_path(path_override)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database_path))
    try:
        yield connection
    finally:
        connection.close()
