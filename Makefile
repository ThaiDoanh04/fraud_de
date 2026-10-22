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
