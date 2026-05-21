import httpx
from ..config import settings


async def search_stations(query: str) -> dict:
    """Search stations by name/pinyin. Returns {stations: [...], count: N}."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/search",
            params={"q": query},
        )
        resp.raise_for_status()
        data = resp.json()
        return {"tool": "search_stations", "stations": data if isinstance(data, list) else data.get("data", []), "count": len(data) if isinstance(data, list) else 0}


async def get_station_detail(station_id: str) -> dict:
    """Get station detail including passing trains."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/{station_id}",
        )
        resp.raise_for_status()
        return {"tool": "get_station_detail", "station": resp.json()}
