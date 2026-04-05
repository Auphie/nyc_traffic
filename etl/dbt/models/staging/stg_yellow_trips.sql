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
        (pickup_at is null or dropoff_at is null or dropoff_at >= pickup_at)
        and (vendor_id is null or vendor_id >= 0)
        and (passenger_count is null or passenger_count >= 0)
        and (trip_distance is null or trip_distance >= 0)
        and (rate_code_id is null or rate_code_id >= 0)
        and (pickup_location_id is null or pickup_location_id >= 0)
        and (dropoff_location_id is null or dropoff_location_id >= 0)
        and (payment_type is null or payment_type >= 0)
        and (fare_amount is null or fare_amount >= 0)
        and (extra_amount is null or extra_amount >= 0)
        and (mta_tax is null or mta_tax >= 0)
        and (tip_amount is null or tip_amount >= 0)
        and (tolls_amount is null or tolls_amount >= 0)
        and (improvement_surcharge is null or improvement_surcharge >= 0)
        and (total_amount is null or total_amount >= 0)
        and (congestion_surcharge is null or congestion_surcharge >= 0)
        and (airport_fee is null or airport_fee >= 0)
        and (cbd_congestion_fee is null or cbd_congestion_fee >= 0)
)

select *
from validated
