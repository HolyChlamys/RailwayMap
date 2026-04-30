#!/usr/bin/env python3
"""快速查看抓取进度 — 无需依赖，随时可运行"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "grids"
QUEUE_FILE = DATA_DIR / "grid_queue.json"
PROGRESS_LOG = DATA_DIR / "progress.log"
FAILED_LOG = DATA_DIR / "failed_grids.json"

# 1. 日志最后几行
if PROGRESS_LOG.exists():
    lines = PROGRESS_LOG.read_text(encoding="utf-8").strip().split("\n")
    print(f"=== 最近日志 ({min(5, len(lines))} 条) ===")
    for line in lines[-5:]:
        print(line)
    print()

# 2. 文件统计
total = 0
if QUEUE_FILE.exists():
    data = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    total = len(data.get("grids", []))

completed = len(list(OUTPUT_DIR.glob("grid_r*_c*.geojson"))) if OUTPUT_DIR.exists() else 0

# 3. 数据统计
total_size = 0
total_ways = 0
total_nodes = 0
if OUTPUT_DIR.exists():
    for f in OUTPUT_DIR.glob("grid_r*_c*.geojson"):
        total_size += f.stat().st_size
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            for feat in d.get("features", []):
                if feat["geometry"]["type"] == "LineString":
                    total_ways += 1
                elif feat["geometry"]["type"] == "Point":
                    total_nodes += 1
        except Exception:
            pass

# 4. 失败列表
failed = 0
if FAILED_LOG.exists():
    fd = json.loads(FAILED_LOG.read_text(encoding="utf-8"))
    failed = fd.get("total_failed", 0)

pct = completed * 100 // max(total, 1)
print(f"=== 抓取进度 ===")
print(f"完成: {completed}/{total} ({pct}%)")
print(f"失败: {failed}")
print(f"数据: {total_size/1024/1024:.1f}MB | 铁路线: {total_ways} | 车站: {total_nodes}")
print()

# 5. 预计剩余
if pct > 0 and completed > 0:
    remaining = total - completed
    # 从日志估算平均速度
    avg_sec = 45
    if PROGRESS_LOG.exists():
        import re
        times = re.findall(r"(\d+\.\d+)s$", "\n".join(lines), re.MULTILINE)
        if times:
            avg_sec = sum(float(t) for t in times) / len(times)

    eta_min = remaining * avg_sec / 60
    print(f"预计剩余: {eta_min/60:.1f} 小时 ({eta_min:.0f} 分钟)")
    print(f"(平均 {avg_sec:.1f}s/格)")

print()
print("提示: 随时 Ctrl+C 停止，再次运行 grid_fetcher.py 自动续传")
