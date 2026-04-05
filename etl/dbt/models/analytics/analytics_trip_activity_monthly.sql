with monthly_metrics as (
    select
        service_type,
        source_month as trip_month,
        count(*) as trip_count,
        avg(trip_distance) as avg_trip_distance,
        sum(total_amount) as gross_amount
    from {{ ref('stg_yellow_trips') }}
    where source_month >= cast('{{ var("analytics_cutoff_month") }}' as date)
    group by 1, 2

    union all

    select
        service_type,
        source_month as trip_month,
        count(*) as trip_count,
        avg(trip_distance) as avg_trip_distance,
        sum(total_amount) as gross_amount
    from {{ ref('stg_green_trips') }}
    where source_month >= cast('{{ var("analytics_cutoff_month") }}' as date)
    group by 1, 2

    union all

    select
        service_type,
        source_month as trip_month,
        count(*) as trip_count,
        avg(trip_miles) as avg_trip_distance,
        sum(
            base_passenger_fare + coalesce(tolls_amount, 0) + coalesce(tip_amount, 0)
        ) as gross_amount
    from {{ ref('stg_fhvhv_trips') }}
    where source_month >= cast('{{ var("analytics_cutoff_month") }}' as date)
    group by 1, 2

    union all

    select
        service_type,
        source_month as trip_month,
        count(*) as trip_count,
        cast(null as double) as avg_trip_distance,
        cast(null as double) as gross_amount
    from {{ ref('stg_fhv_trips') }}
    where source_month >= cast('{{ var("analytics_cutoff_month") }}' as date)
    group by 1, 2
)

select *
from monthly_metrics
order by 2, 1
