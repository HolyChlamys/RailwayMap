from ..state import AgentState


async def format_reply(state: AgentState) -> dict:
    intent = state.get("intent", "clarify")
    tool_results = state.get("tool_results", [])
    relax_history = state.get("relax_history", [])
    constraints = state.get("constraints") or {}
    instructions = []
    suggestions = []

    if intent == "station_query" or intent == "timetable_query":
        reply_text, instructions = _format_station_result(tool_results, intent)
    elif intent == "train_query":
        reply_text, instructions = _format_train_result(tool_results)
    elif intent == "route_planning":
        reply_text, instructions = _format_route_result(tool_results, relax_history, constraints)
        suggestions = ["只看高铁", "最少换乘", "尝试其他时间段"]
    elif intent == "isochrone":
        reply_text, instructions = _format_isochrone_result(tool_results, constraints)
        suggestions = ["细看哪个方向？", "从这些城市中选一个目的地规划路线"]
    else:
        reply_text = "有什么我可以帮你的？"

    return {
        "reply_text": reply_text,
        "instructions": instructions,
        "suggestions": suggestions,
    }


def _format_station_result(tool_results: list[dict], intent: str) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") in ("search_stations", "get_station_detail", "get_station_timetable"):
            station = r.get("station") or (r.get("stations", [None])[0] if r.get("stations") else None)
            if not station:
                continue
            name = station.get("name", "未知站")
            city = station.get("city", "")
            sid = station.get("id")
            instructions = [
                {"action": "flyToStation", "stationId": str(sid)},
                {"action": "openPanel", "panel": "station"},
            ]
            if intent == "timetable_query":
                instructions.append({"action": "openModal", "modal": "timetable", "stationId": str(sid)})
            return f"**{name}**，{city}。详细信息已在左侧面板展示。", instructions
    return "抱歉，未找到该车站的信息。", []


def _format_train_result(tool_results: list[dict]) -> tuple[str, list[dict]]:
    for r in tool_results:
        if r.get("tool") == "get_train_route":
            train = r.get("train", {})
            no = train.get("trainNo", "")
            from_s = train.get("fromStation", {}).get("name", "")
            to_s = train.get("toStation", {}).get("name", "")
            stops = train.get("stops", [])
            return (
                f"**{no}** 次列车，{from_s} → {to_s}，共 {len(stops)} 站。\n\n线路已在地图高亮显示。",
                [
                    {"action": "highlightTrain", "trainNo": no},
                    {"action": "openPanel", "panel": "train"},
                ],
            )
    return "抱歉，未找到该车次的信息。", []


def _format_route_result(tool_results: list[dict], relax_history: list[dict], constraints: dict) -> tuple[str, list[dict]]:
    from .relax import format_relax_diff

    for r in tool_results:
        if r.get("tool") == "search_transfer":
            routes = r.get("routes", [])
            count = r.get("count", len(routes))

            if count == 0:
                return "抱歉，没找到符合条件的中转路线。" + format_relax_diff(relax_history), []

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

            return "\n".join(lines) + diff_text, instructions

    return "抱歉，路线规划失败，请稍后重试。", []


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
