# etl/

This directory is reserved for the dbt project.

Planned contents:

- `dbt_project.yml`
- `models/` for sources, staging, intermediate, and marts
- `macros/` for reusable SQL or Jinja helpers
- `snapshots/`, `analyses/`, and dbt test assets as needed

The project will use the `dbt_nyc_traffic` profile and read `../profiles.yml` through `DBT_PROFILES_DIR=..`.

