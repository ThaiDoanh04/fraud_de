"""Smoke test: gửi 5 message từ máy Mac vào Kafka rồi đọc lại."""

import json
import time
import uuid

from confluent_kafka import Consumer, Producer

BOOTSTRAP = "localhost:9092"
TOPIC = "smoke.test"
N = 5


def main() -> None:
    run_id = uuid.uuid4().hex[:8]

    producer = Producer({"bootstrap.servers": BOOTSTRAP})
    for i in range(N):
        message = {"run_id": run_id, "seq": i, "amt": 100.0 + i, "ts": time.time()}
        producer.produce(TOPIC, key=str(i), value=json.dumps(message))
    not_sent = producer.flush(10)
    if not_sent:
        raise SystemExit(f"FAIL: {not_sent} message chưa gửi được — Kafka có đang chạy ở {BOOTSTRAP}?")
    print(f"Đã gửi {N} message vào topic '{TOPIC}' (run_id={run_id})")

    consumer = Consumer(
        {"bootstrap.servers": BOOTSTRAP, "group.id": f"smoke-{run_id}", "auto.offset.reset": "earliest"}
    )
    consumer.subscribe([TOPIC])
    received = 0
    deadline = time.time() + 20
    while received < N and time.time() < deadline:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        data = json.loads(msg.value())
        if data["run_id"] == run_id:
            received += 1
            print(f"Nhận: partition={msg.partition()} offset={msg.offset()} value={data}")
    consumer.close()

    print("OK: Kafka hoạt động" if received == N else f"FAIL: chỉ nhận {received}/{N} message")


if __name__ == "__main__":
    main()