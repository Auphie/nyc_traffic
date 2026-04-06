# Requirements Guide

This project uses a dedicated DuckDB-focused virtual environment named `.env_duck`.

## Python Packages

Install the project dependencies with:

```bash
make install
```

This single command sets up the demo's full local toolchain inside `.env_duck`:

- dbt + DuckDB
- Streamlit
- Python linting and tests
- Airflow

Under the hood, `make install` installs `requirements.txt` first and then adds
Airflow with the official constraints-based installation pattern.

Because this demo intentionally keeps Airflow, dbt, and Streamlit in one shared
environment, `make install` also reapplies a few compatibility pins after the
Airflow install step:

- `click>=8.3,<9`
- `protobuf>=6,<7`
- `opentelemetry-proto>=1.40,<2`
- `opentelemetry-exporter-otlp>=1.40,<2`
- `opentelemetry-exporter-otlp-proto-common>=1.40,<2`
- `opentelemetry-exporter-otlp-proto-grpc>=1.40,<2`
- `opentelemetry-exporter-otlp-proto-http>=1.40,<2`

Those overrides keep dbt 1.11 and Airflow 3.1 working together in the same
`.env_duck` environment.

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
- `streamlit`: local dashboard layer for read-only serving against the production DuckDB file

## Airflow

For this demo project, Airflow is intentionally installed into the same
`.env_duck` environment as dbt, DuckDB, and Streamlit.

Why this repo uses one environment:

- simpler laptop setup
- easier demo onboarding
- fewer activation steps while developing locally

In a production-style deployment, keeping Airflow in a separate environment or
on a separate machine would still be the more conservative choice.

Recommended setup:

```bash
make install
```

This installs Airflow into `.env_duck` using the official constraints-based
installation pattern from the Apache Airflow quick start:

- [Apache Airflow Quick Start](https://airflow.apache.org/docs/apache-airflow/3.1.2/start.html)

Launch the local scheduler, API server, and UI with:

```bash
make airflow-standalone
```

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

If you prefer to create the environment manually before using `make`, this also works:

```bash
python3 -m venv .env_duck
source .env_duck/bin/activate
make install
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

## Runtime Defaults

This project uses these default runtime paths:

- `./state/build/nyc_tlc.duckdb`
- `./state/prod/nyc_tlc.duckdb`
- `./.env_duck/profiles.yml`
- `../logs/`

Recommended environment variables:

```bash
export DBT_DUCKDB_PATH="$(pwd)/state/build/nyc_tlc.duckdb"
export PROD_DUCKDB_PATH="$(pwd)/state/prod/nyc_tlc.duckdb"
export DBT_PROFILES_DIR="$(pwd)/.env_duck"
```

## Streamlit

Launch the local dashboard with:

```bash
make streamlit-run
```

The Streamlit app is intentionally read-only and should point at `./state/prod/nyc_tlc.duckdb`.
