from __future__ import annotations

import argparse
import sys

try:
    from build.tlc_download_helpers import (
        DEFAULT_DATA_DIR,
        DownloadFromTlcError,
        build_download_targets,
        current_system_month,
        download_targets,
        incremental_trip_tables,
        parse_month,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from tlc_download_helpers import (
        DEFAULT_DATA_DIR,
        DownloadFromTlcError,
        build_download_targets,
        current_system_month,
        download_targets,
        incremental_trip_tables,
        parse_month,
    )


TLC_TRIP_RECORD_PAGE_URL = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"


def format_incremental_download_error(
    source_month: object,
    error: DownloadFromTlcError,
) -> str:
    return (
        f"download error: {error}\n"
        f"requested month: {source_month:%Y-%m}\n"
        "The requested month may not be published yet because TLC trip data is typically "
        "released with a delay.\n"
        f"Check data availability at: {TLC_TRIP_RECORD_PAGE_URL}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download the current system month of TLC parquet files "
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
        "--month",
        type=parse_month,
        help="Optional override for the target month. Defaults to the current system month.",
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
    source_month = args.month or current_system_month()

    try:
        targets = build_download_targets(table_names, [source_month], args.data_dir)
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
        print(format_incremental_download_error(source_month, exc), file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
