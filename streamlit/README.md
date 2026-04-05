# streamlit/

This directory is reserved for the Streamlit application layer.

Recommended responsibilities:

- `app.py` is the main entrypoint
- `pages/` contains multi-page Streamlit views
- `components/` contains small UI helpers or query wrappers
- the app reads from `prod.duckdb` in read-only mode

Recommended practice:

- keep Streamlit read-only
- treat `prod.duckdb` as the serving database
- keep transformation logic in dbt, not in the Streamlit app

Suggested future layout:

```text
streamlit/
├── app.py
├── pages/
└── components/
```
