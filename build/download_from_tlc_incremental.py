from __future__ import annotations

import argparse
import sys
from datetime import date

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


def run_incremental_download(
    table_names: list[str] | None = None,
    *,
    source_month: date | None = None,
    data_dir: str = DEFAULT_DATA_DIR,
    overwrite: bool = False,
) -> dict[str, object]:
    selected_table_names = table_names or incremental_trip_tables()
    selected_source_month = source_month or current_system_month()

    try:
        targets = build_download_targets(
            selected_table_names,
            [selected_source_month],
            data_dir,
        )
        downloaded_paths: list[str] = []
        for target, destination_path in zip(
            targets,
            download_targets(targets, overwrite=overwrite),
            strict=True,
        ):
            downloaded_paths.append(str(destination_path))
            print(
                f"downloaded {target.table_name} {target.source_month:%Y-%m} -> "
                f"{destination_path}"
            )
    except DownloadFromTlcError as exc:
        message = format_incremental_download_error(selected_source_month, exc)
        return {
            "status": "fallback",
            "source_month": selected_source_month.strftime("%Y-%m"),
            "message": message,
        }

    return {
        "status": "success",
        "source_month": selected_source_month.strftime("%Y-%m"),
        "message": (
            f"Downloaded {len(downloaded_paths)} file(s) for "
            f"{selected_source_month:%Y-%m}."
        ),
        "downloaded_paths": downloaded_paths,
    }


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

    result = run_incremental_download(
        args.table,
        source_month=args.month,
        data_dir=args.data_dir,
        overwrite=args.overwrite,
    )
    if result["status"] != "success":
        print(result["message"], file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
