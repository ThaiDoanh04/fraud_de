COMPOSE := docker compose --env-file .env -f infra/docker-compose.yml

.PHONY: help up down clean ps logs smoke lint test check

help: ## Liệt kê các lệnh
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-7s %s\n", $$1, $$2}'

.env:
	cp .env.example .env
	@echo "Đã tạo .env từ .env.example. Hãy đổi mật khẩu trong .env"

up: .env ## Bật toàn bộ hệ thống
	$(COMPOSE) up -d --build

down: ## Tắt hệ thống, giữ dữ liệu
	$(COMPOSE) down

clean: ## Tắt và XOÁ toàn bộ dữ liệu
	$(COMPOSE) down -v

ps: ## Trạng thái các service
	$(COMPOSE) ps

logs: ## Xem log, ví dụ: make logs s=kafka
	$(COMPOSE) logs -f --tail 100 $(s)

smoke: ## Kiểm tra toàn bộ hệ thống
	bash infra/scripts/smoke.sh

lint: ## Kiểm tra code Python
	uv run ruff check .

test: ## Chạy test
	uv run pytest

check: lint test ## Chạy mọi thứ mà CI chạy

load-data: ## Nạp dataset Kaggle vào Postgres
	uv run --env-file .env python source/load_dataset.py

replay: ## Phát lại giao dịch, ví dụ: make replay ARGS="--reset --limit 20 --speed 3600"
	uv run --env-file .env python source/replay.py $(ARGS)

connect-register: ## Tạo/cập nhật connector Debezium (chạy lại nhiều lần được)
	uv run --env-file .env python -c "import os; print(os.path.expandvars(open('ingestion/connectors/postgres-txn.json').read()))" \
	| curl -sf -o /dev/null -X PUT -H "Content-Type: application/json" --data @- localhost:8083/connectors/postgres-txn/config
	@sleep 5
	curl -s localhost:8083/connectors/postgres-txn/status

bronze-check: ## So số message Kafka txn.raw với số dòng bronze
	@echo "Kafka (topic:partition:số message):"
	@docker exec fraud-kafka-1 /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server localhost:9092 --topic txn.raw
	@echo "Bronze:"
	@docker exec fraud-trino-1 trino --execute "SELECT count(*) AS rows, count(DISTINCT _kafka_offset) AS distinct_offsets, max(_kafka_offset) + 1 AS last_offset_plus_1 FROM iceberg.bronze.transactions"

dbt-build: ## dbt build: tạo mọi bảng silver + gold và chạy test (cần Trino đang chạy)
	uv run dbt build --project-dir transform --profiles-dir transform

feast-apply: ## Đăng ký feature definitions vào registry Feast
	mkdir -p features/data && cd features && uv run feast apply

feast-check: ## Kiểm tra point-in-time join của Feast khớp với gold
	uv run python features/check_pit.py

train: ## Train LightGBM baseline qua Feast, log + đăng ký model trên MLflow
	uv run python ml/train_baseline.py

feast-materialize: ## Đẩy feature mới nhất của mỗi thẻ từ Iceberg lên online store
	cd features && uv run feast materialize 2019-01-01T00:00:00 2021-01-01T00:00:00
