# NYC Taxi & Limousine (TLC) Trip

NYC Taxi & Limousine (TLC) Trip is a Python-first demo project for showing how to build a near-real-time analytics workflow with DuckDB, dbt, and NYC TLC trip data published in S3-compatible object storage.

For this project, "near-real-time" means:

- polling the source bucket for newly published Parquet files,
- loading new or changed files into DuckDB quickly,
- transforming them with dbt into analytics-ready tables.

The TLC source data is published monthly with a delay, so this repo demonstrates low-latency ingestion after new files appear, not per-trip live event streaming.

## Current Scope

This first PR lays down the project scaffold:

- base directory layout for Python jobs, dbt work, and tests,
- Python dependency manifests for the `.env_duck` virtual environment,
- parent-path configuration guidance for DuckDB and dbt profiles,
- starter documentation and a small environment check script.

Actual ingestion, operational metadata tables, dbt models, and automated tests will land in the next tickets.

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
python build/check_environment.py
```

The checker reports which expected files, directories, and environment variables are already in place.

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

## What Comes Next

The next tickets will add:

1. DuckDB bootstrap code and `ops.source_metadata`
2. source discovery and ingestion planning
3. incremental raw loaders
4. logging and sample capture
5. dbt sources, staging, and marts
6. pytest and dbt test coverage

