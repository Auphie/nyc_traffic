from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


class DashboardQueryError(RuntimeError):
    """Raised when the Streamlit app cannot read the serving database."""


def resolve_serving_database_path() -> Path:
    default_path = Path(__file__).resolve().parents[2] / "state" / "prod" / "nyc_tlc.duckdb"
    configured_path = Path(os.getenv("PROD_DUCKDB_PATH", str(default_path)))
    if configured_path.is_absolute():
        return configured_path
    return (Path.cwd() / configured_path).resolve()


def database_exists(path: Path | None = None) -> bool:
    database_path = path or resolve_serving_database_path()
    return database_path.exists()


def list_relations(path: Path | None = None) -> pd.DataFrame:
    database_path = path or resolve_serving_database_path()
    if not database_path.exists():
        return pd.DataFrame(columns=["table_schema", "table_name", "table_type"])

    sql = """
        select
            table_schema,
            table_name,
            table_type
        from information_schema.tables
        where table_schema in ('staging', 'core', 'analytics')
        order by table_schema, table_name
    """
    return run_query(sql, path=database_path)


def fetch_overview_metrics(path: Path | None = None) -> dict[str, Any]:
    database_path = path or resolve_serving_database_path()
    empty_metrics: dict[str, Any] = {
        "trip_events": 0,
        "service_types": 0,
        "latest_event_date": None,
        "hourly_rows": 0,
        "latest_month": None,
    }
    if not database_path.exists():
        return empty_metrics

    sql = """
        with core_metrics as (
            select
                count(*) as trip_events,
                count(distinct service_type) as service_types,
                max(event_date) as latest_event_date
            from core.fct_taxi_core_info
        ),
        hourly_metrics as (
            select count(*) as hourly_rows
            from analytics.fct_hourly_taxi_core_stats
        ),
        monthly_metrics as (
            select max(trip_month) as latest_month
            from analytics.fct_trip_activity_monthly
        )
        select
            core_metrics.trip_events,
            core_metrics.service_types,
            core_metrics.latest_event_date,
            hourly_metrics.hourly_rows,
            monthly_metrics.latest_month
        from core_metrics
        cross join hourly_metrics
        cross join monthly_metrics
    """

    frame = run_query(sql, path=database_path)
    if frame.empty:
        return empty_metrics

    row = frame.iloc[0].to_dict()
    return {
        "trip_events": int(row["trip_events"] or 0),
        "service_types": int(row["service_types"] or 0),
        "latest_event_date": row["latest_event_date"],
        "hourly_rows": int(row["hourly_rows"] or 0),
        "latest_month": row["latest_month"],
    }


def fetch_monthly_activity(path: Path | None = None) -> pd.DataFrame:
    sql = """
        select
            service_type,
            trip_month,
            trip_count,
            avg_trip_distance,
            gross_amount
        from analytics.fct_trip_activity_monthly
        order by trip_month, service_type
    """
    return run_query(sql, path=path)


def fetch_service_types(path: Path | None = None) -> list[str]:
    sql = """
        select distinct service_type
        from analytics.fct_hourly_taxi_core_stats
        where service_type is not null
        order by service_type
    """
    frame = run_query(sql, path=path)
    return [str(value) for value in frame["service_type"].tolist()]


def fetch_hourly_taxi_core_stats(
    path: Path | None = None,
    *,
    service_type: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    sql = """
        select
            pickup_borough,
            pickup_zone,
            pickup_service_zone,
            dropoff_borough,
            dropoff_zone,
            dropoff_service_zone,
            service_type,
            event_date,
            event_hour,
            average_commute_minutes,
            average_commute_distance
        from analytics.fct_hourly_taxi_core_stats
        where (? is null or service_type = ?)
        order by event_date desc, event_hour desc, average_commute_minutes desc nulls last
        limit ?
    """
    return run_query(sql, path=path, params=[service_type, service_type, limit])


def fetch_pickup_zones(path: Path | None = None) -> list[str]:
    return fetch_pickup_zones_by_date(event_date=None, path=path)


def fetch_event_dates(path: Path | None = None) -> list[str]:
    sql = """
        select distinct cast(event_date as varchar) as event_date
        from analytics.fct_hourly_taxi_core_stats
        where event_date is not null
        order by event_date desc
    """
    frame = run_query(sql, path=path)
    return [str(value) for value in frame["event_date"].tolist()]


def fetch_pickup_zones_by_date(
    event_date: str | None,
    *,
    pickup_borough: str | None = None,
    service_type: str | None = None,
    path: Path | None = None,
) -> list[str]:
    sql = """
        select distinct pickup_zone
        from analytics.fct_hourly_taxi_core_stats
        where pickup_zone is not null
          and (? is null or cast(event_date as varchar) = ?)
          and (? is null or pickup_borough = ?)
          and (? is null or service_type = ?)
        order by pickup_zone
    """
    frame = run_query(
        sql,
        path=path,
        params=[
            event_date,
            event_date,
            pickup_borough,
            pickup_borough,
            service_type,
            service_type,
        ],
    )
    return [str(value) for value in frame["pickup_zone"].tolist()]


def fetch_pickup_boroughs(
    event_date: str | None,
    *,
    service_type: str | None,
    path: Path | None = None,
) -> list[str]:
    sql = """
        select distinct pickup_borough
        from analytics.fct_hourly_taxi_core_stats
        where pickup_borough is not null
          and (? is null or cast(event_date as varchar) = ?)
          and (? is null or service_type = ?)
        order by pickup_borough
    """
    frame = run_query(
        sql,
        path=path,
        params=[event_date, event_date, service_type, service_type],
    )
    return [str(value) for value in frame["pickup_borough"].tolist()]


def fetch_pickup_zone_hourly_stats(
    *,
    event_date: str | None,
    pickup_borough: str | None,
    service_type: str | None,
    metric: str,
    path: Path | None = None,
) -> pd.DataFrame:
    metric_column = (
        "average_commute_distance"
        if metric == "average_commute_distance"
        else "average_commute_minutes"
    )
    metric_sql = "count(*)" if metric == "count" else f"avg({metric_column})"
    sql = f"""
        select
            event_hour,
            pickup_zone,
            {metric_sql} as metric_value
        from analytics.fct_hourly_taxi_core_stats
        where pickup_zone is not null
          and (? is null or cast(event_date as varchar) = ?)
          and (? is null or pickup_borough = ?)
          and (? is null or service_type = ?)
          and ({'true' if metric == 'count' else metric_column + ' is not null'})
        group by 1, 2
        order by 2, 1
    """
    return run_query(
        sql,
        path=path,
        params=[
            event_date,
            event_date,
            pickup_borough,
            pickup_borough,
            service_type,
            service_type,
        ],
    )


def fetch_route_rankings(
    path: Path | None = None,
    *,
    event_date: str | None = None,
    service_type: str | None = None,
    sort_metric: str = "average_commute_minutes",
    limit: int = 15,
) -> pd.DataFrame:
    metric = (
        "average_commute_distance"
        if sort_metric == "average_commute_distance"
        else "average_commute_minutes"
    )
    sql = f"""
        select
            pickup_zone,
            dropoff_zone,
            service_type,
            event_date,
            event_hour,
            average_commute_minutes,
            average_commute_distance
        from analytics.fct_hourly_taxi_core_stats
        where (? is null or cast(event_date as varchar) = ?)
          and (? is null or service_type = ?)
          and {metric} is not null
        order by {metric} desc nulls last, event_date desc, event_hour desc
        limit ?
    """
    return run_query(
        sql,
        path=path,
        params=[event_date, event_date, service_type, service_type, limit],
    )


def fetch_route_overview_stats(
    path: Path | None = None,
    *,
    event_date: str | None = None,
    service_type: str | None = None,
) -> dict[str, Any]:
    sql = """
        select
            count(*) as route_rows,
            count(distinct pickup_zone) as pickup_zones,
            count(distinct dropoff_zone) as dropoff_zones,
            avg(average_commute_minutes) as avg_commute_minutes,
            avg(average_commute_distance) as avg_commute_distance
        from analytics.fct_hourly_taxi_core_stats
        where (? is null or cast(event_date as varchar) = ?)
          and (? is null or service_type = ?)
    """
    frame = run_query(
        sql,
        path=path,
        params=[event_date, event_date, service_type, service_type],
    )
    if frame.empty:
        return {
            "route_rows": 0,
            "pickup_zones": 0,
            "dropoff_zones": 0,
            "avg_commute_minutes": None,
            "avg_commute_distance": None,
        }

    row = frame.iloc[0].to_dict()
    return {
        "route_rows": int(row["route_rows"] or 0),
        "pickup_zones": int(row["pickup_zones"] or 0),
        "dropoff_zones": int(row["dropoff_zones"] or 0),
        "avg_commute_minutes": row["avg_commute_minutes"],
        "avg_commute_distance": row["avg_commute_distance"],
    }


def fetch_route_hourly_profile(
    path: Path | None = None,
    *,
    event_date: str | None = None,
    service_type: str | None = None,
    metric: str = "average_commute_minutes",
) -> pd.DataFrame:
    metric_column = (
        "average_commute_distance"
        if metric == "average_commute_distance"
        else "average_commute_minutes"
    )
    sql = f"""
        select
            event_hour,
            avg({metric_column}) as metric_value
        from analytics.fct_hourly_taxi_core_stats
        where (? is null or cast(event_date as varchar) = ?)
          and (? is null or service_type = ?)
          and {metric_column} is not null
        group by 1
        order by 1
    """
    return run_query(
        sql,
        path=path,
        params=[event_date, event_date, service_type, service_type],
    )


def fetch_recent_core_sample(path: Path | None = None, *, limit: int = 200) -> pd.DataFrame:
    sql = """
        select
            service_type,
            pickup_location_id,
            dropoff_location_id,
            event_date,
            event_hour,
            pickup_datetime,
            dropoff_datetime,
            commute_datetime,
            trip_distance
        from core.fct_taxi_core_info
        order by pickup_datetime desc
        limit ?
    """
    return run_query(sql, path=path, params=[limit])


def run_query(
    sql: str,
    *,
    path: Path | None = None,
    params: list[Any] | None = None,
) -> pd.DataFrame:
    database_path = path or resolve_serving_database_path()
    if not database_path.exists():
        raise DashboardQueryError(
            f"Serving database not found at {database_path}. Run dbt and swap first."
        )

    try:
        with duckdb.connect(str(database_path), read_only=True) as connection:
            if params:
                return connection.execute(sql, params).fetchdf()
            return connection.execute(sql).fetchdf()
    except duckdb.Error as exc:  # pragma: no cover - depends on local db state
        raise DashboardQueryError(str(exc)) from exc
