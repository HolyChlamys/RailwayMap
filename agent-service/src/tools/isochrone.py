import httpx
from ..config import settings


async def get_isochrone(station_id: str, hours: float) -> dict:
    """Call POST /api/isochrone to get reachable stations within N hours."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.java_base_url}/api/isochrone",
            json={"stationId": station_id, "hours": hours},
        )
        resp.raise_for_status()
        data = resp.json()
        return {"tool": "get_isochrone", "stationId": station_id, "hours": hours, "result": data}
