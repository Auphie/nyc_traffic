# etl/

This directory holds the dbt project for the NYC TLC demo.

Current scenario-1 focus:

- `models/staging/` shows direct DuckDB `read_parquet(...)` usage against local TLC parquet files
- `models/staging/` also contains a seed-backed taxi-zone staging view
- `models/core/` contains shared dimensional tables such as `dim_taxi_zone`
- `models/analytics/` contains light downstream tables for BI consumption
- `seeds/` stores reference data loaded into DuckDB before `dbt run`
- `macros/` contains only minimal dbt schema helpers

The project uses the `dbt_nyc_traffic` profile from `./.env_duck/profiles.yml`.

Boundary with future directories:

- `build/` prepares and promotes databases
- `airflow/` schedules dbt runs
- `streamlit/` reads dbt outputs from `prod.duckdb`
