# build/

This directory holds the Python utilities that orchestrate the project.

Current responsibilities:

- bootstrap DuckDB schemas and operational metadata
- discover source files from the local landing zone
- support dbt runs that read landed parquet files directly into staging views
- promote `build.duckdb` to `prod.duckdb` with an atomic swap once the build is idle
- write structured logs and sample outputs
- trigger dbt runs after local file discovery completes

Boundary with future directories:

- `build/` contains reusable Python logic
- `airflow/` should call into `build/`, not replace it
- `streamlit/` should consume outputs from DuckDB, not perform orchestration

## Current Commands

### Environment check

```bash
python -m build.check_environment
```

### DuckDB bootstrap

```bash
python -m build.bootstrap
```

Optional scratch database override:

```bash
python -m build.bootstrap --duckdb-path ./dev_bootstrap.duckdb
```

### Download public TLC parquet files

```bash
python -m build.download_from_tlc_full --start-month 2025-01 --end-month 2025-03
python -m build.download_from_tlc_incremental
```

Files are written into `./data` by default.

### Source discovery

```bash
python -m build.source_discovery
```

Optional filters and offline input:

```bash
python -m build.source_discovery --table green_trips
python -m build.source_discovery --data-dir ./data
python -m build.source_discovery --output json
```

## Current Operational Schema

The bootstrap flow currently creates:

- `staging` schema for normalized staging views
- `analytics` schema for downstream marts and summaries
- `ops` schema for operational metadata
- `ops.source_metadata` for source-file tracking and future incremental orchestration

`ops.source_metadata` columns:

- `table_name TEXT NOT NULL`
- `source_name TEXT NOT NULL`
- `object_key TEXT`
- `source_month DATE`
- `source_etag TEXT`
- `source_last_modified_at TIMESTAMP`
- `load_status TEXT`
- `batch_id TEXT`
- `row_count BIGINT`
- `last_loaded_at TIMESTAMP`
- `last_error TEXT`
- `created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`

The table is additive-friendly: bootstrap uses `create table if not exists` plus `add column if not exists` so it can be re-run safely as the metadata contract grows.

## Current Discovery Rules

The source discovery module currently understands five logical datasets:

- `fhv_trips` from `fhv_tripdata_YYYY-MM.parquet`
- `fhvhv_trips` from `fhvhv_tripdata_YYYY-MM.parquet`
- `green_trips` from `green_tripdata_YYYY-MM.parquet`
- `yellow_trips` from `yellow_tripdata_YYYY-MM.parquet`
- `taxi_zone_shape` from the taxi zone parquet reference asset

Planned load modes:

- trip datasets: `incremental`
- taxi zone shape: `replace_on_change`

Canonical timestamp rules:

- `fhv_trips` -> `pickup_datetime`
- `fhvhv_trips` -> `pickup_datetime`
- `green_trips` -> `lpep_pickup_datetime`
- `yellow_trips` -> `tpep_pickup_datetime`

Discovery compares source object keys and object state to `ops.source_metadata` and marks each candidate as `new`, `unchanged`, or `reload`.

Current runtime expectation:

- parquet trip files are downloaded locally under `data/`
- discovery reads the local landing zone by default
- dbt staging views explicitly call DuckDB `read_parquet(...)` against local glob patterns
- dbt writes to `./build.duckdb` by default
- visual tools should read `./prod.duckdb`
- `python -m build.swap_duckdb` promotes build to prod with `os.replace()` after a build-lock check
- source discovery no longer depends on anonymous S3 listing
- the default build DuckDB file lives at `./build.duckdb`
- the default production DuckDB file lives at `./prod.duckdb`
- the default dbt profile lives at `./.env_duck/profiles.yml`
