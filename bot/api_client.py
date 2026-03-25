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

    async def place_stars_order(self, username: str, quantity: int) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/client/orders/stars",
                        headers=self.headers,
                        json={"username": username.replace("@", ""), "quantity": quantity},
                        timeout=15
                    )
                    return response.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def place_premium_order(self, username: str, months: int) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/client/orders/premium",
                        headers=self.headers,
                        json={"username": username.replace("@", ""), "months": months},
                        timeout=15
                    )
                    return response.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def get_nft_collections(self) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/client/rent/nft/collections",
                        headers=self.headers,
                        timeout=10
                    )
                    return response.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def get_nft_list(self, collection_address: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        async with self.limiter:
            try:
                params = {"collection_address": collection_address}
                if cursor:
                    params["cursor"] = cursor
                    
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/client/rent/nft/list",
                        headers=self.headers,
                        params=params,
                        timeout=15
                    )
                    data = response.json()
                    if data.get("success") and "items" in data:
                        for item in data["items"]:
                            if "price_per_day_rub" in item:
                                item["price_per_day_rub_with_margin"] = self._apply_margin(item["price_per_day_rub"])
                    return data
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def get_nft_rate(self, nft_address: str, days: int = 1) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/client/rent/nft/rate",
                        headers=self.headers,
                        params={"nft_address": nft_address, "days": days},
                        timeout=10
                    )
                    data = response.json()
                    if data.get("success"):
                        if "price_per_day_rub" in data:
                            data["price_per_day_rub_with_margin"] = self._apply_margin(data["price_per_day_rub"])
                        if "total_rub" in data:
                            data["total_rub_with_margin"] = self._apply_margin(data["total_rub"])
                    return data
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def place_nft_rent_order(self, nft_address: str, days: int) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/client/orders/rent/nft",
                        headers=self.headers,
                        json={"nft_address": nft_address, "days": days},
                        timeout=20
                    )
                    return response.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def connect_nft_rent(self, transaction_id: int, tonconnect_url: str) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/client/orders/rent/connect",
                        headers=self.headers,
                        json={"transaction_id": transaction_id, "tonconnect_url": tonconnect_url},
                        timeout=15
                    )
                    return response.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def get_order_status(self, order_id: int) -> Dict[str, Any]:
        async with self.limiter:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/client/orders/{order_id}",
                    headers=self.headers
                )
                return response.json()

    async def get_stars_items(self) -> Dict[str, Any]:
        async with self.limiter:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/client/stars/items",
                        headers=self.headers,
                        timeout=10
                    )
                    data = response.json()
                    if data.get("success") and "items" in data:
                        for item in data["items"]:
                            if "price_rub" in item:
                                item["price_rub_with_margin"] = self._apply_margin(item["price_rub"])
                    return data
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def get_nft_items(self, nft_type: str) -> Dict[str, Any]:
        """
        nft_type: 'gifts', 'usernames', 'numbers'
        """
        async with self.limiter:
            # Try multiple common endpoint patterns to find the correct one
            endpoints = [
                f"{self.base_url}/api/v1/client/nft/{nft_type}",
                f"{self.base_url}/api/v1/client/nft/items?type={nft_type}",
                f"{self.base_url}/api/v1/client/nft/items?category={nft_type}"
            ]
            
            last_error = "Unknown error"
            for url in endpoints:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, headers=self.headers, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                # Apply margin to prices if they exist in the response
                                if "items" in data:
                                    for item in data["items"]:
                                        if "price_rub" in item:
                                            item["price_rub_with_margin"] = self._apply_margin(item["price_rub"])
                                return data
                        elif response.status_code != 404:
                            # If it's not a 404, maybe there's a real issue with this endpoint
                            last_error = f"HTTP {response.status_code}"
                except Exception as e:
                    last_error = str(e)
            
            return {"success": False, "error": last_error}
