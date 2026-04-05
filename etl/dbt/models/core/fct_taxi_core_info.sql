{{ config(materialized='view') }}

with taxi_core_info as (
    select
        service_type,
        pickup_location_id,
        dropoff_location_id,
        cast(pickup_at as date) as event_date,
        extract(hour from pickup_at) as event_hour,
        pickup_at as pickup_datetime,
        dropoff_at as dropoff_datetime,
        dropoff_at - pickup_at as commute_datetime,
        trip_distance
    from {{ ref('stg_yellow_trips') }}

    union all

    select
        service_type,
        pickup_location_id,
        dropoff_location_id,
        cast(pickup_at as date) as event_date,
        extract(hour from pickup_at) as event_hour,
        pickup_at as pickup_datetime,
        dropoff_at as dropoff_datetime,
        dropoff_at - pickup_at as commute_datetime,
        trip_distance
    from {{ ref('stg_green_trips') }}

    union all

    select
        service_type,
        pickup_location_id,
        dropoff_location_id,
        cast(pickup_at as date) as event_date,
        extract(hour from pickup_at) as event_hour,
        pickup_at as pickup_datetime,
        dropoff_at as dropoff_datetime,
        dropoff_at - pickup_at as commute_datetime,
        trip_miles as trip_distance
    from {{ ref('stg_fhvhv_trips') }}

    union all

    select
        service_type,
        pickup_location_id,
        dropoff_location_id,
        cast(pickup_at as date) as event_date,
        extract(hour from pickup_at) as event_hour,
        pickup_at as pickup_datetime,
        dropoff_at as dropoff_datetime,
        dropoff_at - pickup_at as commute_datetime,
        cast(null as double) as trip_distance
    from {{ ref('stg_fhv_trips') }}
)

select *
from taxi_core_info
