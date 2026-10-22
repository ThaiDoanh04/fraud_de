import argparse
import os
import time
from datetime import datetime

import psycopg


def replay_offset(first: datetime, current: datetime, speed: float) -> float:
    return (current - first).total_seconds() / speed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speed", type=float, default=60, help="60 = 1 giờ dữ liệu phát trong 1 phút")
    parser.add_argument("--start", default="2020-06-21", help="phát từ thời điểm này (đầu tập test)")
    parser.add_argument("--limit", type=int, help="chỉ phát N giao dịch (để thử)")
    parser.add_argument("--reset", action="store_true", help="xoá sạch bảng transactions trước khi phát")
    args = parser.parse_args()

    dsn = (
        f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@localhost:5432/{os.environ['POSTGRES_DB']}"
    )
    n = 0
    with psycopg.connect(dsn) as read_conn, psycopg.connect(dsn, autocommit=True) as write_conn:
        if args.reset:
            write_conn.execute("TRUNCATE transactions")

        # server-side cursor: Postgres trả dữ liệu dần dần, không kéo cả ~555 nghìn dòng vào RAM
        with read_conn.cursor(name="replay") as cur:
            cur.execute(
                "SELECT trans_num, trans_date_trans_time FROM transactions_history"
                " WHERE trans_date_trans_time >= %s"
                " ORDER BY trans_date_trans_time, trans_num LIMIT %s",
                (args.start, args.limit),
            )
            first, started = None, time.monotonic()
            for trans_num, ts in cur:
                first = first or ts
                # hẹn giờ theo đồng hồ thật, nên thời gian chạy INSERT không làm lịch bị trễ dần
                time.sleep(max(started + replay_offset(first, ts, args.speed) - time.monotonic(), 0))
                write_conn.execute(
                    "INSERT INTO transactions SELECT * FROM transactions_history WHERE trans_num = %s"
                    " ON CONFLICT (trans_num) DO NOTHING",
                    (trans_num,),
                )
                n += 1
                if n % 100 == 0:
                    print(f"{n:,} giao dịch, đang ở {ts}", flush=True)

    print(f"Xong: đã phát {n:,} giao dịch")


if __name__ == "__main__":
    main()
