from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import duckdb

from build.swap_duckdb import ensure_build_database_is_idle, swap_build_to_prod


class SwapDuckdbTests(unittest.TestCase):
    def test_swap_moves_build_database_to_prod_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            build_path = Path(temp_dir) / "build.duckdb"
            prod_path = Path(temp_dir) / "prod.duckdb"

            with duckdb.connect(str(build_path)) as connection:
                connection.execute("create table marker as select 42 as value")

            result = swap_build_to_prod(build_path, prod_path)

            self.assertEqual(result.build_path, build_path)
            self.assertEqual(result.prod_path, prod_path)
            self.assertFalse(build_path.exists())
            self.assertTrue(prod_path.exists())

            with duckdb.connect(str(prod_path), read_only=True) as connection:
                stored_value = connection.execute(
                    "select value from marker"
                ).fetchone()[0]

            self.assertEqual(stored_value, 42)

    def test_swap_raises_when_build_database_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            build_path = Path(temp_dir) / "missing_build.duckdb"
            prod_path = Path(temp_dir) / "prod.duckdb"

            with self.assertRaises(FileNotFoundError):
                swap_build_to_prod(build_path, prod_path)

    def test_idle_check_detects_external_build_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            build_path = Path(temp_dir) / "locked_build.duckdb"

            with duckdb.connect(str(build_path)) as connection:
                connection.execute("create table marker as select 1 as value")

            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    (
                        "import duckdb, time; "
                        f"con = duckdb.connect(r'{build_path}'); "
                        "con.execute('select 1'); "
                        "time.sleep(10)"
                    ),
                ]
            )

            try:
                time.sleep(1)
                with self.assertRaises(RuntimeError):
                    ensure_build_database_is_idle(build_path)
            finally:
                process.terminate()
                process.wait()
