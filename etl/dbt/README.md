# etl/dbt/

This is the dbt project for the NYC TLC scenario-1 demo.

Current flow:

1. `make dbt-seed` loads the taxi-zone lookup CSV into DuckDB.
2. `make dbt-run` builds staging views directly from local TLC parquet files with DuckDB `read_parquet(...)`.
3. `make dbt-run` also materializes analytics tables for downstream reads.

Current model layout:

- `seeds/taxi_zone_lookup.csv` loads the taxi zone reference table
- `models/staging/` holds the parquet-backed trip staging views plus `stg_taxi_zone_lookup`
- `models/core/` holds shared dimensional tables and lightweight core facts such as `dim_taxi_zone` and `fct_taxi_core_info`
- `models/analytics/` holds BI-facing fact and summary tables such as `fct_trip_activity_monthly` and `fct_hourly_taxi_core_stats`

Useful commands:

```bash
make dbt-debug
make dbt-seed
make dbt-run
make dbt-test
```
