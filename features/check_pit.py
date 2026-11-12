"""Kiểm tra point-in-time join của Feast: feature lấy ra phải bằng giá trị đã tính sẵn trong gold."""
from pathlib import Path

from feast import FeatureStore

# Feast nhận thẳng câu SQL làm danh sách giao dịch; cột thời gian phải tên là event_timestamp
ENTITY_SQL = """
SELECT t.trans_num, t.card_hash, t.txn_ts AS event_timestamp, f.card_txn_count_24h AS expected
FROM iceberg.silver.transactions t
JOIN iceberg.gold.card_txn_features f ON f.trans_num = t.trans_num
WHERE t.txn_ts < TIMESTAMP '2019-01-08 00:00:00'
"""

# feast apply import mọi file .py trong thư mục này -> chỉ chạy kiểm tra khi gọi trực tiếp bằng python
if __name__ == "__main__":
    store = FeatureStore(repo_path=Path(__file__).parent)
    df = store.get_historical_features(entity_df=ENTITY_SQL, features=["card_velocity:card_txn_count_24h"]).to_df()

    mismatch = df[df["card_txn_count_24h"] != df["expected"]]
    print(f"{len(df):,} giao dịch, {len(mismatch):,} lệch")
    assert len(df) > 0 and mismatch.empty, mismatch.head()
