# streamlit/

This directory holds the Streamlit serving layer for the NYC TLC demo.

Current responsibilities:

- `app.py` is the main dashboard entrypoint
- `pages/` contains focused exploratory pages such as zone-flow drilldowns
- `components/` contains shared DuckDB query helpers
- the app reads from `state/prod/nyc_tlc.duckdb` in read-only mode

Local run flow:

```bash
make dbt-seed
make dbt-run
make swap-duckdb
make streamlit-run
```

Recommended practice:

- keep Streamlit read-only
- treat `state/prod/nyc_tlc.duckdb` as the serving database
- keep transformation logic in dbt, not in the Streamlit app
- keep DuckDB access centralized in `streamlit/components/`
