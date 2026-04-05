with normalized as (
    select  -- noqa: ST06
        hvfhs_license_num,
        dispatching_base_num,
        originating_base_num,
        request_datetime as requested_at,
        on_scene_datetime as on_scene_at,
        pickup_datetime as pickup_at,
        dropoff_datetime as dropoff_at,
        cast(pulocationid as integer) as pickup_location_id,
        cast(dolocationid as integer) as dropoff_location_id,
        cast(trip_miles as double) as trip_miles,
        cast(trip_time as bigint) as trip_time_seconds,
        cast(base_passenger_fare as double) as base_passenger_fare,
        cast(tolls as double) as tolls_amount,
        cast(bcf as double) as bcf_amount,
        cast(sales_tax as double) as sales_tax_amount,
        cast(congestion_surcharge as double) as congestion_surcharge,
        cast(airport_fee as double) as airport_fee,
        cast(tips as double) as tip_amount,
        cast(driver_pay as double) as driver_pay_amount,
        shared_request_flag,
        shared_match_flag,
        access_a_ride_flag,
        wav_request_flag,
        wav_match_flag,
        cast(cbd_congestion_fee as double) as cbd_congestion_fee,
        regexp_extract(filename, '[^/]+$', 0) as source_file_name,
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'fhvhv' as service_type
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/fhvhv_tripdata_*.parquet',
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
