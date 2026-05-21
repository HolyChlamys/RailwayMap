import httpx
from ..config import settings


async def search_stations(query: str) -> dict:
    """Search stations by name/pinyin. Retries without common suffixes if no results."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/search",
            params={"q": query},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data if isinstance(data, list) else data.get("data", [])

        # Retry without common suffixes if no results
        if not results:
            for suffix in ("站", "火车站", "高铁站"):
                if query.endswith(suffix) and len(query) > len(suffix):
                    retry_q = query[:-len(suffix)]
                    resp = await client.get(
                        f"{settings.java_base_url}/api/stations/search",
                        params={"q": retry_q},
                    )
                    resp.raise_for_status()
                    retry_data = resp.json()
                    results = retry_data if isinstance(retry_data, list) else retry_data.get("data", [])
                    if results:
                        break

        return {"tool": "search_stations", "stations": results, "count": len(results)}


async def get_station_detail(station_id: str) -> dict:
    """Get station detail including passing trains."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/stations/{station_id}",
        )
        resp.raise_for_status()
        return {"tool": "get_station_detail", "station": resp.json()}
