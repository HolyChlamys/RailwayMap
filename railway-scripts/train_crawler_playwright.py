"""
Playwright 车次爬虫 — Windows 11 运行
- 用真实浏览器渲染 liecheba.com 列表页，获取完整车次列表
- 逐车次抓取时刻表 + 票价
- 输出: data/trains/{train_no}.json
- 断点续传，进度日志

安装: pip install playwright && playwright install chromium
运行: python train_crawler_playwright.py
"""

import json
import re
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("请先安装: pip install playwright && playwright install chromium")
    sys.exit(1)

DATA_DIR = Path(__file__).parent / "data"
TRAINS_DIR = DATA_DIR / "trains"
PROGRESS_FILE = DATA_DIR / "train_progress.json"
FAILED_FILE = DATA_DIR / "train_failed.json"

BASE_URL = "https://www.liecheba.com"
MIN_INTERVAL_SEC = 1.5
PAGE_TIMEOUT = 20_000  # ms

TRAIN_PREFIXES = ["G", "D", "C", "Z", "T", "K", "Y", "S"]


def log(msg: str):
    now = datetime.now().strftime("%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


# ============================================================
# 阶段一: 用浏览器获取车次列表
# ============================================================

def crawl_train_list(page) -> list[str]:
    """
    访问 /train/ 页面，等待 JS 渲染完成后提取所有车次号。
    liecheba.com 的列表页可能用了不同的 URL 模式，
    需要逐个前缀探索。
    """
    all_trains = set()

    for prefix in TRAIN_PREFIXES:
        log(f"===== {prefix} 字头 =====")
        page_num = 1
        prefix_trains = 0

        while True:
            url = f"{BASE_URL}/train/{prefix}/list_{page_num}.html"
            log(f"尝试 {url}")

            try:
                resp = page.goto(url, timeout=PAGE_TIMEOUT, wait_until="networkidle")
                if resp and resp.status >= 400:
                    # 尝试另一种 URL 模式
                    url2 = f"{BASE_URL}/train/{prefix}/list-{page_num}.html"
                    log(f"404, 尝试备选 {url2}")
                    resp = page.goto(url2, timeout=PAGE_TIMEOUT, wait_until="networkidle")

                if resp and resp.status >= 400:
                    if page_num == 1:
                        # 第一页就 404，这个前缀可能没有
                        log(f"{prefix} 字头无数据")
                    break
            except Exception as e:
                log(f"页面加载异常: {e}")
                break

            # 等待列表渲染
            try:
                page.wait_for_selector("a[href]", timeout=5000)
            except Exception:
                pass
            time.sleep(1)

            # 提取车次链接: /g1.html, /d301.html 等
            html = page.content()
            pattern = rf'href="/({prefix.lower()}\d+\.html)"'
            matches = re.findall(pattern, html, re.IGNORECASE)

            if not matches:
                # 再试另一种模式: /train/G1.html
                pattern2 = rf'href="/train/({prefix}\d+\.html)"'
                matches = re.findall(pattern2, html, re.IGNORECASE)

            if not matches:
                log(f"第{page_num}页无车次链接，停止翻页")
                break

            # 提取车次号
            train_nos = set()
            for m in matches:
                no = re.match(rf'({prefix}\d+)', m, re.IGNORECASE)
                if no:
                    train_nos.add(no.group(1).upper())

            if not train_nos:
                break

            all_trains.update(train_nos)
            prefix_trains += len(train_nos)
            log(f"  第{page_num}页: {len(train_nos)} 个车次 (累计 {prefix_trains})")
            page_num += 1

            if page_num > 100:  # 安全上限
                break

        if prefix_trains > 0:
            log(f"{prefix} 字头共 {prefix_trains} 车次")

    log(f"========== 共发现 {len(all_trains)} 个车次 ==========")
    return sorted(all_trains)


# ============================================================
# 阶段二: 抓取每个车次的详情
# ============================================================

def crawl_train_detail(page, train_no: str) -> dict | None:
    """抓取单趟车次的时刻表 + 票价"""
    url = f"{BASE_URL}/{train_no}.html"

    try:
        resp = page.goto(url, timeout=PAGE_TIMEOUT, wait_until="networkidle")
        if resp and resp.status >= 400:
            log(f"  {train_no}: HTTP {resp.status}")
            return None
    except Exception as e:
        log(f"  {train_no}: 页面异常 {e}")
        return None

    html = page.content()

    # 1. 提取途经站时刻表
    stops = parse_schedule_table(html, train_no)
    if not stops:
        # 尝试从 meta description 判断是否有效车次
        meta = re.search(r'<meta name="description" content="([^"]+)"', html)
        if meta:
            log(f"  {train_no}: 无时刻表但description有效")
        else:
            log(f"  {train_no}: 无数据")
            return None

    # 2. 提取票价
    fares = parse_fare_table(html)

    # 3. 提取基本信息
    depart_station = stops[0]["station_name"] if stops else ""
    arrive_station = stops[-1]["station_name"] if stops else ""
    depart_time = stops[0].get("depart_time", "") if stops else ""
    arrive_time = stops[-1].get("arrive_time", "") if stops else ""

    return {
        "train_no": train_no,
        "train_type": train_no[0],
        "depart_station": depart_station,
        "arrive_station": arrive_station,
        "depart_time": depart_time,
        "arrive_time": arrive_time,
        "stops": stops,
        "fares": fares,
        "fetched_at": datetime.now().isoformat(),
    }


def parse_schedule_table(html: str, train_no: str) -> list[dict]:
    """从 HTML 中提取时刻表"""
    stops = []

    # 尝试找 table 中的 tr
    # 模式: <tr><td>1</td><td>北京南</td><td>06:30</td><td>06:30</td><td>0</td></tr>
    # 或: <tr><td>01</td><td>北京南</td><td>----</td><td>06:30</td><td>0分钟</td></tr>

    # 先尝试找时刻表所在区域
    table_match = re.search(r'<table[^>]*class="[^"]*schedule[^"]*"[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    if not table_match:
        table_match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    if not table_match:
        return stops

    table_html = table_match.group(1)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)

    for row in rows:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.IGNORECASE)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

        if len(cells) < 3:
            continue

        # 判断是否是数据行（第一列是数字序号）
        seq = cells[0].strip()
        if not seq.isdigit():
            continue

        stop = {
            "seq": int(seq),
            "station_name": cells[1] if len(cells) > 1 else "",
            "arrive_time": cells[2] if len(cells) > 2 else "",
            "depart_time": cells[3] if len(cells) > 3 else "",
            "stay_min": cells[4] if len(cells) > 4 else "",
        }

        # 过滤表头行
        if stop["station_name"] in ("站名", "车站", "station", "站次"):
            continue

        stops.append(stop)

    return stops


def parse_fare_table(html: str) -> dict:
    """从 HTML 中提取票价表"""
    fares = {}

    # 票价映射
    seat_map = {
        "商务座": "price_business", "特等座": "price_business",
        "一等座": "price_first",
        "二等座": "price_second",
        "软卧上": "price_soft_sleeper_up", "软卧下": "price_soft_sleeper_down",
        "硬卧上": "price_hard_sleeper_up", "硬卧中": "price_hard_sleeper_mid",
        "硬卧下": "price_hard_sleeper_down",
        "硬座": "price_hard_seat",
        "无座": "price_no_seat",
    }

    # 找票价相关的 table
    fare_match = re.search(
        r'<table[^>]*class="[^"]*(?:fare|price|ticket)[^"]*"[^>]*>(.*?)</table>',
        html, re.DOTALL | re.IGNORECASE
    )
    if not fare_match:
        # 备选: 找所有 table
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
        for t_html in tables:
            if any(k in t_html for k in ["商务座", "一等座", "二等座", "硬座", "硬卧"]):
                fare_match = re.search(r'(.*)', t_html, re.DOTALL)
                break

    if fare_match:
        table_html = fare_match.group(1) if fare_match else fare_match
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', str(table_html), re.DOTALL)
        for row in rows:
            cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.IGNORECASE)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            if len(cells) >= 2:
                seat = cells[0]
                price_str = cells[1].replace("¥", "").replace("￥", "").replace(",", "").strip()
                try:
                    price = float(price_str)
                    if seat in seat_map:
                        fares[seat_map[seat]] = price
                except ValueError:
                    pass

    return fares


# ============================================================
# 进度管理
# ============================================================

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {"completed": [], "failed": [], "train_list": []}


def save_progress(data: dict):
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_failed() -> list:
    if FAILED_FILE.exists():
        return json.loads(FAILED_FILE.read_text(encoding="utf-8")).get("trains", [])
    return []


# ============================================================
# 主流程
# ============================================================

def main():
    TRAINS_DIR.mkdir(parents=True, exist_ok=True)

    log("========== 车次爬虫启动(Playwright) ==========")

    progress = load_progress()
    completed = set(progress["completed"])
    failed = set(progress.get("failed", []))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # 阶段一: 获取车次列表
        train_list = progress.get("train_list", [])
        if not train_list:
            log("阶段一: 获取车次列表")
            train_list = crawl_train_list(page)
            progress["train_list"] = train_list
            save_progress(progress)
        else:
            log(f"复用已有车次列表: {len(train_list)} 个")

        if not train_list:
            log("未找到任何车次，退出")
            browser.close()
            return

        # 阶段二: 逐车次抓取
        pending = [t for t in train_list if t not in completed and t not in failed]
        total = len(pending)
        log(f"阶段二: 待抓取 {total} 车次 (已完成 {len(completed)}, 失败 {len(failed)})")

        if not pending:
            log("所有车次已完成!")
            browser.close()
            return

        last_req = 0.0
        new_failed = []
        train_count = 0
        start_time = time.time()

        for i, train_no in enumerate(pending, 1):
            # 请求间隔
            elapsed = time.time() - last_req
            if elapsed < MIN_INTERVAL_SEC:
                time.sleep(MIN_INTERVAL_SEC - elapsed)

            # 抓取
            data = crawl_train_detail(page, train_no)
            last_req = time.time()

            if data and data.get("stops"):
                output = TRAINS_DIR / f"{train_no}.json"
                output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                completed.add(train_no)
                stops_n = len(data["stops"])
                fares_n = len(data.get("fares", {}))
                log(f"[{i}/{total}] {train_no} ✓ {stops_n}站 {fares_n}票价")
            else:
                new_failed.append(train_no)
                # 仍然保存一个空标记，避免重复尝试
                (TRAINS_DIR / f"{train_no}.json").write_text("{}")
                log(f"[{i}/{total}] {train_no} ✗")

            train_count += 1

            # 每 50 个保存进度
            if i % 50 == 0:
                progress["completed"] = sorted(completed)
                progress["failed"] = sorted(failed | set(new_failed))
                save_progress(progress)
                elapsed_t = time.time() - start_time
                avg_s = elapsed_t / i
                remaining_m = avg_s * (total - i) / 60
                log(f"--- 进度: {i}/{total} | 均{avg_s:.1f}s/车 | 预计剩余 {remaining_m:.0f}min ---")

        # 最终保存
        progress["completed"] = sorted(completed)
        progress["failed"] = sorted(failed | set(new_failed))
        save_progress(progress)

        if new_failed:
            FAILED_FILE.write_text(json.dumps(
                {"timestamp": datetime.now().isoformat(), "total": len(new_failed), "trains": new_failed},
                ensure_ascii=False, indent=2
            ), encoding="utf-8")

        browser.close()

    elapsed_t = time.time() - start_time
    log(f"========== 完成: {len(completed)} 车次, 耗时 {elapsed_t/3600:.1f}h ==========")
    log(f"数据目录: {TRAINS_DIR}")


if __name__ == "__main__":
    main()
