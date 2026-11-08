"""Spark Structured Streaming: Kafka txn.raw (Avro/Confluent) -> Iceberg bronze.transactions (Task 1.2)."""

import json
import os
import time
import urllib.request

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.avro.functions import from_avro

KAFKA = os.environ.get("KAFKA_BOOTSTRAP", "kafka:29092")
REGISTRY = os.environ.get("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
TOPIC = "txn.raw"
TABLE = "iceberg.bronze.transactions"


def latest_schema(subject: str) -> str:
    """Lấy schema Avro mới nhất; chờ nếu connector Debezium chưa đăng ký schema."""
    while True:
        try:
            with urllib.request.urlopen(f"{REGISTRY}/subjects/{subject}/versions/latest") as resp:
                return json.load(resp)["schema"]
        except OSError as err:
            print(f"Chưa có schema {subject} ({err}), thử lại sau 10 giây...", flush=True)
            time.sleep(10)


def main() -> None:
    spark = (
        SparkSession.builder.appName("bronze_transactions")
        .config("spark.sql.session.timeZone", "UTC")  # giữ nguyên giờ gốc của giao dịch, không cộng +7
        .getOrCreate()
    )

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    # Confluent wire format = 1 byte magic + 4 byte schema id + dữ liệu Avro -> bỏ 5 byte đầu
    # shortcut: giải mã mọi message bằng schema mới nhất;
    # nếu schema đổi không tương thích ngược thì phải đọc theo schema id
    payload = F.expr("substring(value, 6, length(value) - 5)")
    bronze = raw.select(
        from_avro(payload, latest_schema(f"{TOPIC}-value")).alias("t"),
        F.col("partition").alias("_kafka_partition"),
        F.col("offset").alias("_kafka_offset"),
        F.col("timestamp").alias("_kafka_ts"),
        F.current_timestamp().alias("_ingested_at"),
    ).select("t.*", "_kafka_partition", "_kafka_offset", "_kafka_ts", "_ingested_at")

    spark.sql("CREATE NAMESPACE IF NOT EXISTS iceberg.bronze")
    if not spark.catalog.tableExists(TABLE):
        # chia partition theo ngày giao dịch: truy vấn lọc theo ngày chỉ đọc đúng thư mục ngày đó
        spark.createDataFrame([], bronze.schema).writeTo(TABLE).partitionedBy(F.days("trans_date_trans_time")).create()

    (
        bronze.writeStream.outputMode("append")
        .trigger(processingTime="30 seconds")
        .option("checkpointLocation", "/checkpoints/bronze_transactions")
        .toTable(TABLE)
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
