from __future__ import annotations

"""Scenario placeholder for the future Streamlit entrypoint.

The app layer should read from prod.duckdb in read-only mode and avoid
embedding transformation logic that belongs in dbt.
"""


def main() -> None:
    print("Streamlit app scaffold. Point future dashboards at prod.duckdb.")


if __name__ == "__main__":
    main()
