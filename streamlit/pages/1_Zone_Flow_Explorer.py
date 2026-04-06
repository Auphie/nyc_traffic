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
    fetch_event_dates,
    fetch_route_hourly_profile,
    fetch_route_overview_stats,
    fetch_route_rankings,
    fetch_service_types,
)


st.set_page_config(page_title="Zone Flow Explorer", page_icon=":bar_chart:", layout="wide")


@st.cache_data(ttl=60)
def load_event_dates() -> list[str]:
    return fetch_event_dates()


@st.cache_data(ttl=60)
def load_service_types() -> list[str]:
    return fetch_service_types()


@st.cache_data(ttl=60)
def load_rankings(
    event_date: str | None,
    service_type: str | None,
    sort_metric: str,
    limit: int,
) -> pd.DataFrame:
    return fetch_route_rankings(
        event_date=event_date,
        service_type=service_type,
        sort_metric=sort_metric,
        limit=limit,
    )


@st.cache_data(ttl=60)
def load_overview_stats(
    event_date: str | None,
    service_type: str | None,
) -> dict[str, object]:
    return fetch_route_overview_stats(
        event_date=event_date,
        service_type=service_type,
    )


@st.cache_data(ttl=60)
def load_hourly_profile(
    event_date: str | None,
    service_type: str | None,
    metric: str,
) -> pd.DataFrame:
    return fetch_route_hourly_profile(
        event_date=event_date,
        service_type=service_type,
        metric=metric,
    )


def main() -> None:
    st.title("Zone Flow Explorer")
    st.caption(
        "Inspect the highest commute-time or commute-distance "
        "pickup-to-dropoff zone combinations."
    )

    try:
        event_dates = load_event_dates()
        service_types = load_service_types()
    except DashboardQueryError as exc:
        st.error(f"Unable to load hourly route data from prod.duckdb: {exc}")
        st.stop()

    if not event_dates:
        st.info("No hourly route rows are available yet.")
        return

    default_event_date = "2026-01-31"
    default_event_date_index = (
        event_dates.index(default_event_date) if default_event_date in event_dates else 0
    )
    selected_event_date = st.sidebar.selectbox(
        "Event Date",
        event_dates,
        index=default_event_date_index,
    )
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
            selected_event_date,
            None if selected_service_type == "All" else selected_service_type,
            sort_metric,
            limit,
        )
        overview = load_overview_stats(
            selected_event_date,
            None if selected_service_type == "All" else selected_service_type,
        )
        hourly_profile = load_hourly_profile(
            selected_event_date,
            None if selected_service_type == "All" else selected_service_type,
            sort_metric,
        )
    except DashboardQueryError as exc:
        st.error(f"Unable to load hourly route explorer data: {exc}")
        st.stop()

    if rankings.empty:
        st.info("No hourly route rows are available for the selected filters.")
        return

    metric_label = sort_metric.replace("_", " ").title()
    top_route = rankings.iloc[0]
    avg_metric_value = rankings[sort_metric].mean()

    stats = st.columns(5)
    stats[0].metric("Event Date", selected_event_date)
    stats[1].metric("Route Rows", f"{overview['route_rows']:,}")
    stats[2].metric(
        f"Top {metric_label}",
        f"{top_route[sort_metric]:,.2f}",
    )
    stats[3].metric(
        "Pickup Zones",
        f"{overview['pickup_zones']:,}",
    )
    stats[4].metric(
        "Dropoff Zones",
        f"{overview['dropoff_zones']:,}",
    )

    st.caption(
        f"Top ranked route: {top_route['pickup_zone']} -> {top_route['dropoff_zone']} | "
        f"Average {metric_label.lower()} across the displayed routes: {avg_metric_value:,.2f}"
    )

    upper_left, upper_right = st.columns([1.25, 1.0])

    with upper_left:
        st.subheader("Hourly Profile")
        if hourly_profile.empty:
            st.info("No hourly profile rows are available for the selected filters.")
        else:
            profile_frame = hourly_profile.set_index("event_hour")[["metric_value"]]
            st.line_chart(profile_frame)

    with upper_right:
        st.subheader("Route Summary")
        st.metric(
            "Avg Commute Minutes",
            f"{(overview['avg_commute_minutes'] or 0):,.2f}",
        )
        st.metric(
            "Avg Commute Distance",
            f"{(overview['avg_commute_distance'] or 0):,.2f}",
        )

    chart_frame = rankings.copy()
    chart_frame["route_label"] = (
        chart_frame["pickup_zone"].fillna("Unknown")
        + " -> "
        + chart_frame["dropoff_zone"].fillna("Unknown")
    )
    chart_frame = chart_frame.set_index("route_label")[[sort_metric]]

    st.subheader("Top Route Rankings")
    st.bar_chart(chart_frame)
    st.dataframe(rankings, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
