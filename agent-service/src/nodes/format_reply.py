from ..state import AgentState


async def format_reply(state: AgentState) -> dict:
    intent = state.get("intent", "clarify")
    tool_results = state.get("tool_results", [])
    relax_history = state.get("relax_history", [])
    constraints = state.get("constraints") or {}
    station = None
    routes_data = None
    suggestions = []

    if intent == "station_query" or intent == "timetable_query":
        reply_text, instructions, station = await _format_station_result(tool_results, intent)
    elif intent == "train_query":
        reply_text, instructions, station = _format_train_result(tool_results)
    elif intent == "route_planning":
        reply_text, instructions, routes_data = _format_route_result(tool_results, relax_history, constraints)
        suggestions = ["只看高铁", "最少换乘", "尝试其他时间段"]
    elif intent == "isochrone":
        reply_text, instructions = _format_isochrone_result(tool_results, constraints)
        suggestions = ["细看哪个方向？", "从这些城市中选一个目的地规划路线"]
    else:
        reply_text = "有什么我可以帮你的？"
        suggestions = []

    result = {
        "reply_text": reply_text,
        "instructions": instructions,
        "suggestions": suggestions,
    }
    if station is not None:
        result["station"] = station
    if routes_data is not None:
        result["routes_data"] = routes_data
    return result


def _nested_get(d: dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d


async def _format_station_result(tool_results: list[dict], intent: str) -> tuple[str, list[dict], dict | None]:
    from ..tools import ALL_TOOLS
    for r in tool_results:
        t = r.get("tool", "")
        if t in ("search_stations", "get_station_detail", "get_station_timetable"):
            # Try multiple possible keys for station data
            station = r.get("station")
            if not station:
                stations_list = r.get("stations")
                if stations_list and len(stations_list) > 0:
                    station = stations_list[0]
            if not station:
                continue
            sid = station.get("id")
            # Fetch full detail to get routes/passingTrains
            detail = None
            if t == "search_stations" and sid:
                try:
                    detail_result = await ALL_TOOLS["get_station_detail"](str(sid))
                    detail = detail_result.get("station", {})
                except Exception:
                    detail = {}
            # Merge detail into station data — only take routes/timetable from detail
            rich_station = dict(station)
            if detail:
                for k in ("passingTrains", "timetable"):
                    if detail.get(k):
                        rich_station[k] = detail[k]
            name = rich_station.get("name", "未知站")
            city = rich_station.get("city", "")
            instructions = [
                {"action": "flyToStation", "stationId": str(sid)},
                {"action": "openPanel", "panel": "station"},
            ]
            if intent == "timetable_query":
                instructions.append({"action": "openModal", "modal": "timetable", "stationId": str(sid)})
            # Build a station dict for the frontend to cache (with routes from detail)
            station_data = {
                "id": sid,
                "name": name,
                "city": city,
                "province": rich_station.get("province"),
                "category": rich_station.get("category", "small_passenger"),
                "lon": rich_station.get("lon", 0),
                "lat": rich_station.get("lat", 0),
                "routes": rich_station.get("passingTrains") or rich_station.get("routes"),
            }
            return f"**{name}**，{city}。详细信息已在左侧面板展示。", instructions, station_data
    return "抱歉，未找到该车站的信息。", [], None


def _format_train_result(tool_results: list[dict]) -> tuple[str, list[dict], dict | None]:
    for r in tool_results:
        if r.get("tool") == "get_train_route":
            train = r.get("train", {})
            no = train.get("trainNo", "")
            from_s = _nested_get(train, "fromStation", "name", default="")
            to_s = _nested_get(train, "toStation", "name", default="")
            stops = train.get("stops", [])
            # Build station-like data for the origin station
            station_data = None
            from_station = train.get("fromStation")
            if from_station and from_station.get("id"):
                station_data = {
                    "id": from_station.get("id"),
                    "name": from_s,
                    "city": from_station.get("city", ""),
                    "province": from_station.get("province"),
                    "category": from_station.get("category", "major_passenger"),
                    "lon": from_station.get("lon", 0),
                    "lat": from_station.get("lat", 0),
                }
            return (
                f"**{no}** 次列车，{from_s} → {to_s}，共 {len(stops)} 站。\n\n线路已在地图高亮显示。",
                [
                    {"action": "highlightTrain", "trainNo": no},
                    {"action": "openPanel", "panel": "train"},
                ],
                station_data,
            )
    return "抱歉，未找到该车次的信息。", [], None


def _format_route_result(tool_results: list[dict], relax_history: list[dict], constraints: dict) -> tuple[str, list[dict], list[dict] | None]:
    from .relax import format_relax_diff

    for r in tool_results:
        if r.get("tool") == "search_transfer":
            routes = r.get("routes", [])
            count = r.get("count", len(routes))

            if count == 0:
                return "抱歉，没找到符合条件的中转路线。" + format_relax_diff(relax_history), [], None

            lines = [f"从 **{constraints.get('from')}** 到 **{constraints.get('to')}**，找到 {count} 条路线：\n"]
            for i, route in enumerate(routes[:5]):
                label = f"方案{i + 1}"
                seg_texts = []
                for seg in route.get("segments", []):
                    if seg.get("trainNo"):
                        seg_texts.append(f"{seg['from']} —{seg['trainNo']}→ {seg['to']}")
                lines.append(f"**{label}**：{' → '.join(seg_texts)}")
                dur = route.get("totalDurationMin", 0)
                transfers = route.get("transfers", 0)
                lines.append(f"⏱ {dur // 60}h{dur % 60}min · 🔄 {transfers} 次换乘\n")

            if count > 5:
                lines.append(f"\n…还有 {count - 5} 条方案，可以进一步筛选。")

            diff_text = format_relax_diff(relax_history)
            route_ids = [r.get("id", f"plan-{i}") for i, r in enumerate(routes[:3])]
            instructions = [{"action": "highlightRoutes", "routeIds": route_ids}]

            # Return routes for frontend to cache
            return "\n".join(lines) + diff_text, instructions, routes[:3]

    return "抱歉，路线规划失败，请稍后重试。", [], None


def _format_isochrone_result(tool_results: list[dict], constraints: dict) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") == "get_isochrone":
            result = r.get("result", {})
            station_id = r.get("stationId", "")
            hours = r.get("hours", 0)
            groups = result.get("directionGroups", {})
            total = result.get("totalReachable", 0)

            if not groups:
                return f"从该站出发 {hours} 小时内可达约 {total} 个站点。", [
                    {"action": "highlightIsochrone", "stationId": str(station_id)},
                ]

            dir_names = {"east": "东", "south": "南", "west": "西", "north": "北",
                         "northeast": "东北", "northwest": "西北", "southeast": "东南", "southwest": "西南"}
            parts = []
            for d, cities in groups.items():
                label = dir_names.get(d, d)
                if cities:
                    example = cities[0] if isinstance(cities[0], str) else cities[0].get("name", "")
                    parts.append(f"往**{label}**（{example}方向）{len(cities)} 站")

            return (
                f"从该站出发 **{hours}** 小时内可达 {total} 个站点：\n\n" + "\n".join(parts) + "\n\n你想去哪个方向？我可以帮你规划具体路线。",
                [{"action": "highlightIsochrone", "stationId": str(station_id)}],
            )

    return "等时圈查询暂不可用，请稍后再试。", []
