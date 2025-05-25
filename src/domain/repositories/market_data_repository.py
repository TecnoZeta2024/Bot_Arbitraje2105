"""
Repository interface for market data operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from ..value_objects.currency import Currency
from ..value_objects.price import Price


class IMarketDataRepository(ABC):
    """
    Abstract repository interface for market data operations.
    """
    
    @abstractmethod
    async def get_current_price(self, base_currency: Currency, quote_currency: Currency) -> Optional[Price]:
        """
        Get current price for a currency pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            
        Returns:
            Current price or None if not available
        """
        pass
    
    @abstractmethod
    async def get_historical_prices(
        self, 
        base_currency: Currency, 
        quote_currency: Currency,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1h"
    ) -> List[Dict]:
        """
        Get historical prices for a currency pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            start_time: Start time
            end_time: End time
            interval: Price interval (1m, 5m, 1h, etc.)
            
        Returns:
            List of historical price data
        """
        pass
    
    @abstractmethod
    async def get_order_book(
        self, 
        base_currency: Currency, 
        quote_currency: Currency,
        depth: int = 10
    ) -> Dict:
        """
        Get order book for a currency pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            depth: Number of price levels to return
            
        Returns:
            Order book data with bids and asks
        """
        pass
    
    @abstractmethod
    async def get_volume_24h(self, base_currency: Currency, quote_currency: Currency) -> Optional[float]:
        """
        Get 24-hour trading volume for a currency pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            
        Returns:
            24-hour volume or None if not available
        """
        pass
    
    @abstractmethod
    async def is_market_open(self, base_currency: Currency, quote_currency: Currency) -> bool:
        """
        Check if market is open for trading for a currency pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            
        Returns:
            True if market is open, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_supported_pairs(self) -> List[str]:
        """
        Get list of supported trading pairs.
        
        Returns:
            List of supported trading pair symbols
        """
        pass
