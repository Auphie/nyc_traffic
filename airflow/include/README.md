# airflow/include/

Use this directory for Airflow-only supporting assets such as:

- environment-specific config
- templated SQL files
- small runtime payloads needed by DAGs

Do not duplicate shared Python logic here. Shared logic should stay in `build/`.
