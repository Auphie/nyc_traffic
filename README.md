# NYC Taxi & Limousine (TLC) Trip

NYC Taxi & Limousine (TLC) Trip is a Python-first demo project for showing how to build a near-real-time analytics workflow with DuckDB, dbt, and NYC TLC trip data published in S3-compatible object storage.

For this project, "near-real-time" means:

- polling the source bucket for newly published Parquet files,
- loading new or changed files into DuckDB quickly,
- transforming them with dbt into analytics-ready tables.

The TLC source data is published monthly with a delay, so this repo demonstrates low-latency ingestion after new files appear, not per-trip live event streaming.

## Current Scope

The project currently includes:

- base directory layout for Python jobs, dbt work, and tests,
- Python dependency manifests for the `.env_duck` virtual environment,
- parent-path configuration guidance for DuckDB and dbt profiles,
- starter documentation and a small environment check script,
- a DuckDB bootstrap command that creates the first operational schema and metadata table,
- a pull request template and local lint commands for Python and SQL files.

Actual ingestion, dbt models, and broader automated tests will land in the next tickets.

## Planned Project Layout

```text
nyc_traffic/
├── build/              # Python orchestration, bootstrap, ingestion, utilities
├── etl/                # dbt project and SQL models
├── tests/              # pytest unit and integration tests
├── Makefile            # local convenience commands
├── README.md           # project overview and tutorial
├── requirements.txt    # pip-installable dependencies
├── requirements.md     # package rationale and setup notes
└── profiles.example.yml
```

## Data Sources

The project is designed around the official NYC TLC trip record data:

- [NYC TLC Trip Records on AWS](https://registry.opendata.aws/nyc-tlc-trip-records-pds/)
- [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

The initial source groups are:

- `fhv_trips`
- `fhvhv_trips`
- `green_trips`
- `yellow_trips`
- `taxi_zone_shape`

The first four will be loaded incrementally. `taxi_zone_shape` will be handled as a reference dataset.

## Local Setup

### 1. Create the virtual environment

```bash
python3 -m venv .env_duck
source .env_duck/bin/activate
```

Or use the Makefile:

```bash
make install
source .env_duck/bin/activate
```

### 2. Install Python packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

See [requirements.md](/Users/LED/Code/Github/Auphie/nyc_traffic/requirements.md) for package details.

### 3. Configure parent-level shared paths

This project intentionally keeps its shared runtime assets one level above the repo:

- DuckDB database: `../nyc_tlc.duckdb`
- dbt profile: `../profiles.yml`
- logs directory: `../logs/`

Recommended shell exports:

```bash
export DBT_DUCKDB_PATH="../nyc_tlc.duckdb"
export DBT_PROFILES_DIR=".."
```

Create `../profiles.yml` by copying the template from [profiles.example.yml](/Users/LED/Code/Github/Auphie/nyc_traffic/profiles.example.yml).

### 4. Validate the local setup

Run the lightweight checker:

```bash
python -m build.check_environment
```

The checker reports which expected files, directories, and environment variables are already in place.

### 5. Bootstrap the operational DuckDB layer

Create the initial schemas and metadata table:

```bash
python -m build.bootstrap
```

If you want to test against a scratch database before using the shared parent path:

```bash
python -m build.bootstrap --duckdb-path ./dev_bootstrap.duckdb
```

The bootstrap command is idempotent. Re-running it keeps existing schemas and tables in place and adds any missing metadata columns needed by later tickets.

### 6. Run local quality checks

After activating `.env_duck`, run:

```bash
make lint
```

You can also run the checks independently:

```bash
make lint-python
make lint-sql
```

Linting details:

- Python linting uses `ruff`
- SQL linting uses `sqlfluff`
- the SQL config is dbt-ready, but it currently uses the `jinja` templater until the dbt project lands in a later ticket

The repository also runs the same style checks in GitHub Actions through `.github/workflows/ci_style_check.yml` on pushes to `main` and on pull requests.

## AWS CLI Note

The ingestion flow will depend on AWS CLI access to the TLC public data location. Install AWS CLI before running the later ingestion tickets.

For example:

```bash
aws --version
```

If AWS CLI is not installed yet, follow the install guide in [requirements.md](/Users/LED/Code/Github/Auphie/nyc_traffic/requirements.md).

## dbt Profile Template

The planned dbt profile is:

```yaml
dbt_nyc_traffic:
  outputs:
    dev:
      type: duckdb
      path: "{{ env_var('DBT_DUCKDB_PATH', 'dev.duckdb') }}"
      schema: dev
      threads: 4
  target: dev
```

The real file should live at `../profiles.yml` so this repo does not depend on machine-specific global dbt configuration.

## Operational Metadata

The first operational table is `ops.source_metadata`. It is designed to support future idempotent ingestion and auditing.

Required fields:

- `table_name`
- `source_name`
- `created_at`
- `updated_at`

Additional fields included now for future incremental loading:

- `object_key`
- `source_month`
- `source_etag`
- `source_last_modified_at`
- `load_status`
- `batch_id`
- `row_count`
- `last_loaded_at`
- `last_error`

See [build/README.md](/Users/LED/Code/Github/Auphie/nyc_traffic/build/README.md) for the operational layer notes.

## Contribution Workflow

This repo now includes a pull request template at [.github/PULL_REQUEST_TEMPLATE.md](/Users/LED/Code/Github/Auphie/nyc_traffic/.github/PULL_REQUEST_TEMPLATE.md).

Use it to capture:

- the ticket summary
- the main code or config changes
- the validation commands you ran
- any risks, gaps, or follow-up work

## What Comes Next

The next tickets will add:

1. source discovery and ingestion planning
2. incremental raw loaders
3. logging and sample capture
4. dbt sources, staging, and marts
5. pytest and dbt test coverage
