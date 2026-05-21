import httpx
from ..config import settings


async def get_train_route(train_no: str) -> dict:
    """Get train route with stops and schedule."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.java_base_url}/api/trains/{train_no}/route",
        )
        resp.raise_for_status()
        return {"tool": "get_train_route", "train": resp.json()}
