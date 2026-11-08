-- shortcut: build lại toàn bộ từ bronze mỗi lần chạy; khi bronze lên hàng chục triệu dòng thì chuyển sang incremental merge theo trans_num
{{ config(properties={"partitioning": "ARRAY['day(txn_ts)']"}) }}

with deduped as (
    -- bronze có thể có trùng (Debezium gửi lại sau sự cố); giữ bản ghi Kafka mới nhất của mỗi giao dịch
    select
        *,
        row_number() over (partition by trans_num order by _kafka_offset desc) as rn
    from {{ source('bronze', 'transactions') }}
)

select
    trans_num,
    -- Spark lưu thời gian dạng có múi giờ (UTC); dữ liệu gốc là giờ địa phương không múi giờ -> bỏ múi giờ
    cast(trans_date_trans_time at time zone 'UTC' as timestamp(6)) as txn_ts,
    cc_num                          as card_hash,
    merchant,
    category,
    cast(amt as decimal(12, 2))     as amount,
    gender,
    city,
    state,
    zip,
    lat                             as cust_lat,
    long                            as cust_long,
    city_pop,
    job,
    dob,
    merch_lat,
    merch_long,
    cast(is_fraud as integer)       as is_fraud,
    _ingested_at                    as ingested_at
from deduped
where rn = 1
