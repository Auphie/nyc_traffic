from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from build.config import resolve_duckdb_path
    from build.database import connect_duckdb
except ImportError:  # pragma: no cover - supports direct script execution
    from config import resolve_duckdb_path
    from database import connect_duckdb


SCHEMA_STATEMENTS = (
    "create schema if not exists staging;",
    "create schema if not exists analytics;",
    "create schema if not exists ops;",
)

SOURCE_METADATA_CREATE_SQL = """
create table if not exists ops.source_metadata (
    table_name text not null,
    source_name text not null,
    created_at timestamp not null default current_timestamp,
    updated_at timestamp not null default current_timestamp
);
"""

SOURCE_METADATA_ALTER_STATEMENTS = (
    "alter table ops.source_metadata add column if not exists object_key text;",
    "alter table ops.source_metadata add column if not exists source_month date;",
    "alter table ops.source_metadata add column if not exists source_etag text;",
    (
        "alter table ops.source_metadata "
        "add column if not exists source_last_modified_at timestamp;"
    ),
    "alter table ops.source_metadata add column if not exists load_status text;",
    "alter table ops.source_metadata add column if not exists batch_id text;",
    "alter table ops.source_metadata add column if not exists row_count bigint;",
    "alter table ops.source_metadata add column if not exists last_loaded_at timestamp;",
    "alter table ops.source_metadata add column if not exists last_error text;",
)


@dataclass(frozen=True)
class BootstrapResult:
    database_path: Path
    schemas: tuple[str, ...]
    source_metadata_columns: tuple[str, ...]


def bootstrap_duckdb(path_override: str | Path | None = None) -> BootstrapResult:
    database_path = resolve_duckdb_path(path_override)

    with connect_duckdb(database_path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)

        connection.execute(SOURCE_METADATA_CREATE_SQL)
        for statement in SOURCE_METADATA_ALTER_STATEMENTS:
            connection.execute(statement)

        columns = tuple(
            row[1]
            for row in connection.execute(
                "pragma table_info('ops.source_metadata')"
            ).fetchall()
        )

    return BootstrapResult(
        database_path=database_path,
        schemas=("staging", "analytics", "ops"),
        source_metadata_columns=columns,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the DuckDB operational schemas and metadata tables."
    )
    parser.add_argument(
        "--duckdb-path",
        help="Optional override for the DuckDB database path.",
    )
    args = parser.parse_args()

    result = bootstrap_duckdb(args.duckdb_path)

    print("DuckDB bootstrap complete")
    print(f"- database: {result.database_path}")
    print(f"- schemas: {', '.join(result.schemas)}")
    print("- source_metadata columns: " + ", ".join(result.source_metadata_columns))

    return 0


if __name__ == "__main__":
    sys.exit(main())
