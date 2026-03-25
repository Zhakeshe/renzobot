import httpx
import asyncio
from aiolimiter import AsyncLimiter
from typing import Optional, Dict, Any

class APIClient:
    def __init__(self, base_url: str, token: str, margin: float = 1.15):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # 30 requests per 60 seconds (1 request per 2 seconds average)
        self.limiter = AsyncLimiter(30, 60)
        self.margin = margin
        self._stars_rate_cache = None
        self._stars_rate_expiry = 0

    def _apply_margin(self, price_rub: float) -> float:
        return round(price_rub * self.margin, 2)

    def nano_to_rub(self, nano: int) -> float:
        return nano / 1_000_000_000

    async def get_balance(self) -> Dict[str, Any]:
        async with self.limiter:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/client/balance",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()

    async def get_stars_rate(self) -> Dict[str, Any]:
        import time
        if self._stars_rate_cache and time.time() < self._stars_rate_expiry:
            return self._stars_rate_cache

        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/client/stars/rate",
                        headers=self.headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Apply margin to the price
                    if data.get("success"):
                        raw_price = data["price_per_star_rub"]
                        data["price_per_star_rub_with_margin"] = self._apply_margin(raw_price)
                        self._stars_rate_cache = data
                        self._stars_rate_expiry = time.time() + 300 # 5 min cache
                    
                    return data
            except Exception:
                if self._stars_rate_cache:
                    return self._stars_rate_cache
                raise

    async def get_stars_items(self) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/client/stars/items",
                        headers=self.headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                    if data.get("success") and "items" in data:
                        for item in data["items"]:
                            if "price_rub" in item:
                                item["price_rub_with_margin"] = self._apply_margin(item["price_rub"])
                    return data
            except Exception:
                return {"success": False}

    async def get_order_status(self, order_id: int) -> Dict[str, Any]:
        async with self.limiter:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/client/orders/{order_id}",
                    headers=self.headers
                )
                return response.json()

    async def get_nft_items(self, nft_type: str) -> Dict[str, Any]:
        """
        nft_type: 'gifts', 'usernames', 'numbers'
        """
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    # Endpoint pattern: /api/v1/client/nft/{type}
                    response = await client.get(
                        f"{self.base_url}/api/v1/client/nft/{nft_type}",
                        headers=self.headers,
                        timeout=15
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Apply margin to prices if they exist in the response
                    if data.get("success") and "items" in data:
                        for item in data["items"]:
                            if "price_rub" in item:
                                item["price_rub_with_margin"] = self._apply_margin(item["price_rub"])
                    
                    return data
            except Exception as e:
                return {"success": False, "error": str(e)}
