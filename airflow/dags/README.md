# airflow/dags/

Keep DAG files thin.

Good DAG responsibilities:

- schedule tasks
- pass runtime parameters
- call `build.*` modules
- trigger dbt commands against `etl/dbt`

Avoid putting transformation or file-processing logic directly in DAG code.
