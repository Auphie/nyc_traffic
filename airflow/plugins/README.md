# airflow/plugins/

Use this directory only when Airflow needs custom plugins.

Examples:

- custom operators
- custom hooks
- app-specific sensors

For this project, prefer built-in operators plus the existing CLI surface until a
custom plugin clearly reduces repetition.

Use this directory only if the project later needs custom Airflow plugins, hooks, or operators.

For now, prefer plain Python modules in `build/` and standard Airflow operators in DAG files.
