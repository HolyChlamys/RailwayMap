"""
车次数据导入脚本 — WSL 运行
读取 data/trains/{train_no}.json → PostgreSQL

用法: .venv/bin/python import_trains.py
前提: 已将 Windows 爬虫输出的 data/trains/ 复制到 railway-scripts/data/trains/
"""

import json
import time
import psycopg2
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"
TRAINS_DIR = DATA_DIR / "trains"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "railwaymap",
    "user": "railway",
    "password": "railway123",
}


def log(msg: str):
    print(f"[{datetime.now():%m-%d %H:%M:%S}] {msg}", flush=True)


def parse_time(val):
    """解析时间字符串 '06:30' → 数据库 TIME"""
    if not val or val in ("----", "--", ""):
        return None
    val = str(val).strip()
    try:
        parts = val.split(":")
        if len(parts) >= 2:
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h < 24 and 0 <= m < 60:
                return f"{h:02d}:{m:02d}:00"
    except (ValueError, IndexError):
        pass
    return None


def import_file(filepath: Path, cur, index: int, total: int):
    """导入单个车次 JSON 文件"""
    train_no = filepath.stem

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"[{index}/{total}] {train_no}: JSON 解析失败 ({e})")
        return 0, 0, 0

    if not data or not data.get("stops"):
        return 0, 0, 0

    # 1. 插入 train_routes
    depart = parse_time(data.get("depart_time"))
    arrive = parse_time(data.get("arrive_time"))

    cur.execute("""
        INSERT INTO train_routes
        (train_no, train_type, depart_station, arrive_station,
         depart_time, arrive_time, is_valid, data_updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,TRUE,NOW())
        ON CONFLICT (train_no) DO UPDATE SET
            depart_station = EXCLUDED.depart_station,
            arrive_station = EXCLUDED.arrive_station,
            depart_time = EXCLUDED.depart_time,
            arrive_time = EXCLUDED.arrive_time,
            data_updated_at = NOW()
    """, (
        train_no,
        data.get("train_type", train_no[0]),
        data.get("depart_station", "")[:200],
        data.get("arrive_station", "")[:200],
        depart,
        arrive,
    ))

    # 2. 插入 train_stops
    stops = data.get("stops", [])
    stops_count = 0
    for stop in stops:
        station_name = (stop.get("station_name") or "")[:200]
        if not station_name:
            continue

        cur.execute("""
            INSERT INTO train_stops
            (train_no, seq, station_name, arrive_time, depart_time, stay_min)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            train_no,
            stop.get("seq"),
            station_name,
            parse_time(stop.get("arrive_time")),
            parse_time(stop.get("depart_time")),
            parse_int(stop.get("stay_min")),
        ))
        stops_count += 1

    # 3. 插入 train_fares (全区间票价)
    fares = data.get("fares", {})
    if fares:
        cur.execute("""
            INSERT INTO train_fares
            (train_no, from_station, to_station,
             price_business, price_first, price_second,
             price_soft_sleeper_up, price_soft_sleeper_down,
             price_hard_sleeper_up, price_hard_sleeper_mid,
             price_hard_sleeper_down, price_hard_seat, price_no_seat)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (train_no, from_station, to_station)
            DO UPDATE SET price_second = EXCLUDED.price_second
        """, (
            train_no,
            data.get("depart_station", "")[:200],
            data.get("arrive_station", "")[:200],
            fares.get("price_business"),
            fares.get("price_first"),
            fares.get("price_second"),
            fares.get("price_soft_sleeper_up"),
            fares.get("price_soft_sleeper_down"),
            fares.get("price_hard_sleeper_up"),
            fares.get("price_hard_sleeper_mid"),
            fares.get("price_hard_sleeper_down"),
            fares.get("price_hard_seat"),
            fares.get("price_no_seat"),
        ))

    pct = index * 100 // total
    log(f"[{index}/{total}] ({pct}%) {train_no}: {stops_count}站")
    return 1, stops_count, 1 if fares else 0


def parse_int(val):
    if not val:
        return None
    try:
        return int(str(val).replace("分钟", "").replace("分", "").strip())
    except ValueError:
        return None


def main():
    log("========== 车次数据导入 ==========")

    if not TRAINS_DIR.exists():
        log(f"数据目录不存在: {TRAINS_DIR}")
        log("请先将 Windows 爬虫输出的 data/trains/ 复制到此目录")
        return

    files = sorted(TRAINS_DIR.glob("*.json"))
    log(f"待导入: {len(files)} 个文件")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    start = time.time()
    total_routes = 0
    total_stops = 0
    total_fares = 0

    for i, f in enumerate(files, 1):
        r, s, fa = import_file(f, cur, i, len(files))
        total_routes += r
        total_stops += s
        total_fares += fa

        if i % 500 == 0:
            conn.commit()
            elapsed = time.time() - start
            log(f"--- 已提交 {i}/{len(files)} | {elapsed/60:.0f}min ---")

    conn.commit()
    conn.close()

    elapsed = time.time() - start
    log(f"========== 导入完成 ==========")
    log(f"车次: {total_routes}, 停站: {total_stops}, 票价: {total_fares}")
    log(f"耗时: {elapsed/60:.1f} 分钟")


if __name__ == "__main__":
    main()
