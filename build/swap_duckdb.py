from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import duckdb

try:
    from build.config import resolve_duckdb_path, resolve_prod_duckdb_path
except ImportError:  # pragma: no cover - supports direct script execution
    from config import resolve_duckdb_path, resolve_prod_duckdb_path


@dataclass(frozen=True)
class SwapResult:
    build_path: Path
    prod_path: Path


def ensure_build_database_is_idle(build_path: Path) -> None:
    try:
        connection = duckdb.connect(str(build_path))
    except duckdb.IOException as exc:
        raise RuntimeError(
            "Build DuckDB is busy. Wait for the dbt build job to finish before swapping."
        ) from exc

    try:
        connection.execute("select 1")
    finally:
        connection.close()


def swap_build_to_prod(
    build_path_override: str | Path | None = None,
    prod_path_override: str | Path | None = None,
) -> SwapResult:
    build_path = resolve_duckdb_path(build_path_override)
    prod_path = resolve_prod_duckdb_path(prod_path_override)

    if not build_path.exists():
        raise FileNotFoundError(f"Build DuckDB does not exist: {build_path}")

    ensure_build_database_is_idle(build_path)

    prod_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(build_path, prod_path)

    return SwapResult(build_path=build_path, prod_path=prod_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Atomically promote the build DuckDB file to the production path."
    )
    parser.add_argument(
        "--build-path",
        help="Optional override for the build DuckDB path.",
    )
    parser.add_argument(
        "--prod-path",
        help="Optional override for the production DuckDB path.",
    )
    args = parser.parse_args()

    try:
        result = swap_build_to_prod(args.build_path, args.prod_path)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"swap error: {exc}", file=sys.stderr)
        return 1

    print("DuckDB production swap complete")
    print(f"- build source: {result.build_path}")
    print(f"- production target: {result.prod_path}")
    print("- swap mode: atomic os.replace")
    print("- build lock check: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
