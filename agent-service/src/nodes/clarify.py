import httpx
from ..state import AgentState
from ..config import settings

CLARIFY_TEMPLATES = {
    "from": "请问你想从哪里出发？",
    "to": "请问你的目的地是哪里？",
    "station_query": "你想查询哪个车站的信息？",
    "train_query": "你想查询哪趟车次？请输入车次号（如G1、D301）。",
    "hours": "你想查询几小时内的等时圈？",
}


async def _resolve_ambiguous_station(name: str) -> dict | None:
    """Check if station name is ambiguous by calling search API."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/search",
            params={"q": name},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("data", [])
        if len(results) > 1:
            return {"query": name, "candidates": [r.get("name") for r in results[:5]]}
        return None


async def clarify(state: AgentState) -> dict:
    missing = state.get("missing", [])
    reply_parts = []

    # Check for ambiguous station names first
    constraints = state.get("constraints") or {}
    ambiguous = []
    for field in ("from", "to", "via"):
        if constraints.get(field) and field not in missing:
            result = await _resolve_ambiguous_station(constraints[field])
            if result:
                ambiguous.append(result)

    if ambiguous:
        for a in ambiguous:
            candidates = "、".join(a["candidates"])
            reply_parts.append(f"「{a['query']}」有多个车站：{candidates}。你指的是哪个？")
    else:
        for field in missing:
            template = CLARIFY_TEMPLATES.get(field)
            if template:
                reply_parts.append(template)

    if not reply_parts:
        reply_parts.append("我没能完全理解你的需求，能再详细说说吗？")

    return {
        "reply_text": "\n\n".join(reply_parts),
        "instructions": [],
        "suggestions": ["查询车次", "查询车站", "路径规划"],
    }
