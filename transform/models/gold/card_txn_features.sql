{{ config(properties={"partitioning": "ARRAY['month(event_ts)']"}) }}

select
    trans_num,
    card_hash,
    txn_ts as event_ts,
    -- số giao dịch của cùng thẻ trong 24 giờ TRƯỚC giao dịch này, không tính chính nó -> không dùng thông tin tương lai
    -- shortcut: giao dịch cùng thẻ trùng đúng timestamp sẽ đếm lẫn nhau (rất hiếm); cần chính xác tuyệt đối thì thêm trans_num vào thứ tự
    count(*) over (
        partition by card_hash
        order by txn_ts
        range between interval '1' day preceding and current row
    ) - 1 as card_txn_count_24h
from {{ ref('transactions') }}
