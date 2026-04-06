from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from components.data_access import (  # noqa: E402,I001
    DashboardQueryError,
    fetch_route_rankings,
    fetch_service_types,
)


st.set_page_config(page_title="Zone Flow Explorer", page_icon=":bar_chart:", layout="wide")


@st.cache_data(ttl=60)
def load_service_types() -> list[str]:
    return fetch_service_types()


@st.cache_data(ttl=60)
def load_rankings(service_type: str | None, sort_metric: str, limit: int) -> pd.DataFrame:
    return fetch_route_rankings(
        service_type=service_type,
        sort_metric=sort_metric,
        limit=limit,
    )


def main() -> None:
    st.title("Zone Flow Explorer")
    st.caption(
        "Inspect the highest commute-time or commute-distance "
        "pickup-to-dropoff zone combinations."
    )

    try:
        service_types = load_service_types()
    except DashboardQueryError as exc:
        st.error(f"Unable to load service types from prod.duckdb: {exc}")
        st.stop()

    options = ["All"] + service_types
    selected_service_type = st.sidebar.selectbox("Service Type", options)
    sort_metric = st.sidebar.radio(
        "Sort By",
        options=["average_commute_minutes", "average_commute_distance"],
        format_func=lambda value: value.replace("_", " ").title(),
    )
    limit = st.sidebar.slider("Rows", min_value=10, max_value=100, value=25, step=5)

    try:
        rankings = load_rankings(
            None if selected_service_type == "All" else selected_service_type,
            sort_metric,
            limit,
        )
    except DashboardQueryError as exc:
        st.error(f"Unable to load hourly route rankings: {exc}")
        st.stop()

    if rankings.empty:
        st.info("No hourly route rows are available yet.")
        return

    chart_frame = rankings.copy()
    chart_frame["route_label"] = (
        chart_frame["pickup_zone"].fillna("Unknown")
        + " -> "
        + chart_frame["dropoff_zone"].fillna("Unknown")
    )
    chart_frame = chart_frame.set_index("route_label")[[sort_metric]]

    st.bar_chart(chart_frame)
    st.dataframe(rankings, use_container_width=True, hide_index=True)
