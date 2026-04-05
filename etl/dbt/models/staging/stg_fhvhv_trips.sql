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
        (pickup_at is null or dropoff_at is null or dropoff_at >= pickup_at)
        and (pickup_location_id is null or pickup_location_id >= 0)
        and (dropoff_location_id is null or dropoff_location_id >= 0)
        and (trip_miles is null or trip_miles >= 0)
        and (trip_time_seconds is null or trip_time_seconds >= 0)
        and (base_passenger_fare is null or base_passenger_fare >= 0)
        and (tolls_amount is null or tolls_amount >= 0)
        and (bcf_amount is null or bcf_amount >= 0)
        and (sales_tax_amount is null or sales_tax_amount >= 0)
        and (congestion_surcharge is null or congestion_surcharge >= 0)
        and (airport_fee is null or airport_fee >= 0)
        and (tip_amount is null or tip_amount >= 0)
        and (driver_pay_amount is null or driver_pay_amount >= 0)
        and (cbd_congestion_fee is null or cbd_congestion_fee >= 0)
)

select *
from validated
