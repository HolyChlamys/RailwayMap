"""
时刻表与票价爬虫
数据源: liecheba.com (服务端渲染 HTML)

特性:
  - 从列车列表页获取全国车次
  - 逐车次爬取途经站 + 时刻表 + 票价
  - 请求间隔 >= 1.5s
  - 断点续传 (SQLite 记录进度)
  - 增量更新 (检查 updated_at)
"""

import json
import re
import sqlite3
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "train_cache.db"
BASE_URL = "https://www.liecheba.com"
MIN_INTERVAL_SEC = 1.5

# 车次类型前缀
TRAIN_PREFIXES = ["G", "D", "C", "Z", "T", "K", "Y", "S"]


class ScheduleParser(HTMLParser):
    """简化的 HTML 解析器 — 提取途经站时间表"""

    def __init__(self):
        super().__init__()
        self.stops = []
        self._current_stop = {}
        self._in_table = False
        self._in_row = False
        self._cell_idx = 0
        self._text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "table" and "schedule" in cls.lower():
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._current_stop = {}
            self._cell_idx = 0
        elif tag == "td" and self._in_row:
            self._text = ""

    def handle_endtag(self, tag):
        if tag == "tr" and self._in_row and self._current_stop:
            self.stops.append(self._current_stop)
            self._current_stop = {}
            self._in_row = False
        elif tag == "td" and self._in_row:
            text = self._text.strip()
            self._map_cell(text)
            self._cell_idx += 1
        elif tag == "table" and self._in_table:
            self._in_table = False

    def handle_data(self, data):
        if self._in_row:
            self._text += data

    def _map_cell(self, text):
        """将表格列映射为 stop 字段"""
        if self._cell_idx == 0:
            self._current_stop["seq"] = text
        elif self._cell_idx == 1:
            self._current_stop["station_name"] = text
        elif self._cell_idx == 2:
            self._current_stop["arrive_time"] = text
        elif self._cell_idx == 3:
            self._current_stop["depart_time"] = text
        elif self._cell_idx == 4:
            self._current_stop["stay_min"] = text


class FareParser(HTMLParser):
    """简化的票价表格解析器"""

    def __init__(self):
        super().__init__()
        self.fares = {}
        self._in_fare_table = False
        self._current_row = []
        self._text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "table" and ("fare" in cls.lower() or "price" in cls.lower()):
            self._in_fare_table = True
        elif tag == "tr" and self._in_fare_table:
            self._current_row = []
        elif tag == "td" and self._in_fare_table:
            self._text = ""

    def handle_endtag(self, tag):
        if tag == "td" and self._in_fare_table:
            self._current_row.append(self._text.strip())
        elif tag == "tr" and self._in_fare_table and len(self._current_row) >= 2:
            seat_type = self._current_row[0]
            try:
                price = float(self._current_row[1].replace("¥", "").replace(",", ""))
                self.fares[self._normalize_seat(seat_type)] = price
            except ValueError:
                pass

    def handle_data(self, data):
        if self._in_fare_table:
            self._text += data

    def _normalize_seat(self, seat: str) -> str:
        seat = seat.lower()
        if "商务" in seat or "特等" in seat:
            return "price_business"
        if "一等" in seat:
            return "price_first"
        if "二等" in seat:
            return "price_second"
        if "软卧上" in seat:
            return "price_soft_sleeper_up"
        if "软卧下" in seat:
            return "price_soft_sleeper_down"
        if "硬卧上" in seat:
            return "price_hard_sleeper_up"
        if "硬卧中" in seat:
            return "price_hard_sleeper_mid"
        if "硬卧下" in seat:
            return "price_hard_sleeper_down"
        if "硬座" in seat:
            return "price_hard_seat"
        if "无座" in seat:
            return "price_no_seat"
        return seat.replace(" ", "_")


def init_db():
    """初始化本地 SQLite 缓存数据库"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS train_cache (
            train_no TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            is_valid INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crawl_progress (
            prefix TEXT PRIMARY KEY,
            last_page INTEGER DEFAULT 1,
            updated_at TEXT
        )
    """)
    conn.commit()
    return conn


def fetch_url(url: str, timeout: int = 30) -> str | None:
    """HTTP GET 请求"""
    try:
        resp = requests.get(url, timeout=timeout, verify=False, headers={
            "User-Agent": "Mozilla/5.0 (compatible; RailwayMap/1.0)"
        })
        if resp.status_code == 200:
            return resp.text
        print(f"[CRAWLER] HTTP {resp.status_code}: {url}")
    except Exception as e:
        print(f"[CRAWLER] 请求失败: {url} — {e}")
    return None


def crawl_train_list(prefix: str, page: int = 1) -> list[str]:
    """
    从 liecheba.com 车次列表页获取车次号。
    返回 train_no 列表。
    """
    url = f"{BASE_URL}/train/list/{prefix}?page={page}"
    html = fetch_url(url)
    if not html:
        return []

    # 提取 href="/XX1234/" 格式的车次链接
    pattern = rf'href="/{re.escape(prefix)}\d+/\?(.*?)"'
    matches = re.findall(pattern, html)
    train_nos = list(set(re.findall(rf'({re.escape(prefix)}\d+)', html)))

    print(f"[CRAWLER] {prefix} 字头 第{page}页: {len(train_nos)} 个车次")
    return train_nos


def crawl_train_schedule(train_no: str) -> dict | None:
    """
    爬取单趟车次的途经站时刻表 + 票价。
    返回: {train_no, train_type, depart_station, arrive_station,
           depart_time, arrive_time, stops[], fares{}}
    """
    url = f"{BASE_URL}/{train_no}"
    html = fetch_url(url)
    if not html:
        return None

    # 解析时刻表
    sched_parser = ScheduleParser()
    sched_parser.feed(html)

    # 解析票价
    fare_parser = FareParser()
    fare_parser.feed(html)

    if not sched_parser.stops:
        print(f"[CRAWLER] {train_no}: 未找到时刻表数据")
        return None

    # 提取车次基本信息
    first_stop = sched_parser.stops[0]
    last_stop = sched_parser.stops[-1]

    return {
        "train_no": train_no,
        "train_type": train_no[0],
        "depart_station": first_stop.get("station_name", ""),
        "arrive_station": last_stop.get("station_name", ""),
        "depart_time": first_stop.get("depart_time", ""),
        "arrive_time": last_stop.get("arrive_time", ""),
        "stops": sched_parser.stops,
        "fares": fare_parser.fares,
        "fetched_at": datetime.now().isoformat()
    }


def save_to_json(train_data: dict):
    """将爬取结果保存为 JSON 文件"""
    train_no = train_data["train_no"]
    prefix = train_no[0]
    prefix_dir = DATA_DIR / "trains" / prefix
    prefix_dir.mkdir(parents=True, exist_ok=True)

    output = prefix_dir / f"{train_no}.json"
    output.write_text(
        json.dumps(train_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def save_to_db(conn: sqlite3.Connection, train_data: dict):
    """缓存到 SQLite"""
    conn.execute(
        "INSERT OR REPLACE INTO train_cache (train_no, data, fetched_at, is_valid) VALUES (?, ?, ?, 1)",
        (train_data["train_no"], json.dumps(train_data, ensure_ascii=False),
         train_data["fetched_at"])
    )
    conn.commit()


def run_incremental(conn: sqlite3.Connection):
    """
    增量更新: 检查已缓存车次的 fetched_at，
    仅重新爬取超过 24h 未更新的车次。
    """
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    stale = conn.execute(
        "SELECT train_no FROM train_cache WHERE fetched_at < ?",
        (cutoff,)
    ).fetchall()

    print(f"[CRAWLER] 需要更新 {len(stale)} 个过期车次")
    _crawl_list(conn, [row[0] for row in stale])


def run_full(conn: sqlite3.Connection):
    """
    全量爬取: 从所有车次类型前缀的第 1 页开始，
    逐页获取车次列表，然后逐车次爬取详情。
    """
    all_train_nos = []

    for prefix in TRAIN_PREFIXES:
        print(f"[CRAWLER] ===== {prefix} 字头 =====")
        page = 1
        while True:
            train_nos = crawl_train_list(prefix, page)
            if not train_nos:
                break
            all_train_nos.extend(train_nos)
            page += 1
            time.sleep(MIN_INTERVAL_SEC)

    print(f"[CRAWLER] 共发现 {len(all_train_nos)} 个车次")
    _crawl_list(conn, all_train_nos)


def _crawl_list(conn: sqlite3.Connection, train_nos: list[str]):
    """爬取车次列表的详情"""
    total = len(train_nos)
    success = 0
    failed = 0
    last_request = 0.0

    for i, train_no in enumerate(train_nos, 1):
        # 检查缓存
        cached = conn.execute(
            "SELECT data FROM train_cache WHERE train_no = ? AND is_valid = 1",
            (train_no,)
        ).fetchone()

        if cached:
            print(f"[CRAWLER] [{i}/{total}] {train_no}: 已缓存, 跳过")
            success += 1
            continue

        # 请求间隔
        elapsed = time.time() - last_request
        if elapsed < MIN_INTERVAL_SEC:
            time.sleep(MIN_INTERVAL_SEC - elapsed)

        train_data = crawl_train_schedule(train_no)
        last_request = time.time()

        if train_data:
            save_to_json(train_data)
            save_to_db(conn, train_data)
            stops_count = len(train_data.get("stops", []))
            print(f"[CRAWLER] [{i}/{total}] {train_no}: {stops_count} 站, "
                  f"{len(train_data.get('fares', {}))} 种票价 ✓")
            success += 1
        else:
            # 标记为无效车次（可能已停运）
            conn.execute(
                "INSERT OR REPLACE INTO train_cache (train_no, data, fetched_at, is_valid) VALUES (?, '{}', ?, 0)",
                (train_no, datetime.now().isoformat())
            )
            conn.commit()
            print(f"[CRAWLER] [{i}/{total}] {train_no}: 爬取失败 ✗")
            failed += 1

    print(f"[CRAWLER] 完成: 成功 {success}, 失败 {failed}, 总计 {total}")


def run(mode: str = "incremental"):
    """主入口
    Args:
        mode: "full" 全量爬取 / "incremental" 增量更新
    """
    conn = init_db()
    if mode == "full":
        run_full(conn)
    else:
        run_incremental(conn)
    conn.close()


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "incremental"
    print(f"[CRAWLER] 模式: {mode}")
    run(mode)
