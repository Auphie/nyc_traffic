# build/

This directory will hold the Python utilities that orchestrate the project.

Planned responsibilities:

- bootstrap DuckDB schemas and operational metadata
- discover source files in AWS-hosted storage
- run incremental raw-data ingestion
- write structured logs and sample outputs
- trigger dbt runs after raw loads complete

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

## Current Operational Schema

The bootstrap flow currently creates:

- `raw` schema for future landed source tables
- `ops` schema for operational metadata
- `ops.source_metadata` for source-file tracking and load auditing

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
