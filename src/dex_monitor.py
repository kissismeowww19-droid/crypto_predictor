"""DexScreener API integration for monitoring new token pairs."""
import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


class DexMonitor:
    """Monitor DexScreener for new token pairs across networks."""
    
    # DexScreener API endpoints
    BASE_URL = "https://api.dexscreener.com/latest"
    
    def __init__(self, networks: List[str]):
        """Initialize DexScreener monitor.
        
        Args:
            networks: List of network names to monitor (e.g., ['bsc', 'eth', 'solana', 'base'])
        """
        self.networks = networks
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _fetch_pairs(self, network: str) -> List[Dict[str, Any]]:
        """Fetch new pairs for a specific network.
        
        Args:
            network: Network name (bsc, eth, solana, base, etc.)
            
        Returns:
            List of pair data dictionaries
        """
        endpoint = f"{self.BASE_URL}/dex/pairs/{network}"
        
        try:
            response = await self.client.get(endpoint)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "60"))
                logger.warning(f"Rate limited on {network}, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return []
            
            response.raise_for_status()
            data = response.json()
            
            # DexScreener returns pairs in 'pairs' key
            pairs = data.get("pairs", []) if isinstance(data, dict) else []
            logger.debug(f"Fetched {len(pairs)} pairs from {network}")
            return pairs
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {network} pairs: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {network} pairs: {e}")
            return []
    
    async def scan_all_networks(self) -> List[Dict[str, Any]]:
        """Scan all configured networks for new pairs.
        
        Returns:
            List of all pairs across all networks
        """
        tasks = [self._fetch_pairs(network) for network in self.networks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_pairs = []
        for network, result in zip(self.networks, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {network}: {result}")
            elif isinstance(result, list):
                all_pairs.extend(result)
        
        return all_pairs
    
    @staticmethod
    def check_pump_signal(
        pair: Dict[str, Any],
        thresh_price: float,
        thresh_vol_ratio: float,
        thresh_liq_usd: float,
    ) -> Optional[Dict[str, Any]]:
        """Check if a pair meets pump signal criteria.
        
        Args:
            pair: Pair data from DexScreener
            thresh_price: Minimum price change % for m5
            thresh_vol_ratio: Minimum volume ratio (m5 vs h6)
            thresh_liq_usd: Minimum liquidity in USD
            
        Returns:
            Signal data dict if criteria met, None otherwise
        """
        try:
            # Extract key metrics
            price_change = pair.get("priceChange", {}).get("m5", 0)
            volume_m5 = pair.get("volume", {}).get("m5", 0)
            volume_h6 = pair.get("volume", {}).get("h6", 0)
            liquidity_usd = pair.get("liquidity", {}).get("usd", 0)
            
            # Calculate volume ratio (m5 represents 5 minutes, volume_h6 is total 6-hour volume)
            # h6 represents 6 hours = 360 minutes = 72 five-minute periods
            # We compare current 5-min volume against average 5-min volume in last 6h
            volume_ratio = 0
            if volume_h6 > 0:
                avg_5min_volume = volume_h6 / 72  # Average 5-min volume from 6h total
                if avg_5min_volume > 0:
                    volume_ratio = volume_m5 / avg_5min_volume
            
            # Check all thresholds
            if (
                price_change > thresh_price
                and volume_ratio > thresh_vol_ratio
                and liquidity_usd > thresh_liq_usd
            ):
                return {
                    "pair_address": pair.get("pairAddress", ""),
                    "chain": pair.get("chainId", ""),
                    "dex": pair.get("dexId", ""),
                    "base_token": pair.get("baseToken", {}).get("symbol", ""),
                    "quote_token": pair.get("quoteToken", {}).get("symbol", ""),
                    "price_usd": pair.get("priceUsd", "0"),
                    "price_change_m5": price_change,
                    "volume_m5": volume_m5,
                    "volume_ratio": volume_ratio,
                    "liquidity_usd": liquidity_usd,
                    "url": pair.get("url", ""),
                }
        except Exception as e:
            logger.debug(f"Error checking pump signal: {e}")
        
        return None
    
    async def check_honeypot(self, pair_address: str, chain: str) -> bool:
        """Placeholder for honeypot check.
        
        This is a hook for future integration with honeypot detection APIs.
        Currently returns False (not a honeypot) as it's disabled by default.
        
        Args:
            pair_address: Token pair contract address
            chain: Blockchain network
            
        Returns:
            True if honeypot detected, False otherwise
        """
        # TODO: Integrate with a free honeypot detection API when available
        # Example services: honeypot.is, tokensniffer.com
        # For now, always return False
        return False
