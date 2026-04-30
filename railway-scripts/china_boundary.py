"""
中国陆地边界获取脚本
数据源: OpenStreetMap relation 270056 (China)
输出: data/china_boundary.geojson
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OVERPAST_URL = "https://overpass-api.de/api/interpreter"

QUERY = """
[out:json][timeout:300];
rel(270056);
map_to_area -> .china;
rel(pivot.china);
(._;>;);
out geom;
"""


def fetch_boundary(output_path: Path, max_retries: int = 3) -> bool:
    """
    从 Overpass API 获取中国陆地边界 (relation 270056)。
    返回 True 表示成功，False 表示失败。
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    data = urllib.parse.urlencode({"data": QUERY}).encode("utf-8")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[FETCH] 尝试 {attempt}/{max_retries} …")
            req = urllib.request.Request(
                OVERPAST_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read().decode("utf-8")

            result = json.loads(raw)
            elements = result.get("elements", [])
            if not elements:
                print("[FETCH] 返回空结果，跳过")
                return False

            # 提取闭合边界线 (outer ways of relation 270056)
            ways = []
            nodes = {}
            for el in elements:
                if el["type"] == "way" and "geometry" in el:
                    ways.append(el)
                elif el["type"] == "node":
                    nodes[el["id"]] = (el["lon"], el["lat"])

            geojson = _to_geojson(ways, nodes)
            output_path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")

            coord_count = sum(len(f["geometry"]["coordinates"]) for f in geojson["features"])
            print(f"[FETCH] 成功: {len(geojson['features'])} 条边界线, {coord_count} 个坐标点")
            print(f"[FETCH] 输出: {output_path}")
            return True

        except urllib.error.HTTPError as e:
            print(f"[FETCH] HTTP {e.code}: {e.reason}")
            if e.code == 429:
                wait = 30 * attempt
                print(f"[FETCH] 429 限流, 等待 {wait}s …")
                time.sleep(wait)
            elif attempt < max_retries:
                time.sleep(10 * attempt)
        except Exception as e:
            print(f"[FETCH] 异常: {e}")
            if attempt < max_retries:
                time.sleep(10 * attempt)

    print("[FETCH] 所有重试失败")
    return False


def _to_geojson(ways: list, nodes: dict) -> dict:
    features = []
    for way in ways:
        coords = way.get("geometry", [])
        if len(coords) < 2:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "osm_id": way["id"],
                "name": way.get("tags", {}).get("name", ""),
                "boundary": way.get("tags", {}).get("boundary", ""),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[p["lon"], p["lat"]] for p in coords]
            }
        })
    return {"type": "FeatureCollection", "features": features}


def verify_boundary(path: Path) -> bool:
    """验证边界 GeoJSON 文件完整性"""
    if not path.exists():
        print(f"[VERIFY] 文件不存在: {path}")
        return False

    try:
        geojson = json.loads(path.read_text(encoding="utf-8"))
        features = geojson.get("features", [])
        if not features:
            print("[VERIFY] GeoJSON 无要素")
            return False

        # 计算 bbox
        all_coords = []
        for f in features:
            all_coords.extend(f["geometry"]["coordinates"])
        lons = [c[0] for c in all_coords]
        lats = [c[1] for c in all_coords]

        bbox = (min(lons), min(lats), max(lons), max(lats))
        print(f"[VERIFY] 边界框: {bbox}")
        print(f"[VERIFY] 要素数: {len(features)}, 坐标点数: {len(all_coords)}")

        # 验证中国预期范围
        if bbox[0] < 73 or bbox[2] > 136 or bbox[1] < 15 or bbox[3] > 55:
            print("[VERIFY] 警告: bbox 超出中国预期范围, 边界可能不完整")

        # 检查是否闭合
        if len(features) <= 1:
            print("[VERIFY] 警告: 只有一条边界线, 可能仅是陆上边界 (缺海岸线)")

        return True
    except Exception as e:
        print(f"[VERIFY] 解析异常: {e}")
        return False


if __name__ == "__main__":
    output = DATA_DIR / "china_boundary.geojson"
    if fetch_boundary(output):
        verify_boundary(output)
