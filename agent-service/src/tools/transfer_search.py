import httpx
from ..config import settings


async def search_transfer(constraints: dict) -> dict:
    """Call POST /api/transfer/search with structured constraints."""
    async with httpx.AsyncClient(timeout=30) as client:
        body = {
            "from": constraints.get("from"),
            "to": constraints.get("to"),
        }
        if constraints.get("via"):
            body["waypoints"] = [constraints["via"]]
        if constraints.get("maxTransfers") is not None:
            body["maxTransfers"] = constraints["maxTransfers"]
        if constraints.get("trainTypes"):
            body["preferTrainTypes"] = constraints["trainTypes"]
        if constraints.get("dMax"):
            body["maxSegmentDuration"] = constraints["dMax"]
        if constraints.get("tStart") or constraints.get("tEnd"):
            body["departAfter"] = _minutes_to_time(constraints.get("tStart"))
            body["arriveBefore"] = _minutes_to_time(constraints.get("tEnd"))

        resp = await client.post(
            f"{settings.java_base_url}/api/transfer/search",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        routes = data if isinstance(data, list) else data.get("data", data.get("routes", []))
        return {"tool": "search_transfer", "params": body, "routes": routes, "count": len(routes)}


def _minutes_to_time(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"
