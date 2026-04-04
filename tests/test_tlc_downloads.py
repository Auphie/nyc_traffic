from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock

from build.download_from_tlc_full import resolve_month_range
from build.download_from_tlc_incremental import format_incremental_download_error
from build.tlc_download_helpers import (
    DownloadFromTlcError,
    build_download_targets,
    build_trip_download_target,
    current_system_month,
    download_target,
    incremental_trip_tables,
    iter_months,
)


class TlcDownloadsTests(unittest.TestCase):
    def test_build_trip_download_target_uses_cloudfront_url_and_data_dir(self) -> None:
        target = build_trip_download_target(
            "yellow_trips",
            datetime.strptime("2025-01", "%Y-%m").date(),
            data_dir="data",
        )

        self.assertEqual(
            target.url,
            "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet",
        )
        self.assertEqual(target.destination_path, Path("data/yellow_tripdata_2025-01.parquet"))

    def test_download_target_skips_existing_file_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = build_trip_download_target(
                "fhv_trips",
                datetime.strptime("2025-02", "%Y-%m").date(),
                data_dir=temp_dir,
            )
            target.destination_path.write_text("existing")

            with mock.patch("build.tlc_download_helpers.urlopen") as mocked_urlopen:
                result = download_target(target, overwrite=False)

            self.assertEqual(result, target.destination_path)
            mocked_urlopen.assert_not_called()

    def test_iter_months_returns_inclusive_month_range(self) -> None:
        month_range = iter_months(date(2025, 1, 1), date(2025, 3, 1))

        self.assertEqual(
            month_range,
            [date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1)],
        )

    def test_iter_months_rejects_reversed_range(self) -> None:
        with self.assertRaises(DownloadFromTlcError):
            iter_months(date(2025, 3, 1), date(2025, 1, 1))

    def test_build_download_targets_creates_all_table_month_combinations(self) -> None:
        targets = build_download_targets(
            ["yellow_trips", "green_trips"],
            [date(2025, 1, 1), date(2025, 2, 1)],
            data_dir="data",
        )

        self.assertEqual(len(targets), 4)

    def test_incremental_trip_tables_excludes_reference_tables(self) -> None:
        self.assertEqual(
            sorted(incremental_trip_tables()),
            ["fhv_trips", "fhvhv_trips", "green_trips", "yellow_trips"],
        )

    def test_current_system_month_is_first_day_of_month(self) -> None:
        current_month = current_system_month()

        self.assertEqual(current_month.day, 1)

    def test_resolve_month_range_prompts_for_missing_values(self) -> None:
        with mock.patch(
            "builtins.input",
            side_effect=["2025-01", "2025-03"],
        ):
            start_month, end_month = resolve_month_range(None, None)

        self.assertEqual(start_month, date(2025, 1, 1))
        self.assertEqual(end_month, date(2025, 3, 1))

    def test_resolve_month_range_keeps_provided_values(self) -> None:
        start_month, end_month = resolve_month_range(date(2025, 1, 1), date(2025, 3, 1))

        self.assertEqual(start_month, date(2025, 1, 1))
        self.assertEqual(end_month, date(2025, 3, 1))

    def test_incremental_error_message_points_to_tlc_homepage(self) -> None:
        message = format_incremental_download_error(
            date(2026, 4, 1),
            DownloadFromTlcError(
                (
                    "Download failed for "
                    "https://example.com/fhv_tripdata_2026-04.parquet with HTTP 403."
                )
            ),
        )

        self.assertIn("requested month: 2026-04", message)
        self.assertIn("Check data availability at:", message)
        self.assertIn("nyc.gov/site/tlc/about/tlc-trip-record-data.page", message)
