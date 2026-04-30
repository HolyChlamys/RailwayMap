"""
渔网分割器 (Fishnet Grid Splitter)
将中国陆地边界分割为 1°×1° 网格，用于分批抓取 OSM 铁路数据。

输入:
  - data/china_boundary.geojson (来自 china_boundary.py)
  - 网格边长 step = 1.0° (约 110km)
  - 重叠宽度 overlap = 0.05° (约 5.5km)

输出:
  - data/grid_queue.json      抓取队列 (蛇形排序)
  - data/skipped_grids.json   跳过的网格 (海域/境外)
  - data/grid_r{row}_c{col}.geojson  (每格边界矩形)
"""

import json
import math
from pathlib import Path
from typing import Tuple

try:
    from shapely.geometry import box, shape, mapping
    from shapely.ops import unary_union
except ImportError:
    print("请安装 shapely: pip install shapely")
    raise

DATA_DIR = Path(__file__).parent / "data"

# 中国陆地边界默认 bbox (作为无 GeoJSON 文件时的 fallback)
CHINA_FALLBACK_BBOX = (73.5, 18.0, 135.14, 53.56)


def load_boundary_polygon(path: Path) -> object:
    """从 GeoJSON 加载中国陆地边界并构建联合多边形"""
    if not path.exists():
        print(f"[SPLITTER] 边界文件不存在: {path}, 使用 fallback bbox")
        return box(*CHINA_FALLBACK_BBOX)

    with open(path, encoding="utf-8") as f:
        geojson = json.load(f)

    polygons = []
    for feat in geojson["features"]:
        geom = shape(feat["geometry"])
        if geom.geom_type == "LineString":
            polygons.append(geom.buffer(0.001))
        elif geom.geom_type in ("Polygon", "MultiPolygon"):
            polygons.append(geom)

    if not polygons:
        print("[SPLITTER] 边界无有效几何, 使用 fallback bbox")
        return box(*CHINA_FALLBACK_BBOX)

    combined = unary_union(polygons)
    # 用凸包简化，避免岛屿空洞导致的不必要抓取
    simplified = combined.convex_hull.simplify(0.1)
    print(f"[SPLITTER] 边界多边形面积: {simplified.area:.6f} 平方度")
    return simplified


def generate_grid(
    boundary,
    step: float = 1.0,
    overlap: float = 0.05
) -> Tuple[list, list]:
    """
    生成 1°×1° 渔网分割，与中国边界相交的网格进入抓取队列。
    返回 (queue, skipped)。
    """
    minx, miny, maxx, maxy = boundary.bounds
    # 扩展边界框到整数度
    minx = math.floor(minx)
    miny = math.floor(miny)
    maxx = math.ceil(maxx)
    maxy = math.ceil(maxy)

    print(f"[SPLITTER] 网格范围: lon [{minx}, {maxx}], lat [{miny}, {maxy}]")
    print(f"[SPLITTER] 步长: {step}°, 重叠: {overlap}°")

    queue = []
    skipped = []

    row = 0
    y = miny
    while y < maxy:
        col = 0
        x = minx
        while x < maxx:
            cell = box(
                x - overlap,
                y - overlap,
                x + step + overlap,
                y + step + overlap
            )
            grid_id = f"r{row}_c{col}"

            if cell.intersects(boundary):
                queue.append({
                    "id": grid_id,
                    "row": row,
                    "col": col,
                    "bbox": f"{cell.bounds[1]:.4f},{cell.bounds[0]:.4f},{cell.bounds[3]:.4f},{cell.bounds[2]:.4f}",
                    "center_lon": (cell.bounds[0] + cell.bounds[2]) / 2,
                    "center_lat": (cell.bounds[1] + cell.bounds[3]) / 2,
                })
                # 输出每格独立 GeoJSON
                cell_geojson = {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {"grid_id": grid_id},
                        "geometry": mapping(cell)
                    }]
                }
                grid_file = DATA_DIR / f"grid_{grid_id}.geojson"
                grid_file.write_text(
                    json.dumps(cell_geojson, ensure_ascii=False), encoding="utf-8"
                )
            else:
                skipped.append(grid_id)

            col += 1
            x += step
        row += 1
        y += step

    return queue, skipped


def snake_sort(queue: list) -> list:
    """
    蛇形排序 (S-curve): 偶数行正向, 奇数行反向
    减少 Overpass API 连续请求间的空间跳跃
    """
    rows = {}
    for item in queue:
        r = item["row"]
        rows.setdefault(r, []).append(item)

    result = []
    for r in sorted(rows.keys()):
        items = sorted(rows[r], key=lambda g: g["col"])
        if r % 2 == 1:
            items.reverse()
        result.extend(items)

    return result


def run(
    boundary_path: Path = None,
    step: float = 1.0,
    overlap: float = 0.05
):
    """主入口"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if boundary_path is None:
        boundary_path = DATA_DIR / "china_boundary.geojson"

    boundary = load_boundary_polygon(boundary_path)
    queue, skipped = generate_grid(boundary, step, overlap)

    # 蛇形排序
    queue = snake_sort(queue)

    # 写入 grid_queue.json
    queue_path = DATA_DIR / "grid_queue.json"
    queue_path.write_text(
        json.dumps({
            "total": len(queue),
            "step": step,
            "overlap": overlap,
            "grids": queue
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 写入 skipped_grids.json
    skipped_path = DATA_DIR / "skipped_grids.json"
    skipped_path.write_text(
        json.dumps({
            "total": len(skipped),
            "grids": skipped
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    count = len(queue)
    estimated_hours = count * 45 / 3600  # 平均 45s/格
    print(f"[SPLITTER] 完成: 待抓取 {count} 格, 跳过 {len(skipped)} 格")
    print(f"[SPLITTER] 预估全量抓取耗时: {estimated_hours:.1f} 小时")
    print(f"[SPLITTER] 输出: {queue_path}")
    print(f"[SPLITTER] 输出: {skipped_path}")

    return queue, skipped


if __name__ == "__main__":
    run()
