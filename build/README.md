# build/

This directory will hold the Python utilities that orchestrate the project.

Planned responsibilities:

- bootstrap DuckDB schemas and operational metadata
- discover source files in AWS-hosted storage
- run incremental raw-data ingestion
- write structured logs and sample outputs
- trigger dbt runs after raw loads complete

Current contents are intentionally small for the first PR.

