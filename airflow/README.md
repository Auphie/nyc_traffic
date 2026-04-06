# airflow/

This directory contains the Airflow orchestration layer for the NYC TLC demo.

The project keeps Airflow intentionally thin:

- `dags/` contains scheduling wrappers only
- `include/` is reserved for DAG-facing config or SQL assets
- `plugins/` is reserved for custom operators and hooks only if they become necessary

All business logic should stay in:

- `build/` for Python workflows
- `etl/dbt` for SQL transformations

## Local Setup

For this demo project, Airflow is installed into the same `.env_duck`
environment as DuckDB, dbt, and Streamlit.

Why this repo uses one environment instead of the more common separate-Airflow
setup:

- this project is a laptop-friendly demo
- one environment is simpler for local onboarding
- the reduced setup friction is more valuable here than strict dependency isolation

In a more production-like setup, a separate Airflow environment or separate host
would still be the safer default.

Official install guidance:
- [Apache Airflow Quick Start](https://airflow.apache.org/docs/apache-airflow/3.1.2/start.html)

Airflow is included in the repo's main install flow:

```bash
make install
```

If you need to re-run only the Airflow installation step later, you can still use:

```bash
make airflow-install
```

Start Airflow in standalone mode:

```bash
make airflow-standalone
```

This uses:

- `AIRFLOW_HOME=./airflow/.local`
- DAG folder `./airflow/dags`
- example DAGs disabled

After Airflow starts, open the UI at `http://localhost:8080`.

## Included DAG

`dags/nyc_tlc_local_pipeline.py` orchestrates the existing local workflow:

1. `make download-tlc`
2. `make bootstrap`
3. `make dbt-seed`
4. `make dbt-run`
5. `make swap-duckdb`

This keeps writers on `state/build/nyc_tlc.duckdb` and readers on
`state/prod/nyc_tlc.duckdb`.
