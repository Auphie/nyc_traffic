# airflow/include/

Use this directory for Airflow-facing assets that are not DAG definitions.

Examples:

- runtime YAML/JSON config
- shared SQL files for DAG tasks
- small text templates used by operators

Do not duplicate Python business logic here if it already belongs in `build/`.

Use this directory for Airflow-only supporting assets such as:

- environment-specific config
- templated SQL files
- small runtime payloads needed by DAGs

Do not duplicate shared Python logic here. Shared logic should stay in `build/`.
