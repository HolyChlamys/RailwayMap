"""
列车时刻表爬虫 — 纯 HTTP 请求（无需浏览器/Playwright）
- liecheba.com 搜索页和详情页均为 SSR，直接解析 HTML
- 搜索: /search/train/?number={prefix}{digit} → 获取车次列表
- 详情: /{train_no}.html → 获取时刻表 + 票价
- 输出: data/trains/{train_no}.json
- 断点续传，进度日志

环境: Python 3 + requests (已在 venv 中安装)
运行: .venv/bin/python train_crawler_playwright.py
      或在 Windows 上: python train_crawler_playwright.py (需先 pip install requests)
"""

import json
import re
import time
import sys
import requests
from pathlib import Path
from datetime import datetime

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent / "data"
TRAINS_DIR = DATA_DIR / "trains"
PROGRESS_FILE = DATA_DIR / "train_progress.json"
FAILED_FILE = DATA_DIR / "train_failed.json"

BASE_URL = "https://www.liecheba.com"
MIN_INTERVAL_SEC = 1.5

TRAIN_PREFIXES = ["G", "D", "C", "Z", "T", "K", "Y", "S"]
SEARCH_DIGITS = list(range(10))  # 0-9


def log(msg: str):
    now = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def http_get(path: str) -> str | None:
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=20, verify=False, headers={
            "User-Agent": "Mozilla/5.0 (compatible; RailwayMap/1.0)"
        })
        if resp.status_code != 200:
            return None
        return resp.text
    except Exception as e:
        log(f"请求失败 {url}: {e}")
        return None


# ============================================================
# 阶段一: 从搜索页获取车次列表
# ============================================================

def search_train_numbers(prefix: str, digit: int) -> list[dict]:
    """
    搜索 /search/train/?number={prefix}{digit}
    返回 [{train_no, train_type, depart_station, depart_time,
            arrive_station, arrive_time, duration}, ...]
    """
    path = f"/search/train/?number={prefix.lower()}{digit}"
    html = http_get(path)
    if not html:
        return []

    tbody_match = re.search(r'<tbody>(.*?)</tbody>', html, re.DOTALL)
    if not tbody_match:
        return []

    results = []
    rows = re.findall(r'<tr>(.*?)</tr>', tbody_match.group(1), re.DOTALL)

    for row in rows:
        train_match = re.search(r'data-value="([GCDZTKYS]\d+)"', row)
        if not train_match:
            continue
        train_no = train_match.group(1).upper()

        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        cell_texts = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

        if len(cell_texts) < 7:
            continue

        arrive_raw = cell_texts[5] if len(cell_texts) > 5 else ""
        arrive_time = re.sub(r'[^\d:]', '', arrive_raw)[:5] if arrive_raw else ""

        results.append({
            "train_no": train_no,
            "train_type": cell_texts[1] if len(cell_texts) > 1 else "",
            "depart_station": cell_texts[2] if len(cell_texts) > 2 else "",
            "depart_time": cell_texts[3] if len(cell_texts) > 3 else "",
            "arrive_station": cell_texts[4] if len(cell_texts) > 4 else "",
            "arrive_time": arrive_time,
            "duration": cell_texts[6] if len(cell_texts) > 6 else "",
        })

    return results


def crawl_all_train_lists() -> tuple[list[str], dict]:
    """返回 (车次号列表, {车次号: 基本信息})"""
    all_trains = {}
    total_queries = len(TRAIN_PREFIXES) * len(SEARCH_DIGITS)
    q = 0

    for prefix in TRAIN_PREFIXES:
        for digit in SEARCH_DIGITS:
            q += 1
            results = search_train_numbers(prefix, digit)

            for r in results:
                no = r["train_no"]
                if no not in all_trains:
                    all_trains[no] = r

            if results:
                log(f"  [{q}/{total_queries}] {prefix}{digit}: {len(results)}个 "
                    f"(累计 {len(all_trains)})")
            time.sleep(1)

    log(f"共发现 {len(all_trains)} 个唯一车次")
    return sorted(all_trains.keys()), all_trains


# ============================================================
# 阶段二: 抓取车次详情
# ============================================================

def parse_detail_page(html: str, train_no: str) -> dict | None:
    """解析车次详情页 HTML，提取时刻表 + 票价"""

    # --- 提取时刻表 ---
    stops = []
    inner_match = re.search(
        r'<div class="table-inner">(.*?)</div>',
        html, re.DOTALL
    )
    if not inner_match:
        return None

    rows = re.findall(r'<tr>(.*?)</tr>', inner_match.group(1), re.DOTALL)
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        cell_texts = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

        if len(cell_texts) < 5:
            continue
        if not cell_texts[0].strip().isdigit():
            continue

        arr = re.sub(r'[^\d:]', '', cell_texts[3]) if len(cell_texts) > 3 else ""
        dep = re.sub(r'[^\d:]', '', cell_texts[4]) if len(cell_texts) > 4 else ""
        stay = re.sub(r'[^\d]', '', cell_texts[6]) if len(cell_texts) > 6 else ""

        stops.append({
            "seq": int(cell_texts[0]),
            "station_name": cell_texts[1] if len(cell_texts) > 1 else "",
            "arrive_time": arr,
            "depart_time": dep,
            "stay_min": stay,
        })

    if not stops:
        return None

    # --- 提取票价 ---
    fares = {}
    fare_match = re.search(
        r'<div class="group-right">(.*?)</div>\s*</div>',
        html, re.DOTALL
    )
    if fare_match:
        fare_rows = re.findall(r'<tr>(.*?)</tr>', fare_match.group(1), re.DOTALL)
        for row in fare_rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            texts = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            # 遍历相邻单元格对，找"席别+价格"组合
            for j in range(len(texts) - 1):
                s = texts[j]
                if not s:
                    continue
                try:
                    price = float(texts[j + 1])
                except (ValueError, IndexError):
                    continue
                _map_fare(fares, s, price)

    return {
        "train_no": train_no,
        "train_type": train_no[0],
        "depart_station": stops[0]["station_name"],
        "arrive_station": stops[-1]["station_name"],
        "depart_time": stops[0].get("depart_time", ""),
        "arrive_time": stops[-1].get("arrive_time", ""),
        "stops": stops,
        "fares": fares,
        "fetched_at": datetime.now().isoformat(),
    }


def _map_fare(fares: dict, seat: str, price: float):
    """将席别名称映射到 fares 字典"""
    s = seat.strip()
    if "一等座" in s:
        fares["price_first"] = price
    elif "二等座" in s:
        fares["price_second"] = price
    elif "商务座" in s or "特等座" in s:
        fares["price_business"] = price
    elif "软卧上" in s:
        fares["price_soft_sleeper_up"] = price
    elif "软卧下" in s:
        fares["price_soft_sleeper_down"] = price
    elif "硬卧上" in s:
        fares["price_hard_sleeper_up"] = price
    elif "硬卧中" in s:
        fares["price_hard_sleeper_mid"] = price
    elif "硬卧下" in s:
        fares["price_hard_sleeper_down"] = price
    elif "硬座" in s:
        fares["price_hard_seat"] = price
    elif "无座" in s:
        fares["price_no_seat"] = price


# ============================================================
# 进度管理
# ============================================================

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {"completed": [], "failed": [], "train_list": [], "train_info": {}}


def save_progress(data: dict):
    PROGRESS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# 主流程
# ============================================================

def main():
    TRAINS_DIR.mkdir(parents=True, exist_ok=True)

    log("========== 列车爬虫启动 (纯HTTP/SSR) ==========")

    progress = load_progress()
    completed = set(progress.get("completed", []))
    failed = set(progress.get("failed", []))

    # 阶段一: 搜索收集车次列表
    train_list = progress.get("train_list", [])
    if not train_list:
        log("阶段一: 搜索车次列表 (G/D/C/Z/T/K/Y/S × 0-9)")
        train_list, train_info = crawl_all_train_lists()
        progress["train_list"] = train_list
        progress["train_info"] = train_info
        save_progress(progress)
    else:
        log(f"复用已有列表: {len(train_list)} 个车次")

    if not train_list:
        log("未找到车次，退出")
        return

    # 阶段二: 逐车次抓取详情
    pending = [t for t in train_list if t not in completed and t not in failed]
    total = len(pending)
    log(f"阶段二: 待抓取 {total} 车次 "
        f"(已完成 {len(completed)}, 失败 {len(failed)})")

    if not pending:
        log("全部完成!")
        return

    last_req = 0.0
    new_failed = []
    start_time = time.time()

    for i, train_no in enumerate(pending, 1):
        elapsed = time.time() - last_req
        if elapsed < MIN_INTERVAL_SEC:
            time.sleep(MIN_INTERVAL_SEC - elapsed)

        html = http_get(f"/{train_no.lower()}.html")
        last_req = time.time()

        if html:
            data = parse_detail_page(html, train_no)
            if data and data.get("stops"):
                (TRAINS_DIR / f"{train_no}.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                completed.add(train_no)
                log(f"[{i}/{total}] {train_no} ✓ {len(data['stops'])}站 "
                    f"{len(data.get('fares',{}))}票价")
            else:
                new_failed.append(train_no)
                log(f"[{i}/{total}] {train_no} ✗ 解析失败")
        else:
            new_failed.append(train_no)
            log(f"[{i}/{total}] {train_no} ✗ HTTP错误")

        if i % 100 == 0:
            progress["completed"] = sorted(completed)
            progress["failed"] = sorted(failed | set(new_failed))
            save_progress(progress)
            et = time.time() - start_time
            log(f"--- 进度: {i}/{total} | "
                f"均{et/i:.1f}s | 剩余 ~{et/i*(total-i)/60:.0f}min ---")

    progress["completed"] = sorted(completed)
    progress["failed"] = sorted(failed | set(new_failed))
    save_progress(progress)

    if new_failed:
        FAILED_FILE.write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "total": len(new_failed), "trains": new_failed
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    et = time.time() - start_time
    log(f"========== 完成: {len(completed)}/{len(train_list)} 车次, "
        f"{et/3600:.1f}h ==========")
    log(f"数据目录: {TRAINS_DIR}")


if __name__ == "__main__":
    main()
