"""
快速数据导入脚本 — 将 GeoJSON 网格数据导入 PostgreSQL + PostGIS
运行: .venv/bin/python import_data.py
"""

import json
import time
import psycopg2
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"
GRIDS_DIR = DATA_DIR / "grids"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "railwaymap",
    "user": "railway",
    "password": "railway123",
}


def connect():
    return psycopg2.connect(**DB_CONFIG)


def log(msg: str):
    now = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def import_grid_file(path: Path, conn, cur, index: int, total: int) -> dict:
    """导入单个网格 GeoJSON 文件"""
    grid_id = path.stem.replace("grid_", "")
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features", [])

    ways = [f for f in features if f["geometry"]["type"] == "LineString"]
    nodes = [f for f in features if f["geometry"]["type"] == "Point"]

    rail_count = 0
    station_count = 0

    # 批量插入铁路线段
    for feat in ways:
        props = feat.get("properties", {})
        coords = feat["geometry"]["coordinates"]
        if len(coords) < 2:
            continue

        wkt_coords = ", ".join(f"{c[0]:.7f} {c[1]:.7f}" for c in coords)
        wkt = f"LINESTRING({wkt_coords})"

        railway_val = props.get("railway", "rail")
        usage_val = props.get("usage")
        if usage_val and len(usage_val) > 30:
            usage_val = usage_val[:30]

        category = classify_railway(railway_val, props)

        cur.execute("""
            INSERT INTO railway_segments
            (osm_id, name, railway, usage, category, electrified,
             gauge, max_speed, track_count, geom, length_km, source_grid, data_quality)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    ST_GeomFromText(%s,4326),%s,%s,'osm')
        """, (
            props.get("osm_id"),
            (props.get("name", "") or "")[:300],
            railway_val,
            usage_val,
            category,
            props.get("electrified"),
            parse_int(props.get("gauge"), 1435),
            parse_int(props.get("maxspeed")),
            parse_int(props.get("tracks"), 1),
            wkt,
            compute_length(coords),
            grid_id,
        ))
        rail_count += 1

    # 批量插入车站
    for feat in nodes:
        props = feat.get("properties", {})
        coords = feat["geometry"]["coordinates"]
        if len(coords) < 2:
            continue

        name = props.get("name:zh") or props.get("name", "")
        if not name:
            continue

        wkt = f"POINT({coords[0]:.7f} {coords[1]:.7f})"

        cur.execute("""
            INSERT INTO stations
            (osm_id, name, railway, category, passenger,
             geom, source_grid, data_quality)
            VALUES (%s,%s,%s,%s,%s,
                    ST_GeomFromText(%s,4326),%s,'osm')
        """, (
            props.get("osm_id"),
            name[:200],
            props.get("railway"),
            classify_station(props),
            props.get("railway") not in ("yard", "depot", "signal_box"),
            wkt,
            grid_id,
        ))
        station_count += 1

    pct = index * 100 // total
    log(f"[{index}/{total}] ({pct}%) {grid_id}: 线{rail_count} 站{station_count}")
    return {"rail": rail_count, "station": station_count}


def classify_railway(railway: str, props: dict) -> str:
    if railway == "subway":
        return "subway"
    highspeed = props.get("highspeed", "")
    if highspeed in ("yes", "high_speed"):
        return "high_speed"
    usage = props.get("usage", "")
    if usage == "freight":
        return "freight_rail"
    if usage == "main":
        return "passenger_rail"
    if usage in ("industrial", "military", "tourism"):
        return "other_rail"
    return "conventional"


def classify_station(props: dict) -> str:
    rw = props.get("railway", "")
    if rw == "yard":
        return "medium_yard"
    if rw == "depot":
        return "emu_depot"
    if rw == "signal_box":
        return "signal_station"
    if rw == "halt":
        return "small_passenger"
    return "small_passenger"


def parse_int(val, default=None):
    if val is None:
        return default
    try:
        return int(str(val).replace("mm", "").strip())
    except (ValueError, TypeError):
        return default


def compute_length(coords: list) -> float:
    import math
    total = 0.0
    for i in range(1, len(coords)):
        a, b = coords[i - 1], coords[i]
        dlat = math.radians(b[1] - a[1])
        dlon = math.radians(b[0] - a[0])
        lat1 = math.radians(a[1])
        lat2 = math.radians(b[1])
        x = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        total += 6371000.0 * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))
    return total / 1000.0


def main():
    log("========== 开始导入 ==========")

    files = sorted(GRIDS_DIR.glob("grid_r*_c*.geojson"))
    log(f"待导入: {len(files)} 个文件")

    conn = connect()
    cur = conn.cursor()

    start = time.time()
    total_rail = 0
    total_station = 0

    for i, file in enumerate(files, 1):
        counts = import_grid_file(file, conn, cur, i, len(files))
        total_rail += counts["rail"]
        total_station += counts["station"]

        if i % 50 == 0:
            conn.commit()
            elapsed = time.time() - start
            log(f"--- 已提交 {i}/{len(files)} | 累计 线{total_rail} 站{total_station} | {elapsed/60:.0f}min ---")

    conn.commit()
    conn.close()

    elapsed = time.time() - start
    log(f"========== 导入完成 ==========")
    log(f"总文件: {len(files)}, 铁路线: {total_rail}, 车站: {total_station}")
    log(f"耗时: {elapsed/60:.1f} 分钟")


if __name__ == "__main__":
    try:
        import psycopg2
    except ImportError:
        print("请安装 psycopg2: .venv/bin/pip install psycopg2-binary")
        raise
    main()
