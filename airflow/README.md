# airflow/

This directory is reserved for Airflow-specific orchestration.

Recommended responsibilities:

- `dags/` contains thin DAG definitions only
- `include/` contains Airflow-facing config, SQL, or helper assets
- `plugins/` contains custom operators or hooks only when truly needed

Recommended practice:

- keep orchestration logic in `build/`
- let DAGs call Python entrypoints from `build/` and dbt commands from `etl/`
- avoid duplicating business logic inside DAG files

Suggested future layout:

```text
airflow/
├── dags/
├── include/
└── plugins/
```
