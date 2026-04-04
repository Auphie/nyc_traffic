from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

try:
    from build.config import load_environment_settings, load_project_paths
except ImportError:  # pragma: no cover - supports direct script execution
    from config import load_environment_settings, load_project_paths


def _status_line(label: str, ok: bool, detail: str) -> str:
    prefix = "[ok]" if ok else "[missing]"
    return f"{prefix} {label}: {detail}"


def _path_exists(path: Path) -> tuple[bool, str]:
    return path.exists(), str(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the local NYC TLC Trip scaffold environment."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when expected setup items are missing.",
    )
    args = parser.parse_args()

    project_paths = load_project_paths()
    env_settings = load_environment_settings()

    checks = [
        ("Repo root", True, str(project_paths.root_dir)),
        ("Parent directory", True, str(project_paths.parent_dir)),
        ("DuckDB path", *_path_exists(project_paths.duckdb_path)),
        ("dbt profile", *_path_exists(project_paths.profiles_path)),
        ("Logs directory", *_path_exists(project_paths.logs_dir)),
        (
            "DBT_DUCKDB_PATH",
            "DBT_DUCKDB_PATH" in os.environ,
            env_settings.dbt_duckdb_path,
        ),
        (
            "DBT_PROFILES_DIR",
            "DBT_PROFILES_DIR" in os.environ,
            env_settings.dbt_profiles_dir,
        ),
    ]

    print("NYC TLC Trip environment check")
    print("")
    for label, ok, detail in checks:
        print(_status_line(label, ok, detail))

    missing = [label for label, ok, _ in checks if not ok]
    if missing:
        print("")
        print("Next steps:")
        print("- Copy profiles.example.yml to ../profiles.yml")
        print("- Export DBT_DUCKDB_PATH and DBT_PROFILES_DIR")
        print("- Create ../logs/ if it does not exist")

    return 1 if args.strict and missing else 0


if __name__ == "__main__":
    sys.exit(main())
