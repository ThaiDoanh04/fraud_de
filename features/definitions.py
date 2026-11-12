"""Định nghĩa feature cho Feast (Task 1.3)."""

from datetime import timedelta

from feast import Entity, FeatureView, Field
from feast.infra.offline_stores.contrib.trino_offline_store.trino_source import TrinoSource
from feast.types import Int64
from feast.value_type import ValueType

# Entity = "đối tượng" mà feature mô tả: ở đây là thẻ, nhận diện bằng số thẻ đã băm
card = Entity(name="card", join_keys=["card_hash"], value_type=ValueType.STRING)

card_velocity_source = TrinoSource(
    name="card_txn_features",
    table="gold.card_txn_features",  # catalog iceberg lấy từ feature_store.yaml
    timestamp_field="event_ts",       # feature có hiệu lực từ thời điểm này
)

card_velocity = FeatureView(
    name="card_velocity",
    entities=[card],
    ttl=timedelta(days=1),  # giá trị cũ hơn 1 ngày coi như hết hạn
    schema=[Field(name="card_txn_count_24h", dtype=Int64)],
    source=card_velocity_source,
)
