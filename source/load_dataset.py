import os
from pathlib import Path

import psycopg

RAW = Path("data/raw")
FILES = ["fraudTrain.csv", "fraudTest.csv"]
# Cột đầu tiên của CSV không có tên (index của pandas) -> lưu vào row_id
COLUMNS = (
    "row_id, trans_date_trans_time, cc_num, merchant, category, amt, first, last, gender, "
    "street, city, state, zip, lat, long, city_pop, job, dob, trans_num, unix_time, "
    "merch_lat, merch_long, is_fraud"
)


def main() -> None:
    dsn = (
        f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@localhost:5432/{os.environ['POSTGRES_DB']}"
    )
    with psycopg.connect(dsn) as conn:  # thoát khối with không lỗi = commit, có lỗi = rollback
        conn.execute(Path("source/schema.sql").read_text())
        conn.execute("TRUNCATE transactions_history")
        for name in FILES:
            sql = f"COPY transactions_history ({COLUMNS}) FROM STDIN WITH (FORMAT csv, HEADER true)"
            with (RAW / name).open("rb") as f, conn.cursor().copy(sql) as copy:
                while chunk := f.read(1 << 20):
                    copy.write(chunk)
            print(f"Đã nạp {name}")

        rows, fraud_pct, first_ts, last_ts = conn.execute(
            "SELECT count(*), round(avg(is_fraud) * 100, 3), min(trans_date_trans_time), "
            "max(trans_date_trans_time) FROM transactions_history"
        ).fetchone()
        assert rows > 0, "Không nạp được dòng nào"
        print(f"Tổng {rows:,} giao dịch, gian lận {fraud_pct}%, từ {first_ts} đến {last_ts}")


if __name__ == "__main__":
    main()
