from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT_DIR.parent


@dataclass(frozen=True)
class ProjectPaths:
    root_dir: Path = ROOT_DIR
    parent_dir: Path = PARENT_DIR
    duckdb_path: Path = PARENT_DIR / "nyc_tlc.duckdb"
    profiles_path: Path = PARENT_DIR / "profiles.yml"
    logs_dir: Path = PARENT_DIR / "logs"


@dataclass(frozen=True)
class EnvironmentSettings:
    dbt_duckdb_path: str = os.getenv("DBT_DUCKDB_PATH", "../nyc_tlc.duckdb")
    dbt_profiles_dir: str = os.getenv("DBT_PROFILES_DIR", "..")


def load_project_paths() -> ProjectPaths:
    return ProjectPaths()


def load_environment_settings() -> EnvironmentSettings:
    return EnvironmentSettings()

