from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import duckdb

from build.bootstrap import bootstrap_duckdb


class BootstrapDuckdbTests(unittest.TestCase):
    def test_bootstrap_creates_expected_schemas_and_metadata_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "bootstrap_test.duckdb"

            result = bootstrap_duckdb(database_path)

            self.assertTrue(result.database_path.samefile(database_path))

            with duckdb.connect(str(database_path)) as connection:
                schemata = {
                    row[0]
                    for row in connection.execute(
                        "select schema_name from information_schema.schemata"
                    ).fetchall()
                }
                self.assertIn("raw", schemata)
                self.assertIn("ops", schemata)

                columns = {
                    row[1]
                    for row in connection.execute(
                        "pragma table_info('ops.source_metadata')"
                    ).fetchall()
                }

            expected_columns = {
                "table_name",
                "source_name",
                "created_at",
                "updated_at",
                "object_key",
                "source_month",
                "source_etag",
                "source_last_modified_at",
                "load_status",
                "batch_id",
                "row_count",
                "last_loaded_at",
                "last_error",
            }
            self.assertTrue(expected_columns.issubset(columns))

    def test_bootstrap_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "bootstrap_test.duckdb"

            first_result = bootstrap_duckdb(database_path)
            second_result = bootstrap_duckdb(database_path)

            self.assertEqual(
                first_result.source_metadata_columns,
                second_result.source_metadata_columns,
            )

            with duckdb.connect(str(database_path)) as connection:
                table_count = connection.execute(
                    """
                    select count(*)
                    from information_schema.tables
                    where table_schema = 'ops'
                      and table_name = 'source_metadata'
                    """
                ).fetchone()[0]

            self.assertEqual(table_count, 1)
