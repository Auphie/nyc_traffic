with normalized as (
    select  -- noqa: ST06
        dispatching_base_num,
        affiliated_base_number,
        pickup_datetime as pickup_at,
        dropoff_datetime as dropoff_at,
        cast(pulocationid as bigint) as pickup_location_id,
        cast(dolocationid as bigint) as dropoff_location_id,
        cast(sr_flag as bigint) as sr_flag,
        regexp_extract(filename, '[^/]+$', 0) as source_file_name,
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'fhv' as service_type
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/fhv_tripdata_*.parquet',
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
        and (sr_flag is null or sr_flag >= 0)
)

select *
from validated
