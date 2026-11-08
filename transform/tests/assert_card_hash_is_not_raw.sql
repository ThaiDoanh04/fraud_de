-- Fail nếu card_hash trông giống số thẻ thật (12-19 chữ số) -> nghĩa là băm ở Debezium đã bị tắt
select trans_num, card_hash
from {{ ref('transactions') }}
where regexp_like(card_hash, '^[0-9]{12,19}$')
