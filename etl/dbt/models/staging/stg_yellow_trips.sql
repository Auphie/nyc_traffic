with normalized as (
    select  -- noqa: ST06
        cast(vendorid as integer) as vendor_id,
        tpep_pickup_datetime as pickup_at,
        tpep_dropoff_datetime as dropoff_at,
        cast(passenger_count as bigint) as passenger_count,
        cast(trip_distance as double) as trip_distance,
        cast(ratecodeid as bigint) as rate_code_id,
        store_and_fwd_flag,
        cast(pulocationid as integer) as pickup_location_id,
        cast(dolocationid as integer) as dropoff_location_id,
        cast(payment_type as bigint) as payment_type,
        cast(fare_amount as double) as fare_amount,
        cast(extra as double) as extra_amount,
        cast(mta_tax as double) as mta_tax,
        cast(tip_amount as double) as tip_amount,
        cast(tolls_amount as double) as tolls_amount,
        cast(improvement_surcharge as double) as improvement_surcharge,
        cast(total_amount as double) as total_amount,
        cast(congestion_surcharge as double) as congestion_surcharge,
        cast(airport_fee as double) as airport_fee,
        cast(cbd_congestion_fee as double) as cbd_congestion_fee,
        regexp_extract(filename, '[^/]+$', 0) as source_file_name,
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'yellow' as service_type
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/yellow_tripdata_*.parquet',
        union_by_name = true,
        filename = true
    )
),

validated as (
    select *
    from normalized
    where
        pickup_at is not null
        and dropoff_at is not null
        and dropoff_at >= pickup_at
        and pickup_location_id is not null
        and dropoff_location_id is not null
)

select *
from validated
