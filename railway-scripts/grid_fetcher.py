"""
逐格抓取脚本 — Overpass API 客户端
读取 grid_queue.json → 逐格查询 → 每格独立 GeoJSON 输出

特性:
  - 持久化进度日志 (progress.log)
  - 断点续传 (跳过已有输出文件)
  - 5 次重试 + 429 限流处理
  - 随时可 Ctrl+C 停止，再次运行自动续传
"""

import json
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "grids"
PROGRESS_LOG = DATA_DIR / "progress.log"
FAILED_LOG = DATA_DIR / "failed_grids.json"
OVERPAST_URL = "https://overpass-api.de/api/interpreter"

QUERY_TEMPLATE = """
[out:json][timeout:180];
(
  way["railway"="rail"]({bbox});
  way["railway"="subway"]({bbox});
  way["railway"="light_rail"]({bbox});
  way["railway"="narrow_gauge"]({bbox});
  way["railway"="funicular"]({bbox});
  way["railway"="tram"]({bbox});
  way["railway"="disused"]({bbox});
  way["railway"="abandoned"]({bbox});
  node["railway"="station"]({bbox});
  node["railway"="halt"]({bbox});
  node["railway"="tram_stop"]({bbox});
  node["railway"="yard"]({bbox});
  node["railway"="depot"]({bbox});
  node["railway"="signal_box"]({bbox});
  node["public_transport"="station"]["train"="yes"]({bbox});
);
out geom;
"""

MIN_INTERVAL_SEC = 5
MAX_RETRIES = 5


def log(msg: str):
    """写日志到文件和 stdout"""
    line = f"[{datetime.now().strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(PROGRESS_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_queue(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    grids = data.get("grids", [])
    log(f"队列加载: {len(grids)} 个网格")
    return grids


def find_completed() -> set:
    """扫描已有输出文件"""
    completed = set()
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("grid_r*_c*.geojson"):
            if f.stat().st_size > 100:
                grid_id = f.stem.replace("grid_", "")
                completed.add(grid_id)
    return completed


def fetch_grid(grid: dict, index: int, total: int) -> bool:
    grid_id = grid["id"]
    output_path = OUTPUT_DIR / f"grid_{grid_id}.geojson"
    query = QUERY_TEMPLATE.replace("{bbox}", grid["bbox"])

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()
            resp = requests.post(
                OVERPAST_URL, data={"data": query}, timeout=180,
                headers={"User-Agent": "RailwayMap/1.0"}
            )
            elapsed = time.time() - start

            if resp.status_code == 200:
                result = resp.json()
                elements = result.get("elements", [])
                ways = sum(1 for e in elements if e["type"] == "way")
                nodes = sum(1 for e in elements if e["type"] == "node")

                geojson = _to_geojson(elements)
                output_path.write_text(
                    json.dumps(geojson, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

                log(f"[{index}/{total}] {grid_id} ✓ 线{ways} 站{nodes} {elapsed:.1f}s")
                return True

            elif resp.status_code == 429:
                wait = 30 * attempt
                log(f"[{index}/{total}] {grid_id} 429限流 等{wait}s")
                time.sleep(wait)
            elif resp.status_code >= 500:
                wait = 15 * attempt
                log(f"[{index}/{total}] {grid_id} {resp.status_code} 等{wait}s")
                time.sleep(wait)
            else:
                log(f"[{index}/{total}] {grid_id} HTTP{resp.status_code} 跳过")
                return False

        except requests.exceptions.Timeout:
            log(f"[{index}/{total}] {grid_id} 超时(尝试{attempt})")
        except Exception as e:
            log(f"[{index}/{total}] {grid_id} 异常: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(10 * attempt)

    log(f"[{index}/{total}] {grid_id} ✗ 失败({MAX_RETRIES}次重试)")
    return False


def _to_geojson(elements: list) -> dict:
    features = []
    for el in elements:
        if el["type"] == "way" and "geometry" in el:
            features.append({
                "type": "Feature",
                "properties": {
                    "osm_id": el["id"],
                    "railway": el.get("tags", {}).get("railway", ""),
                    "name": el.get("tags", {}).get("name", ""),
                    "usage": el.get("tags", {}).get("usage", ""),
                    "highspeed": el.get("tags", {}).get("highspeed", ""),
                    "electrified": el.get("tags", {}).get("electrified", ""),
                    "gauge": el.get("tags", {}).get("gauge", ""),
                    "maxspeed": el.get("tags", {}).get("maxspeed", ""),
                    "tracks": el.get("tags", {}).get("tracks", ""),
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[p["lon"], p["lat"]] for p in el["geometry"]]
                }
            })
        elif el["type"] == "node" and "tags" in el:
            rw = el.get("tags", {}).get("railway", "")
            pt = el.get("tags", {}).get("public_transport", "")
            if rw or pt:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "osm_id": el["id"],
                        "railway": rw,
                        "name": el.get("tags", {}).get("name", ""),
                        "name:zh": el.get("tags", {}).get("name:zh", ""),
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [el["lon"], el["lat"]]
                    }
                })
    return {"type": "FeatureCollection", "features": features}


def print_status(completed: set, pending: list, failed: set):
    """输出当前状态摘要"""
    done = len(completed)
    total = done + len(pending)
    pct = done * 100 // max(total, 1)
    log(f"====== 状态: {done}/{total} ({pct}%) 完成, {len(failed)} 失败 ======")


def run():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log("========== 网格抓取启动 ==========")

    grids = load_queue(DATA_DIR / "grid_queue.json")
    completed = find_completed()

    # 加载之前的失败记录
    failed = set()
    if FAILED_LOG.exists():
        try:
            prev = json.loads(FAILED_LOG.read_text(encoding="utf-8"))
            failed = set(prev.get("grids", []))
        except Exception:
            pass

    pending = [g for g in grids if g["id"] not in completed and g["id"] not in failed]

    if not pending:
        log("所有网格已完成!")
        print_status(completed, pending, failed)
        return

    total_pending = len(pending)
    log(f"待抓取: {total_pending} 格, 已完成: {len(completed)} 格")

    if completed:
        print_status(completed, pending, failed)

    new_failed = []
    last_req = 0.0
    start_time = time.time()

    for i, grid in enumerate(pending, 1):
        # 请求间隔
        elapsed = time.time() - last_req
        if elapsed < MIN_INTERVAL_SEC:
            time.sleep(MIN_INTERVAL_SEC - elapsed)

        success = fetch_grid(grid, i, total_pending)
        last_req = time.time()

        if not success:
            new_failed.append(grid["id"])

        # 每 50 格输出一次状态摘要
        if i % 50 == 0:
            elapsed_total = time.time() - start_time
            avg = elapsed_total / i
            remaining = avg * (total_pending - i)
            log(f"--- 进度: {i}/{total_pending} | 均{avg:.1f}s/格 | 预计剩余 {remaining/60:.0f}min ---")

    # 最终状态
    elapsed_total = time.time() - start_time
    all_failed = failed | set(new_failed)
    log(f"========== 本轮完成: {total_pending}格, {elapsed_total/3600:.1f}h ==========")

    if new_failed:
        FAILED_LOG.write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "total_failed": len(new_failed),
            "grids": list(all_failed)
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"本轮失败 {len(new_failed)} 格 → {FAILED_LOG}")
    else:
        log("本轮全部成功 ✓")

    print_status(find_completed(), [], all_failed)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        log("========== 用户中断 (可随时重新运行续传) ==========")
        print_status(find_completed(), [], set())
        sys.exit(0)
