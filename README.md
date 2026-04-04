# NYC Taxi & Limousine (TLC) Trip

NYC Taxi & Limousine (TLC) Trip is a Python-first demo project for showing how to build a near-real-time analytics workflow with DuckDB, dbt, and NYC TLC trip data.

For this project, "near-real-time" means:

- downloading newly published TLC parquet files into a local landing zone,
- detecting new or changed landed files quickly,
- transforming them with dbt into analytics-ready tables.

The TLC source data is published monthly with a delay, so this repo demonstrates low-latency ingestion after new files appear, not per-trip live event streaming.

## Current Scope

The project currently includes:

- base directory layout for Python jobs, dbt work, and tests,
- Python dependency manifests for the `.env_duck` virtual environment,
- parent-path configuration guidance for DuckDB and dbt profiles,
- a small environment check script plus operational DuckDB bootstrap and metadata setup,
- local TLC download jobs for full backfill and current-month incremental pulls,
- local source discovery and ingestion planning against landed files in `data/`,
- local and CI style checks for Python and SQL files,
- a pull request template for incremental feature PRs.

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

### 1. Create the virtual environment and install dependencies

```bash
make install
source .env_duck/bin/activate
```

See [requirements.md](/Users/LED/Code/Github/Auphie/nyc_traffic/requirements.md) for package details and tooling notes.

### 2. Configure parent-level shared paths

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

### 3. Validate the local setup

```bash
make check-env
```

The checker reports which expected files, directories, and environment variables are already in place.

### 4. Bootstrap the operational DuckDB layer

```bash
make bootstrap
```

The bootstrap command is idempotent. Re-running it keeps existing schemas and tables in place and adds any missing metadata columns needed by later tickets.

### 5. Download TLC parquet files into the local landing zone

There are now two user-facing download modes built on shared internal download helpers.

Full backfill for a month range:

```bash
make download-tlc-full START_MONTH=2020-01 END_MONTH=2026-02
```

If you run `make download-tlc-full` without `START_MONTH` and `END_MONTH`, the script will prompt for them interactively using `YYYY-MM`.

Optional table filter:

```bash
make download-tlc-full START_MONTH=2025-01 END_MONTH=2025-03 \
  DOWNLOAD_ARGS="--table yellow_trips --table green_trips"
```

Incremental download for the current system month:

```bash
make download-tlc
```

Optional table filter or month override:

```bash
make download-tlc DOWNLOAD_ARGS="--table yellow_trips"
make download-tlc DOWNLOAD_ARGS="--month 2025-02"
```

These downloaders use the public TLC CloudFront parquet URLs and write files into `data/`, which is intentionally ignored by Git.

If the incremental download returns an HTTP 403 or 404 for the current system month, that usually means the month has not been published yet. The downloader will echo the original HTTP error and point you to the TLC homepage to verify availability:

- [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

### 6. Discover source files and plan ingestion

```bash
make discover-sources
```

By default, discovery reads from `./data`. You can limit the plan to one table:

```bash
make discover-sources DOWNLOAD_ARGS="--table yellow_trips"
```

Point discovery at a different local landing directory:

```bash
make discover-sources DOWNLOAD_ARGS="--data-dir ./data"
```

Render the plan as JSON:

```bash
make discover-sources DOWNLOAD_ARGS="--output json"
```

Current source rules:

- `fhv_trips` -> `fhv_tripdata_YYYY-MM.parquet` -> timestamp column `pickup_datetime`
- `fhvhv_trips` -> `fhvhv_tripdata_YYYY-MM.parquet` -> timestamp column `pickup_datetime`
- `green_trips` -> `green_tripdata_YYYY-MM.parquet` -> timestamp column `lpep_pickup_datetime`
- `yellow_trips` -> `yellow_tripdata_YYYY-MM.parquet` -> timestamp column `tpep_pickup_datetime`
- `taxi_zone_shape` -> taxi zone parquet reference file -> replace-on-change behavior

Discovery compares local source objects to `ops.source_metadata` and labels each object as `new`, `unchanged`, or `reload`.

### 7. Run local quality checks

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

AWS CLI remains installed in this project because later tickets may still need it for optional S3 workflows or alternative landing-zone patterns. The current download and discovery flow in this repo does not depend on AWS CLI.

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

Those metadata fields are now used by the source discovery planner to classify incoming source objects before raw ingestion is implemented.

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

1. incremental raw loaders
2. logging and sample capture
3. dbt sources, staging, and marts
4. pytest and dbt test coverage
