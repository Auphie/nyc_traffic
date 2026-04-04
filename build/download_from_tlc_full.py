from __future__ import annotations

import argparse
import sys

try:
    from build.tlc_download_helpers import (
        DEFAULT_DATA_DIR,
        DownloadFromTlcError,
        build_download_targets,
        download_targets,
        incremental_trip_tables,
        iter_months,
        parse_month,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from tlc_download_helpers import (
        DEFAULT_DATA_DIR,
        DownloadFromTlcError,
        build_download_targets,
        download_targets,
        incremental_trip_tables,
        iter_months,
        parse_month,
    )


def prompt_for_month(prompt_text: str) -> object:
    while True:
        raw_value = input(prompt_text).strip()
        try:
            return parse_month(raw_value)
        except ValueError:
            print("Invalid month format. Please use YYYY-MM.", file=sys.stderr)


def resolve_month_range(
    start_month: object | None,
    end_month: object | None,
) -> tuple[object, object]:
    resolved_start = start_month or prompt_for_month("Start month (YYYY-MM): ")
    resolved_end = end_month or prompt_for_month("End month (YYYY-MM): ")
    return resolved_start, resolved_end


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download a full TLC parquet backfill for a month range "
            "into the local data directory."
        )
    )
    parser.add_argument(
        "--table",
        action="append",
        choices=sorted(incremental_trip_tables()),
        help="One or more trip tables to download. Defaults to all trip tables.",
    )
    parser.add_argument(
        "--start-month",
        type=parse_month,
        help="Inclusive start month in YYYY-MM format.",
    )
    parser.add_argument(
        "--end-month",
        type=parse_month,
        help="Inclusive end month in YYYY-MM format.",
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="Destination directory for downloaded parquet files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing local file if it already exists.",
    )
    args = parser.parse_args()

    table_names = args.table or incremental_trip_tables()

    try:
        start_month, end_month = resolve_month_range(args.start_month, args.end_month)
        source_months = iter_months(start_month, end_month)
        targets = build_download_targets(table_names, source_months, args.data_dir)
        for target, destination_path in zip(
            targets,
            download_targets(targets, overwrite=args.overwrite),
            strict=True,
        ):
            print(
                f"downloaded {target.table_name} {target.source_month:%Y-%m} -> "
                f"{destination_path}"
            )
    except DownloadFromTlcError as exc:
        print(f"download error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
