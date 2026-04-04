from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from build.bootstrap import bootstrap_duckdb
from build.database import connect_duckdb
from build.source_discovery import (
    SOURCE_DEFINITIONS_BY_TABLE,
    SourceDiscoveryError,
    list_source_objects_from_local_data_dir,
    load_source_metadata_records,
    parse_source_object,
    parse_source_objects,
    plan_source_discovery,
)


class SourceDiscoveryTests(unittest.TestCase):
    def test_incremental_trip_object_parsing_extracts_month_and_timestamp_column(self) -> None:
        definition = SOURCE_DEFINITIONS_BY_TABLE["yellow_trips"]

        parsed_object = parse_source_object(
            definition,
            "trip data/yellow_tripdata_2025-02.parquet",
            source_last_modified_at=datetime(2025, 4, 1, 10, 0, tzinfo=timezone.utc),
            source_etag='"etag-1"',
            size_bytes=123,
        )

        self.assertIsNotNone(parsed_object)
        assert parsed_object is not None
        self.assertEqual(parsed_object.table_name, "yellow_trips")
        self.assertEqual(parsed_object.source_month.isoformat(), "2025-02-01")
        self.assertEqual(parsed_object.timestamp_column, "tpep_pickup_datetime")
        self.assertEqual(parsed_object.load_mode, "incremental")
        self.assertEqual(parsed_object.source_etag, "etag-1")

    def test_reference_object_parsing_matches_taxi_zone_shape(self) -> None:
        definition = SOURCE_DEFINITIONS_BY_TABLE["taxi_zone_shape"]

        parsed_object = parse_source_object(
            definition,
            "trip data/taxi_zone_shape.parquet",
            source_last_modified_at=datetime(2025, 4, 1, 10, 0, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(parsed_object)
        assert parsed_object is not None
        self.assertEqual(parsed_object.table_name, "taxi_zone_shape")
        self.assertEqual(parsed_object.load_mode, "replace_on_change")
        self.assertIsNone(parsed_object.source_month)
        self.assertIsNone(parsed_object.timestamp_column)

    def test_parse_source_objects_ignores_unmapped_files(self) -> None:
        listed_objects = [
            {"Key": "trip data/yellow_tripdata_2025-01.parquet", "LastModified": None},
            {"Key": "trip data/not_supported.csv", "LastModified": None},
        ]

        parsed_objects = parse_source_objects(listed_objects)

        self.assertEqual(len(parsed_objects), 1)
        self.assertEqual(parsed_objects[0].table_name, "yellow_trips")

    def test_local_data_listing_reads_downloaded_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            (source_dir / "yellow_tripdata_2025-01.parquet").write_text("sample")
            (source_dir / "ignored.txt").write_text("sample")

            listed_objects = list_source_objects_from_local_data_dir(source_dir)
            parsed_objects = parse_source_objects(listed_objects)

            self.assertEqual(len(parsed_objects), 1)
            self.assertEqual(parsed_objects[0].table_name, "yellow_trips")

    def test_local_data_listing_requires_directory(self) -> None:
        with self.assertRaises(SourceDiscoveryError):
            list_source_objects_from_local_data_dir("missing-data-dir")

    def test_plan_marks_new_sources_without_metadata(self) -> None:
        source_objects = parse_source_objects(
            [
                {
                    "Key": "trip data/fhv_tripdata_2025-01.parquet",
                    "LastModified": "2025-03-30T12:00:00+00:00",
                    "ETag": '"etag-new"',
                    "Size": 100,
                }
            ]
        )

        plan_entries = plan_source_discovery(source_objects, {})

        self.assertEqual(len(plan_entries), 1)
        self.assertEqual(plan_entries[0].disposition, "new")

    def test_plan_marks_unchanged_when_metadata_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "discovery_test.duckdb"
            bootstrap_duckdb(database_path)

            with connect_duckdb(database_path) as connection:
                connection.execute(
                    """
                    insert into ops.source_metadata (
                        table_name,
                        source_name,
                        object_key,
                        source_month,
                        source_etag,
                        source_last_modified_at,
                        load_status
                    )
                    values (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        "yellow_trips",
                        "yellow_tripdata",
                        "trip data/yellow_tripdata_2025-01.parquet",
                        "2025-01-01",
                        "etag-same",
                        datetime(2025, 3, 30, 12, 0),
                        "completed",
                    ],
                )

            source_objects = parse_source_objects(
                [
                    {
                        "Key": "trip data/yellow_tripdata_2025-01.parquet",
                        "LastModified": "2025-03-30T12:00:00",
                        "ETag": '"etag-same"',
                        "Size": 100,
                    }
                ]
            )
            metadata_records = load_source_metadata_records(database_path)

            plan_entries = plan_source_discovery(source_objects, metadata_records)

            self.assertEqual(plan_entries[0].disposition, "unchanged")

    def test_plan_marks_reload_when_object_state_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "discovery_test.duckdb"
            bootstrap_duckdb(database_path)

            with connect_duckdb(database_path) as connection:
                connection.execute(
                    """
                    insert into ops.source_metadata (
                        table_name,
                        source_name,
                        object_key,
                        source_month,
                        source_etag,
                        source_last_modified_at,
                        load_status
                    )
                    values (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        "fhvhv_trips",
                        "fhvhv_tripdata",
                        "trip data/fhvhv_tripdata_2025-01.parquet",
                        "2025-01-01",
                        "etag-old",
                        datetime(2025, 3, 30, 12, 0),
                        "completed",
                    ],
                )

            source_objects = parse_source_objects(
                [
                    {
                        "Key": "trip data/fhvhv_tripdata_2025-01.parquet",
                        "LastModified": "2025-04-01T00:00:00+00:00",
                        "ETag": '"etag-new"',
                        "Size": 200,
                    }
                ]
            )
            metadata_records = load_source_metadata_records(database_path)

            plan_entries = plan_source_discovery(source_objects, metadata_records)

            self.assertEqual(plan_entries[0].disposition, "reload")
