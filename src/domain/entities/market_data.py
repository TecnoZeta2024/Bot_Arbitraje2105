"""
Market Data Entity - Core market information
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MarketData:
    """
    Core market data entity
    """
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    spread: Optional[float] = None
    spread_percentage: Optional[float] = None
    volume_ratio: Optional[float] = None
    
    @property
    def is_liquid(self) -> bool:
        """Check if market has sufficient liquidity"""
        return self.volume > 100.0  # Simple liquidity check
