# Project Structure

Recommended top-level structure for the full project:

```text
nyc_traffic/
├── airflow/           # Airflow-only orchestration layer
├── build/             # Shared Python jobs and operational utilities
├── data/              # Local landed parquet files, gitignored
├── docs/              # Architecture and project notes
├── etl/               # dbt project
├── streamlit/         # Dashboard application layer
├── tests/             # Python unit and integration tests
├── state/build/nyc_tlc.duckdb   # dbt build database
├── state/prod/nyc_tlc.duckdb    # serving database for dashboards
└── Makefile
```

Recommended ownership by directory:

- `build/`: shared Python modules for download, discovery, bootstrap, and DuckDB swap
- `etl/`: dbt staging and analytics models
- `airflow/`: scheduler wrappers that call `build/`, dbt, and swap promotion
- `streamlit/`: read-only application layer for dashboards
- `tests/`: tests for shared Python logic and future app/orchestration integrations

Recommended practice:

- keep DAGs thin and orchestration-focused
- keep Streamlit read-only against `prod.duckdb`
- keep reusable logic in `build/`
- keep SQL transformation logic in dbt
- let the build-to-prod swap separate writers from readers
