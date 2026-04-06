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
    fetch_pickup_boroughs,
    fetch_service_types,
    fetch_pickup_zone_hourly_stats,
)


st.set_page_config(page_title="zone_hourly_stats", page_icon=":taxi:", layout="wide")

MEASURE_OPTIONS = {
    "Count": "count",
    "Average Commute Minutes": "average_commute_minutes",
    "Average Commute Distance": "average_commute_distance",
}


@st.cache_data(ttl=60)
def load_event_dates() -> list[str]:
    return fetch_event_dates()


@st.cache_data(ttl=60)
def load_service_types() -> list[str]:
    return fetch_service_types()


@st.cache_data(ttl=60)
def load_pickup_boroughs(
    event_date: str | None,
    service_type: str | None,
) -> list[str]:
    return fetch_pickup_boroughs(event_date, service_type=service_type)


@st.cache_data(ttl=60)
def load_pickup_zone_hourly_stats(
    event_date: str | None,
    pickup_borough: str | None,
    service_type: str | None,
    metric: str,
) -> pd.DataFrame:
    return fetch_pickup_zone_hourly_stats(
        event_date=event_date,
        pickup_borough=pickup_borough,
        service_type=service_type,
        metric=metric,
    )


def build_heatmap_spec(
    frame: pd.DataFrame,
    *,
    metric_label: str,
    pickup_zone_order: list[str],
) -> dict[str, object]:
    return {
        "mark": {"type": "rect", "cornerRadius": 3},
        "encoding": {
            "x": {
                "field": "event_hour",
                "type": "ordinal",
                "sort": list(range(24)),
                "title": "Hour of Day",
                "axis": {"orient": "top"},
            },
            "y": {
                "field": "pickup_zone",
                "type": "nominal",
                "sort": pickup_zone_order,
                "title": "Pickup Zone",
            },
            "color": {
                "field": "metric_value",
                "type": "quantitative",
                "title": metric_label,
                "scale": {"scheme": "goldorange"},
            },
            "tooltip": [
                {"field": "pickup_zone", "type": "nominal", "title": "Pickup Zone"},
                {"field": "event_hour", "type": "ordinal", "title": "Hour"},
                {
                    "field": "metric_value",
                    "type": "quantitative",
                    "title": metric_label,
                    "format": ".2f",
                },
            ],
        },
        "height": {"step": 24},
    }


def main() -> None:
    st.title("Pickup Zone statistics")
    st.caption(
        "Explore hourly pickup-zone patterns using the "
        "pre-aggregated hourly taxi analytics model."
    )

    try:
        event_dates = load_event_dates()
        service_types = load_service_types()
    except DashboardQueryError as exc:
        st.error(f"Unable to load event dates from prod.duckdb: {exc}")
        st.stop()

    if not event_dates:
        st.info("No hourly analytics rows are available yet.")
        return

    default_event_date = "2026-01-31"
    default_event_date_index = (
        event_dates.index(default_event_date) if default_event_date in event_dates else 0
    )
    filter_cols = st.columns(4)
    selected_event_date = filter_cols[1].selectbox(
        "Event Date",
        event_dates,
        index=default_event_date_index,
    )
    service_type_options = ["All"] + service_types
    selected_service_type = filter_cols[2].selectbox("Service Type", service_type_options)

    try:
        pickup_boroughs = load_pickup_boroughs(
            selected_event_date,
            None if selected_service_type == "All" else selected_service_type,
        )
    except DashboardQueryError as exc:
        st.error(f"Unable to load pickup boroughs from prod.duckdb: {exc}")
        st.stop()

    if not pickup_boroughs:
        st.info("No pickup boroughs are available for the selected filters.")
        return

    pickup_borough_options = ["All"] + pickup_boroughs
    default_pickup_borough = "Manhattan"
    default_pickup_borough_index = (
        pickup_borough_options.index(default_pickup_borough)
        if default_pickup_borough in pickup_borough_options
        else 0
    )
    selected_pickup_borough = filter_cols[0].selectbox(
        "Pickup Borough",
        pickup_borough_options,
        index=default_pickup_borough_index,
    )
    selected_measure_label = filter_cols[3].selectbox(
        "Measure",
        list(MEASURE_OPTIONS.keys()),
        index=0,
    )

    selected_measure = MEASURE_OPTIONS[selected_measure_label]

    try:
        zone_stats = load_pickup_zone_hourly_stats(
            selected_event_date,
            None if selected_pickup_borough == "All" else selected_pickup_borough,
            None if selected_service_type == "All" else selected_service_type,
            selected_measure,
        )
    except DashboardQueryError as exc:
        st.error(f"Unable to load zone hourly stats: {exc}")
        st.stop()

    if zone_stats.empty:
        st.info("No hourly rows are available for the selected filters.")
        return

    pickup_zone_order = (
        zone_stats.groupby("pickup_zone", as_index=False)["metric_value"]
        .mean()
        .sort_values("metric_value", ascending=False)["pickup_zone"]
        .tolist()
    )

    st.caption(
        f"Source slice: event_date = {selected_event_date}, "
        f"service_type = {selected_service_type}, "
        f"pickup_borough = {selected_pickup_borough}, rows = {len(zone_stats)}"
    )

    st.vega_lite_chart(
        zone_stats,
        build_heatmap_spec(
            zone_stats,
            metric_label=selected_measure_label,
            pickup_zone_order=pickup_zone_order,
        ),
        use_container_width=True,
    )

    pivoted = (
        zone_stats.pivot(index="pickup_zone", columns="event_hour", values="metric_value")
        .reindex(columns=list(range(24)))
        .reindex(pickup_zone_order)
    )
    st.dataframe(pivoted, use_container_width=True)


if __name__ == "__main__":
    main()
