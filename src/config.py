"""Configuration management for the crypto pump alert bot."""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration from environment variables."""
    
    # Telegram settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    CHAT_ID: str = os.getenv("CHAT_ID", "")
    
    # Network settings
    NETWORKS: List[str] = os.getenv("NETWORKS", "bsc,eth,solana,base").split(",")
    
    # Alert thresholds
    THRESH_PRICE: float = float(os.getenv("THRESH_PRICE", "8.0"))  # % change in m5
    THRESH_VOL_RATIO: float = float(os.getenv("THRESH_VOL_RATIO", "3.0"))  # m5 vs avg 5m over h6
    THRESH_LIQ_USD: float = float(os.getenv("THRESH_LIQ_USD", "30000"))  # minimum liquidity
    
    # Polling settings
    POLL_INTERVAL_SEC: int = int(os.getenv("POLL_INTERVAL_SEC", "45"))
    ANTISPAM_SECONDS: int = int(os.getenv("ANTISPAM_SECONDS", "900"))  # 15 minutes
    
    # Honeypot check (disabled by default)
    HONEYPOT_CHECK_ENABLED: bool = os.getenv("HONEYPOT_CHECK_ENABLED", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not cls.CHAT_ID:
            raise ValueError("CHAT_ID is required")
        if cls.POLL_INTERVAL_SEC < 30:
            raise ValueError("POLL_INTERVAL_SEC must be at least 30 seconds")
