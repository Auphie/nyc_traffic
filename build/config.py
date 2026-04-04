from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

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


def resolve_path(value: str | Path, base_dir: Path | None = None) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    anchor = base_dir or ROOT_DIR
    return (anchor / path).resolve()


def resolve_duckdb_path(path_override: str | Path | None = None) -> Path:
    if path_override is not None:
        return resolve_path(path_override)

    env_settings = load_environment_settings()
    return resolve_path(env_settings.dbt_duckdb_path)
