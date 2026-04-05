with fhv as (
    select
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'fhv' as service_type,
        1 as record_count
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/fhv_tripdata_*.parquet',
        union_by_name = true,
        filename = true
    )
),

fhvhv as (
    select
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'fhvhv' as service_type,
        1 as record_count
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/fhvhv_tripdata_*.parquet',
        union_by_name = true,
        filename = true
    )
),

green as (
    select
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'green' as service_type,
        1 as record_count
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/green_tripdata_*.parquet',
        union_by_name = true,
        filename = true
    )
),

yellow as (
    select
        cast(regexp_extract(filename, '([0-9]{4}-[0-9]{2})', 1) || '-01' as date) as source_month,
        'yellow' as service_type,
        1 as record_count
    from read_parquet(
        '{{ env_var("TLC_DATA_DIR", "data") }}/yellow_tripdata_*.parquet',
        union_by_name = true,
        filename = true
    )
),

all_trips as (
    select * from fhv
    union all
    select * from fhvhv
    union all
    select * from green
    union all
    select * from yellow
)

select *
from all_trips
