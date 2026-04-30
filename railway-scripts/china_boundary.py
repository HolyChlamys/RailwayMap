"""
中国陆地边界获取脚本
数据源: OpenStreetMap relation 270056 (China)
输出: data/china_boundary.geojson
"""

import json
import time
import requests
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OVERPAST_URL = "https://overpass-api.de/api/interpreter"

# 获取 relation 270056 的所有成员（含几何）
QUERY = """
[out:json][timeout:300];
rel(270056);
(._;>;);
out geom;
"""


def fetch_boundary(output_path: Path, max_retries: int = 3) -> bool:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[FETCH] 尝试 {attempt}/{max_retries} …")
            resp = requests.post(
                OVERPAST_URL,
                data={"data": QUERY},
                timeout=300,
                headers={"User-Agent": "RailwayMap/1.0"}
            )
            if resp.status_code != 200:
                print(f"[FETCH] HTTP {resp.status_code}: {resp.text[:200]}")
                if resp.status_code == 429:
                    wait = 30 * attempt
                    print(f"[FETCH] 429 限流, 等待 {wait}s …")
                    time.sleep(wait)
                elif attempt < max_retries:
                    time.sleep(10 * attempt)
                continue

            result = resp.json()
            elements = result.get("elements", [])
            if not elements:
                print("[FETCH] 返回空结果，跳过")
                return False

            ways = []
            for el in elements:
                if el["type"] == "way" and "geometry" in el:
                    ways.append(el)

            if not ways:
                print(f"[FETCH] 无 way 元素，返回 {len(elements)} 个元素")
                return False

            geojson = _to_geojson(ways)
            output_path.write_text(
                json.dumps(geojson, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            coord_count = sum(len(f["geometry"]["coordinates"]) for f in geojson["features"])
            print(f"[FETCH] 成功: {len(geojson['features'])} 条边界线, {coord_count} 个坐标点")
            print(f"[FETCH] 输出: {output_path}")
            return True

        except requests.exceptions.Timeout:
            print(f"[FETCH] 超时")
        except Exception as e:
            print(f"[FETCH] 异常: {e}")
            if attempt < max_retries:
                time.sleep(10 * attempt)

    print("[FETCH] 所有重试失败")
    return False


def _to_geojson(ways: list) -> dict:
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
    if not path.exists():
        print(f"[VERIFY] 文件不存在: {path}")
        return False
    try:
        geojson = json.loads(path.read_text(encoding="utf-8"))
        features = geojson.get("features", [])
        if not features:
            print("[VERIFY] GeoJSON 无要素")
            return False
        all_coords = []
        for f in features:
            all_coords.extend(f["geometry"]["coordinates"])
        lons = [c[0] for c in all_coords]
        lats = [c[1] for c in all_coords]
        bbox = (min(lons), min(lats), max(lons), max(lats))
        print(f"[VERIFY] 边界框: lon[{bbox[0]:.2f}, {bbox[2]:.2f}] lat[{bbox[1]:.2f}, {bbox[3]:.2f}]")
        print(f"[VERIFY] 要素数: {len(features)}, 坐标点数: {len(all_coords)}")
        if len(features) <= 1:
            print("[VERIFY] 警告: 只有一条边界线，可能缺海岸线数据")
        return True
    except Exception as e:
        print(f"[VERIFY] 解析异常: {e}")
        return False


if __name__ == "__main__":
    output = DATA_DIR / "china_boundary.geojson"
    if fetch_boundary(output):
        verify_boundary(output)
