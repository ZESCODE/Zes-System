"""Async REST API client."""
from typing import Optional, Dict, Any
import aiohttp


class RESTAPISkill:
    def __init__(self, base_url: str = "", default_headers: Optional[Dict] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout

    async def request(self, method: str, endpoint: str = "", **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url and endpoint else f"{self.base_url}{endpoint}"
        headers = {**self.default_headers, **kwargs.pop("headers", {})}
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.request(method, url, **kwargs) as resp:
                    try:
                        data = await resp.json()
                    except Exception:
                        data = await resp.text()
                    return {"success": True, "status": resp.status, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get(self, endpoint: str = "", **kwargs) -> Dict[str, Any]:
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str = "", **kwargs) -> Dict[str, Any]:
        return await self.request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str = "", **kwargs) -> Dict[str, Any]:
        return await self.request("PUT", endpoint, **kwargs)

    async def patch(self, endpoint: str = "", **kwargs) -> Dict[str, Any]:
        return await self.request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str = "", **kwargs) -> Dict[str, Any]:
        return await self.request("DELETE", endpoint, **kwargs)
