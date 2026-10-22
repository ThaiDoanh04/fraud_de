"""Bảo vệ cấu hình CDC: PII phải được băm hoặc loại bỏ, không ghi cứng secret."""

import json
from pathlib import Path

CONFIG = json.loads(
    (Path(__file__).resolve().parents[1] / "ingestion" / "connectors" / "postgres-txn.json").read_text()
)


def test_cc_num_is_hashed_with_salt_from_env():
    assert CONFIG.get("column.mask.hash.SHA-256.with.salt.${PII_SALT}") == "public.transactions.cc_num"


def test_name_and_street_are_dropped():
    excluded = CONFIG["column.exclude.list"].split(",")
    for col in ("first", "last", "street"):
        assert f"public.transactions.{col}" in excluded


def test_only_live_table_is_captured():
    assert CONFIG["table.include.list"] == "public.transactions"


def test_no_hardcoded_credentials():
    for key in ("database.user", "database.password", "database.dbname"):
        assert CONFIG[key].startswith("${"), f"{key} phải lấy từ .env"


def test_events_go_to_txn_raw():
    assert CONFIG["transforms.route.replacement"] == "txn.raw"
