from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from build.config import (
        load_environment_settings,
        load_project_paths,
        resolve_duckdb_path,
        resolve_profiles_dir,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from config import (
        load_environment_settings,
        load_project_paths,
        resolve_duckdb_path,
        resolve_profiles_dir,
    )


def _status_line(label: str, ok: bool, detail: str) -> str:
    prefix = "[ok]" if ok else "[missing]"
    return f"{prefix} {label}: {detail}"


def _path_exists(path: Path) -> tuple[bool, str]:
    return path.exists(), str(path)


def _optional_path_status(path: Path, empty_detail: str) -> tuple[bool, str]:
    if path.exists():
        return True, str(path)

    return True, f"{path} ({empty_detail})"


def _env_path_status(env_name: str, resolved_path: Path, raw_value: str) -> tuple[bool, str]:
    if env_name in os.environ:
        return True, f"{raw_value} (from environment)"

    if resolved_path.exists():
        return True, f"{raw_value} (default)"

    return False, raw_value


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
    resolved_duckdb_path = resolve_duckdb_path()
    resolved_profiles_dir = resolve_profiles_dir()

    checks = [
        ("Repo root", True, str(project_paths.root_dir)),
        ("Parent directory", True, str(project_paths.parent_dir)),
        ("Build DuckDB path", *_path_exists(project_paths.build_duckdb_path)),
        (
            "Production DuckDB path",
            *_optional_path_status(
                project_paths.prod_duckdb_path,
                "created on first swap",
            ),
        ),
        ("dbt profile", *_path_exists(project_paths.profiles_path)),
        ("Logs directory", *_path_exists(project_paths.logs_dir)),
        (
            "DBT_DUCKDB_PATH",
            *_env_path_status(
                "DBT_DUCKDB_PATH",
                resolved_duckdb_path,
                env_settings.dbt_duckdb_path,
            ),
        ),
        (
            "DBT_PROFILES_DIR",
            *_env_path_status(
                "DBT_PROFILES_DIR",
                resolved_profiles_dir,
                env_settings.dbt_profiles_dir,
            ),
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
        print("- Create .env_duck/profiles.yml if it does not exist")
        print("- Export DBT_DUCKDB_PATH and DBT_PROFILES_DIR only if you need overrides")
        print("- Create ../logs/ if it does not exist")

    return 1 if args.strict and missing else 0


if __name__ == "__main__":
    sys.exit(main())
