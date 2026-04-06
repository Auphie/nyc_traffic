# airflow/dags/

Keep DAG files thin.

Good DAG responsibilities:

- schedule tasks
- pass runtime parameters
- call `build.*` modules or project `make` targets
- trigger dbt commands against `etl/dbt`

Avoid putting transformation or file-processing logic directly in DAG code.

Current DAG:

- `nyc_tlc_local_pipeline.py`

The current DAG intentionally shells out to the repo's existing commands so the
same workflow can be run from local development, CI, or Airflow with minimal drift.
