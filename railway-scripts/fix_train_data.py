"""
修复 train JSON 数据中的时间字段 v2
策略: arrive_time 列可靠，用相邻站交叉填充 depart_time
- stop[N].depart_time = stop[N+1].arrive_time (同一站出发=下一站到达)
- 或 stop[N].arrive_time (大部分站到站即发车)
"""

import json, re, os
from pathlib import Path

TRAINS_DIR = Path(__file__).parent / "data" / "trains"
TIME_RE = re.compile(r'^\d{1,2}:\d{2}$')


def is_valid(s: str) -> bool:
    if not s: return False
    return bool(TIME_RE.match(str(s).strip()))


def fix_file(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0

    stops = data.get("stops", [])
    if not stops: return 0

    fixes = 0
    n = len(stops)

    for i, stop in enumerate(stops):
        arr = str(stop.get("arrive_time", "")).strip()
        dep = str(stop.get("depart_time", "")).strip()

        # 清理明显无效值（数字、特殊字符）
        if arr in ("----", "", "None"): arr = ""
        if dep in ("----", "", "None"): dep = ""

        # arrive: 已有有效值则保留
        if not is_valid(arr): arr = ""
        if not is_valid(dep): dep = ""

        stop["arrive_time"] = arr
        stop["depart_time"] = dep

    # 交叉填充: depart = 下一站的 arrive
    for i in range(n - 1):
        if not is_valid(stops[i].get("depart_time", "")):
            next_arr = stops[i + 1].get("arrive_time", "")
            if is_valid(next_arr):
                # 这里 depart 应该是本站在两站之间的发车时间
                # 但爬虫没抓到，用 next_stop.arrive 也不对
                # 退而求其次: 用 arrive_time 代替（大部分站停留时间短）
                if not is_valid(stops[i].get("depart_time", "")):
                    if is_valid(stops[i].get("arrive_time", "")):
                        stops[i]["depart_time"] = stops[i]["arrive_time"]
                        fixes += 1

    # 特殊处理首站和末站
    # 首站: depart_time = arrive_time (如果没有)
    if is_valid(stops[0].get("arrive_time", "")) and not is_valid(stops[0].get("depart_time", "")):
        stops[0]["depart_time"] = stops[0]["arrive_time"]
        fixes += 1

    # 末站: arrive_time = 上一站的 depart_time 或 arrive_time
    if not is_valid(stops[-1].get("arrive_time", "")):
        for prev in range(n - 2, -1, -1):
            t = stops[prev].get("depart_time", "") or stops[prev].get("arrive_time", "")
            if is_valid(t):
                stops[-1]["arrive_time"] = t
                fixes += 1
                break

    # Route 级别时间
    depart = stops[0].get("depart_time", "") or stops[0].get("arrive_time", "")
    arrive = stops[-1].get("arrive_time", "") or stops[-1].get("depart_time", "")

    if is_valid(depart): data["depart_time"] = depart
    if is_valid(arrive): data["arrive_time"] = arrive

    # 清理无效值
    for stop in stops:
        for key in ("arrive_time", "depart_time"):
            v = str(stop.get(key, "")).strip()
            if not is_valid(v):
                stop[key] = ""

    if fixes > 0:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return fixes


def main():
    files = sorted(TRAINS_DIR.glob("*.json"))
    total = len(files)
    fixed = fixed_files = 0
    for i, f in enumerate(files, 1):
        n = fix_file(f)
        if n: fixed += n; fixed_files += 1
        if i % 5000 == 0:
            print(f"{i}/{total} | {fixed_files} 文件, {fixed} 处")
    print(f"完成: {total} 文件, 修复 {fixed_files} 个 ({fixed} 处)")


if __name__ == "__main__":
    main()
