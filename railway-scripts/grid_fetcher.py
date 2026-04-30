"""
逐格抓取脚本 — Overpass API 客户端
读取 grid_queue.json → 逐格查询 → 每格独立 GeoJSON 输出

特性:
  - 5 次重试 + 递增间隔
  - 429 限流特殊处理 (Retry-After)
  - 断点续传 (跳过已有输出文件)
  - 进度日志
"""

import json
import time
import urllib.request
import urllib.error
import sys
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent / "data"
OVERPAST_URL = "https://overpass-api.de/api/interpreter"

# Overpass 查询模板: 返回网格内的所有铁路线和车站
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

MIN_INTERVAL_SEC = 5  # 最小请求间隔
MAX_RETRIES = 5


def load_queue(queue_path: Path) -> list:
    """加载抓取队列"""
    if not queue_path.exists():
        print(f"[FETCHER] 队列文件不存在: {queue_path}")
        print("[FETCHER] 请先运行 grid_splitter.py 生成网格队列")
        sys.exit(1)

    data = json.loads(queue_path.read_text(encoding="utf-8"))
    grids = data.get("grids", [])
    print(f"[FETCHER] 队列: {len(grids)} 个网格待处理")
    return grids


def find_completed_grids(output_dir: Path) -> set:
    """扫描已有输出文件，实现断点续传"""
    completed = set()
    if output_dir.exists():
        for f in output_dir.glob("grid_r*_c*.geojson"):
            # 文件名格式: grid_r{row}_c{col}.geojson (抓取输出)
            # 或 grid_r{row}_c{col}.geojson (网格定义)
            name = f.stem  # grid_r0_c2
            grid_id = name.replace("grid_", "")
            if f.stat().st_size > 100:  # 非空文件
                completed.add(grid_id)
    if completed:
        print(f"[FETCHER] 发现 {len(completed)} 个已完成网格, 将跳过")
    return completed


def fetch_grid(grid: dict, output_dir: Path, index: int, total: int) -> bool:
    """
    抓取单个网格的铁路数据。
    返回 True 表示成功。
    """
    grid_id = grid["id"]
    bbox = grid["bbox"]
    output_path = output_dir / f"grid_{grid_id}.geojson"

    query = QUERY_TEMPLATE.replace("{bbox}", bbox)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = urllib.parse.urlencode({"data": query}).encode("utf-8")
            req = urllib.request.Request(
                OVERPAST_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            start = time.time()
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read().decode("utf-8")
            elapsed = time.time() - start

            result = json.loads(raw)
            elements = result.get("elements", [])

            ways = [e for e in elements if e["type"] == "way"]
            nodes = [e for e in elements if e["type"] == "node"]

            geojson = _to_geojson(elements)
            output_path.write_text(
                json.dumps(geojson, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            pct = index * 100 // total
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[{now}] [{index}/{total}] ({pct}%) {grid_id}: "
                f"铁路线 {len(ways)}, 车站 {len(nodes)}, "
                f"耗时 {elapsed:.1f}s"
            )
            return True

        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")[:200]
            except Exception:
                pass

            print(f"[FETCHER] {grid_id} HTTP {e.code}: {e.reason} {body}")

            if e.code == 429:
                # 从 Retry-After header 或递增等待获取时间
                retry_after = e.headers.get("Retry-After", str(30 * attempt))
                wait = int(retry_after) if retry_after.isdigit() else 30 * attempt
                print(f"[FETCHER] 429 限流, 等待 {wait}s …")
                time.sleep(wait)
            elif e.code == 504:
                if attempt < MAX_RETRIES:
                    wait = 30 * attempt
                    print(f"[FETCHER] 504 超时, 等待 {wait}s 后重试 …")
                    time.sleep(wait)
            else:
                if attempt < MAX_RETRIES:
                    time.sleep(10 * attempt)

        except urllib.error.URLError as e:
            print(f"[FETCHER] {grid_id} 网络错误: {e.reason}")
            if attempt < MAX_RETRIES:
                time.sleep(10 * attempt)

        except Exception as e:
            print(f"[FETCHER] {grid_id} 异常: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(10 * attempt)

    print(f"[FETCHER] {grid_id} 失败 (已重试 {MAX_RETRIES} 次)")
    return False


def _to_geojson(elements: list) -> dict:
    """将 Overpass 元素转换为 GeoJSON FeatureCollection"""
    features = []

    nodes_map = {}
    for el in elements:
        if el["type"] == "node":
            nodes_map[el["id"]] = (el["lon"], el["lat"])

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
            railway = el.get("tags", {}).get("railway", "")
            public_transport = el.get("tags", {}).get("public_transport", "")
            if railway or public_transport:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "osm_id": el["id"],
                        "railway": railway,
                        "public_transport": public_transport,
                        "name": el.get("tags", {}).get("name", ""),
                        "name:zh": el.get("tags", {}).get("name:zh", ""),
                        "station": el.get("tags", {}).get("station", ""),
                        "train": el.get("tags", {}).get("train", ""),
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [el["lon"], el["lat"]]
                    }
                })

    return {"type": "FeatureCollection", "features": features}


def run(queue_path: Path = None, output_dir: Path = None):
    """主入口"""
    if queue_path is None:
        queue_path = DATA_DIR / "grid_queue.json"
    if output_dir is None:
        output_dir = DATA_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    grids = load_queue(queue_path)
    completed = find_completed_grids(output_dir)

    pending = [g for g in grids if g["id"] not in completed]
    print(f"[FETCHER] 待抓取: {len(pending)} 格, 已完成: {len(completed)} 格")

    if not pending:
        print("[FETCHER] 所有网格已完成, 无需抓取")
        return

    failed_grids = []
    total = len(pending)
    last_request_time = None

    for i, grid in enumerate(pending, 1):
        # 请求间隔
        if last_request_time:
            elapsed = (time.time() - last_request_time)
            if elapsed < MIN_INTERVAL_SEC:
                time.sleep(MIN_INTERVAL_SEC - elapsed)

        success = fetch_grid(grid, output_dir, i, total)
        last_request_time = time.time()

        if not success:
            failed_grids.append(grid["id"])

    # 失败报告
    if failed_grids:
        failed_path = output_dir / "failed_grids.json"
        failed_path.write_text(
            json.dumps({
                "timestamp": datetime.now().isoformat(),
                "total_failed": len(failed_grids),
                "grids": failed_grids
            }, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[FETCHER] 失败网格已记录: {failed_path}")
        print(f"[FETCHER] 失败列表: {failed_grids}")
    else:
        print("[FETCHER] 全部成功!")


if __name__ == "__main__":
    run()
