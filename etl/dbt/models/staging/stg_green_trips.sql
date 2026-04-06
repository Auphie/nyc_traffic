with normalized as (
    select  -- noqa: ST06
        cast(vendorid as integer) as vendor_id,
        lpep_pickup_datetime as pickup_at,
        lpep_dropoff_datetime as dropoff_at,
        store_and_fwd_flag,
        cast(ratecodeid as bigint) as rate_code_id,
        cast(pulocationid as integer) as pickup_location_id,
        cast(dolocationid as integer) as dropoff_location_id,
        cast(passenger_count as bigint) as passenger_count,
        cast(trip_distance as double) as trip_distance,
        cast(fare_amount as double) as fare_amount,
        cast(extra as double) as extra_amount,
        cast(mta_tax as double) as mta_tax,
        cast(tip_amount as double) as tip_amount,
        cast(tolls_amount as double) as tolls_amount,
        cast(ehail_fee as double) as ehail_fee,
        cast(improvement_surcharge as double) as improvement_surcharge,
        cast(total_amount as double) as total_amount,
        cast(payment_type as bigint) as payment_type,
        cast(trip_type as bigint) as trip_type,
        cast(congestion_surcharge as double) as congestion_surcharge,
        cast(cbd_congestion_fee as double) as cbd_congestion_fee,
        regexp_extract(filename, '[^/]+$', 0) as source_file_name,
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'green' as service_type
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/green_tripdata_*.parquet',
        union_by_name = true,
        filename = true
    )
),

validated as (
    select *
    from normalized
    where
        DATE(pickup_at) < '2026-02-01'
        and DATE(dropoff_at) < '2026-02-01'
        and dropoff_at >= pickup_at
        and pickup_location_id is not null
        and dropoff_location_id is not null
        and date_diff('day', pickup_at, dropoff_at) < 2
)

select *
from validated
