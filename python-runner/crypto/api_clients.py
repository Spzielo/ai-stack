"""
External API clients for Crypto One-Glance module.
Handles communication with CoinGecko, DefiLlama, and TokenUnlocks.
"""

import logging
import os
from typing import Dict, List, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """Client for CoinGecko API."""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["x-cg-pro-api-key"] = self.api_key
    
    async def get_coin_data(self, coin_id: str) -> Optional[Dict]:
        """
        Get current market data for a coin.
        Returns: {price_usd, market_cap, volume_24h, ...}
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/{coin_id}",
                    headers=self.headers,
                    params={
                        "localization": "false",
                        "tickers": "false",
                        "community_data": "false",
                        "developer_data": "false",
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                market_data = data.get("market_data", {})
                
                return {
                    "price_usd": market_data.get("current_price", {}).get("usd"),
                    "market_cap": market_data.get("market_cap", {}).get("usd"),
                    "volume_24h": market_data.get("total_volume", {}).get("usd"),
                    "price_change_24h": market_data.get("price_change_percentage_24h"),
                    "price_change_7d": market_data.get("price_change_percentage_7d"),
                    "raw": data,
                }
        except httpx.HTTPError as e:
            logger.error(f"CoinGecko API error for {coin_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching CoinGecko data for {coin_id}: {e}")
            return None
    
    async def get_batch_prices(self, coin_ids: List[str]) -> Dict[str, Dict]:
        """
        Get current prices for multiple coins in one request.
        Returns: {coin_id: {price_usd, market_cap, volume_24h}}
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/markets",
                    headers=self.headers,
                    params={
                        "vs_currency": "usd",
                        "ids": ",".join(coin_ids),
                        "order": "market_cap_desc",
                        "per_page": 250,
                        "page": 1,
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                result = {}
                for coin in data:
                    result[coin["id"]] = {
                        "price_usd": coin.get("current_price"),
                        "market_cap": coin.get("market_cap"),
                        "volume_24h": coin.get("total_volume"),
                        "price_change_24h": coin.get("price_change_percentage_24h"),
                        "price_change_7d": coin.get("price_change_percentage_7d"),
                    }
                
                return result
        except httpx.HTTPError as e:
            logger.error(f"CoinGecko batch API error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching CoinGecko batch data: {e}")
            return {}


class DefiLlamaClient:
    """Client for DefiLlama API."""
    
    BASE_URL = "https://api.llama.fi"
    
    async def get_protocol_tvl(self, slug: str) -> Optional[Dict]:
        """
        Get TVL data for a DeFi protocol.
        Returns: {tvl, tvl_change_24h, ...}
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.BASE_URL}/protocol/{slug}")
                response.raise_for_status()
                data = response.json()
                
                # Get current TVL (most recent data point)
                tvl_data = data.get("tvl", [])
                current_tvl = tvl_data[-1]["totalLiquidityUSD"] if tvl_data else None
                
                # Get 24h change
                tvl_24h_ago = tvl_data[-2]["totalLiquidityUSD"] if len(tvl_data) > 1 else None
                tvl_change_24h = None
                if current_tvl and tvl_24h_ago:
                    tvl_change_24h = ((current_tvl - tvl_24h_ago) / tvl_24h_ago) * 100
                
                return {
                    "tvl": current_tvl,
                    "tvl_change_24h": tvl_change_24h,
                    "chain_tvls": data.get("chainTvls", {}),
                    "raw": data,
                }
        except httpx.HTTPError as e:
            logger.error(f"DefiLlama API error for {slug}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching DefiLlama data for {slug}: {e}")
            return None
    
    async def get_protocol_fees(self, slug: str) -> Optional[Dict]:
        """
        Get fees and revenue data for a protocol.
        Returns: {fees_24h, revenue_24h, ...}
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try fees endpoint
                response = await client.get(f"https://api.llama.fi/summary/fees/{slug}")
                response.raise_for_status()
                data = response.json()
                
                return {
                    "fees_24h": data.get("total24h"),
                    "revenue_24h": data.get("totalRevenue24h"),
                    "raw": data,
                }
        except httpx.HTTPError as e:
            logger.warning(f"DefiLlama fees API error for {slug}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching DefiLlama fees for {slug}: {e}")
            return None


class TokenUnlocksClient:
    """Client for TokenUnlocks API."""
    
    BASE_URL = "https://api.token.unlocks.app"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TOKENUNLOCKS_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def get_upcoming_unlocks(self, token_id: str, days: int = 90) -> Optional[List[Dict]]:
        """
        Get upcoming token unlocks.
        Returns: [{date, amount, percentage, ...}]
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Note: This is a placeholder - actual API endpoint may differ
                # TokenUnlocks may not have a public API, might need web scraping
                response = await client.get(
                    f"{self.BASE_URL}/unlocks/{token_id}",
                    headers=self.headers,
                    params={"days": days},
                )
                response.raise_for_status()
                data = response.json()
                
                unlocks = []
                for unlock in data.get("unlocks", []):
                    unlocks.append({
                        "date": unlock.get("date"),
                        "amount": unlock.get("amount"),
                        "percentage": unlock.get("percentage"),
                        "description": unlock.get("description"),
                    })
                
                return unlocks
        except httpx.HTTPError as e:
            logger.warning(f"TokenUnlocks API error for {token_id}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching TokenUnlocks data for {token_id}: {e}")
            return None


# Singleton instances
coingecko_client = CoinGeckoClient()
defillama_client = DefiLlamaClient()
tokenunlocks_client = TokenUnlocksClient()
