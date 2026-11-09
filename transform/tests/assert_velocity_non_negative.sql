-- Đếm số giao dịch trước đó không thể âm; âm nghĩa là logic cửa sổ sai
select trans_num, card_txn_count_24h
from {{ ref('card_txn_features') }}
where card_txn_count_24h < 0
