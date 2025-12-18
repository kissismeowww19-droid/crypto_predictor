"""Alert cache to prevent duplicate notifications."""
import time
from typing import Dict, Set


class AlertCache:
    """Cache for tracking alerted pairs to prevent spam."""
    
    def __init__(self, antispam_seconds: int = 900):
        """Initialize alert cache.
        
        Args:
            antispam_seconds: Time window in seconds to prevent duplicate alerts
        """
        self.antispam_seconds = antispam_seconds
        self._cache: Dict[str, float] = {}  # pair_address -> timestamp
    
    def should_alert(self, pair_address: str) -> bool:
        """Check if we should alert for this pair.
        
        Args:
            pair_address: The pair contract address
            
        Returns:
            True if we should alert, False if within antispam window
        """
        current_time = time.time()
        
        if pair_address in self._cache:
            time_since_last_alert = current_time - self._cache[pair_address]
            if time_since_last_alert < self.antispam_seconds:
                return False
        
        # Update cache with current timestamp
        self._cache[pair_address] = current_time
        return True
    
    def cleanup(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._cache.items()
            if current_time - timestamp > self.antispam_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get_cached_count(self) -> int:
        """Get number of cached pairs."""
        return len(self._cache)
