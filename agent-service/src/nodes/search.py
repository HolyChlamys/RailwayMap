import asyncio
from ..state import AgentState
from ..tools import ALL_TOOLS


async def search(state: AgentState) -> dict:
    intent = state.get("intent", "clarify")
    constraints = state.get("constraints") or {}
    tasks = []

    if intent == "station_query" or intent == "timetable_query":
        name = constraints.get("stationName") or constraints.get("from") or constraints.get("to") or constraints.get("query")
        if name:
            tasks.append(("search_stations", ALL_TOOLS["search_stations"](name)))
        elif constraints.get("stationId"):
            tasks.append(("get_station_detail", ALL_TOOLS["get_station_detail"](constraints["stationId"])))

    elif intent == "train_query":
        train_no = constraints.get("trainNo") or constraints.get("from")
        if train_no:
            tasks.append(("get_train_route", ALL_TOOLS["get_train_route"](train_no)))

    elif intent == "isochrone":
        station_id = constraints.get("stationId")
        hours = constraints.get("hours", 4)
        if station_id:
            tasks.append(("get_isochrone", ALL_TOOLS["get_isochrone"](station_id, hours)))
        if not station_id and constraints.get("stationName"):
            tasks.append(("search_stations", ALL_TOOLS["search_stations"](constraints["stationName"])))

    elif intent == "route_planning":
        if constraints.get("from") and constraints.get("to"):
            tasks.append(("search_transfer", ALL_TOOLS["search_transfer"](constraints)))

    # Run all tasks in parallel
    tool_results = []
    if tasks:
        names, coros = zip(*tasks)
        results = await asyncio.gather(*coros, return_exceptions=True)
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                tool_results.append({"tool": name, "params": {}, "result": None, "error": str(result)})
            else:
                tool_results.append(result)

    return {"tool_results": tool_results}
