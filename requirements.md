# Requirements Guide

This project uses a dedicated DuckDB-focused virtual environment named `.env_duck`.

## Python Packages

Install the project dependencies with:

```bash
pip install -r requirements.txt
```

Package summary:

- `awscli`: discover and access NYC TLC source files from AWS-hosted storage
- `duckdb`: embedded analytics database used as the main project warehouse
- `duckdb-cli`: local DuckDB shell for inspection and manual queries
- `dbt-core`: dbt framework for transformations and tests
- `dbt-duckdb`: dbt adapter for DuckDB
- `pandas`: lightweight local data inspection helpers
- `pyarrow`: Parquet support for Python-side file handling
- `pytest`: unit and integration test runner
- `python-dotenv`: optional local environment variable loading for Python utilities
- `PyYAML`: YAML parsing for future config helpers
- `ruff`: fast Python linting
- `sqlfluff`: SQL linter for DuckDB/dbt-style SQL
- `sqlfluff-templater-dbt`: dbt-aware templating support for future dbt models

## AWS CLI

AWS CLI is required for the ingestion workflow because the source data lives in AWS-hosted object storage.

Verify installation:

```bash
aws --version
```

If you do not already have AWS CLI installed, follow the official installer for your platform:

- macOS: `brew install awscli`
- official documentation: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>

## Virtual Environment

Recommended setup:

```bash
python3 -m venv .env_duck
source .env_duck/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Local Quality Checks

After installing dependencies and activating `.env_duck`, run:

```bash
make lint
```

Individual commands:

```bash
make lint-python
make lint-sql
```

Current linting approach:

- `ruff` checks the Python code in `build/` and `tests/`
- `sqlfluff` checks SQL files under `etl/`
- the SQL linter is configured to be dbt-ready, but uses the `jinja` templater for now because the dbt project files will land in a later ticket

## Shared Parent-Level Assets

This project expects a few runtime assets to live in the parent directory:

- `../nyc_tlc.duckdb`
- `../profiles.yml`
- `../logs/`

Recommended environment variables:

```bash
export DBT_DUCKDB_PATH="../nyc_tlc.duckdb"
export DBT_PROFILES_DIR=".."
```

Copy the repo template into the parent folder when you are ready to use dbt:

```bash
cp profiles.example.yml ../profiles.yml
```
