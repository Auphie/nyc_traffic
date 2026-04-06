from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from components.data_access import (  # noqa: E402,I001
    DashboardQueryError,
    database_exists,
    fetch_hourly_taxi_core_stats,
    fetch_monthly_activity,
    fetch_overview_metrics,
    list_relations,
    resolve_serving_database_path,
)


st.set_page_config(
    page_title="NYC TLC Dashboard",
    page_icon=":taxi:",
    layout="wide",
)

st.markdown(
    """
    <style>
      .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #fff3bf 0%, #f59e0b 100%);
        color: #1f2937;
        margin-bottom: 1rem;
      }
      .hero h1 {
        margin: 0;
        font-size: 2.2rem;
      }
      .hero p {
        margin: 0.4rem 0 0;
        max-width: 58rem;
        font-size: 1rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_overview() -> dict[str, object]:
    return fetch_overview_metrics()


@st.cache_data(ttl=60)
def load_monthly_activity() -> pd.DataFrame:
    return fetch_monthly_activity()


@st.cache_data(ttl=60)
def load_hourly_snapshot() -> pd.DataFrame:
    return fetch_hourly_taxi_core_stats(limit=25)


@st.cache_data(ttl=60)
def load_relations() -> pd.DataFrame:
    return list_relations()


def main() -> None:
    database_path = resolve_serving_database_path()

    st.markdown(
        """
        <section class="hero">
          <h1>NYC TLC Near-Real-Time Dashboard</h1>
          <p>
            Streamlit reads <code>prod.duckdb</code> in read-only mode while dbt
            continues building in <code>build.duckdb</code>. This keeps the demo
            focused on low-cost serving with atomic database promotion.
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.header("Serving Database")
    st.sidebar.code(str(database_path))
    st.sidebar.caption("Override with PROD_DUCKDB_PATH if you want a different serving file.")

    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()

    if not database_exists(database_path):
        st.warning(
            "The production DuckDB file does not exist yet. Run `make dbt-seed`, "
            "`make dbt-run`, and `make swap-duckdb`, then refresh the page."
        )
        return

    try:
        metrics = load_overview()
        monthly_activity = load_monthly_activity()
        hourly_snapshot = load_hourly_snapshot()
        relations = load_relations()
    except DashboardQueryError as exc:
        st.error(f"Unable to read the serving database: {exc}")
        st.info(
            "Make sure `prod.duckdb` exists and already contains the `core` and "
            "`analytics` models before starting Streamlit."
        )
        return

    metric_cols = st.columns(4)
    metric_cols[0].metric("Trip Events", f"{metrics['trip_events']:,}")
    metric_cols[1].metric("Service Types", f"{metrics['service_types']}")
    metric_cols[2].metric("Latest Event Date", str(metrics["latest_event_date"] or "-"))
    metric_cols[3].metric("Hourly Rows", f"{metrics['hourly_rows']:,}")

    left_col, right_col = st.columns([1.3, 1.0])

    with left_col:
        st.subheader("Monthly Activity")
        if monthly_activity.empty:
            st.info("No monthly analytics rows are available yet.")
        else:
            pivoted = monthly_activity.pivot(
                index="trip_month",
                columns="service_type",
                values="trip_count",
            ).fillna(0)
            st.line_chart(pivoted)
            st.dataframe(
                monthly_activity,
                use_container_width=True,
                hide_index=True,
            )

    with right_col:
        st.subheader("Served Relations")
        st.dataframe(relations, use_container_width=True, hide_index=True)

    st.subheader("Latest Hourly Zone Flow Snapshot")
    if hourly_snapshot.empty:
        st.info("No hourly route aggregates are available yet.")
    else:
        st.dataframe(hourly_snapshot, use_container_width=True, hide_index=True)

    with st.expander("Local run sequence"):
        st.code(
            "\n".join(
                [
                    "make dbt-seed",
                    "make dbt-run",
                    "make swap-duckdb",
                    "make streamlit-run",
                ]
            )
        )


if __name__ == "__main__":
    main()
