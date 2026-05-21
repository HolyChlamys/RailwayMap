import httpx
from ..config import settings


async def get_station_timetable(station_id: str) -> dict:
    """Get all trains passing through a station (timetable)."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/{station_id}",
        )
        resp.raise_for_status()
        return {"tool": "get_station_timetable", "station": resp.json()}
