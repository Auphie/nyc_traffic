# streamlit/components/

Use this directory for lightweight Streamlit support code such as:

- reusable query helpers
- small chart wrappers
- app-level configuration helpers

Current implementation:

- `data_access.py` contains read-only DuckDB query helpers for the Streamlit app

This is not the place for dbt models or orchestration logic.
