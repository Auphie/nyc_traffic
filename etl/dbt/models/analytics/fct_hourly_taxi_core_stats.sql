with enriched_trips as (
    select
        pickup_zone.borough as pickup_borough,
        pickup_zone.zone_name as pickup_zone,
        pickup_zone.service_zone as pickup_service_zone,
        dropoff_zone.borough as dropoff_borough,
        dropoff_zone.zone_name as dropoff_zone,
        dropoff_zone.service_zone as dropoff_service_zone,
        core_info.service_type,
        core_info.event_date,
        core_info.event_hour,
        core_info.trip_distance,
        date_diff(
            'minute',
            core_info.pickup_datetime,
            core_info.dropoff_datetime
        ) as commute_minutes
    from {{ ref('fct_taxi_core_info') }} as core_info
    left join {{ ref('dim_taxi_zone') }} as pickup_zone
        on core_info.pickup_location_id = pickup_zone.location_id
    left join {{ ref('dim_taxi_zone') }} as dropoff_zone
        on core_info.dropoff_location_id = dropoff_zone.location_id
    where core_info.event_date >= (
        select max(core_window.event_date) - interval '7' day
        from {{ ref('fct_taxi_core_info') }} as core_window
    )
)

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
    avg(commute_minutes) as average_commute_minutes,
    avg(trip_distance) as average_commute_distance
from enriched_trips
group by 1, 2, 3, 4, 5, 6, 7, 8, 9
