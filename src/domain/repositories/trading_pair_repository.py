"""
Repository interface for trading pair operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..value_objects.currency import Currency


class ITradingPairRepository(ABC):
    """
    Abstract repository interface for trading pair operations.
    """
    
    @abstractmethod
    async def get_all_pairs(self) -> List[str]:
        """
        Get all available trading pairs.
        
        Returns:
            List of trading pair symbols (e.g., ["BTCUSDT", "ETHUSDT"])
        """
        pass
    
    @abstractmethod
    async def get_pairs_by_base_currency(self, base_currency: Currency) -> List[str]:
        """
        Get trading pairs that have the specified base currency.
        
        Args:
            base_currency: Base currency to filter by
            
        Returns:
            List of trading pair symbols with the specified base currency
        """
        pass
    
    @abstractmethod
    async def get_pairs_by_quote_currency(self, quote_currency: Currency) -> List[str]:
        """
        Get trading pairs that have the specified quote currency.
        
        Args:
            quote_currency: Quote currency to filter by
            
        Returns:
            List of trading pair symbols with the specified quote currency
        """
        pass
    
    @abstractmethod
    async def is_pair_supported(self, base_currency: Currency, quote_currency: Currency) -> bool:
        """
        Check if a trading pair is supported.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            
        Returns:
            True if the pair is supported, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_pair_info(self, base_currency: Currency, quote_currency: Currency) -> Optional[dict]:
        """
        Get detailed information about a trading pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            
        Returns:
            Dictionary with pair information or None if not found
        """
        pass
    
    @abstractmethod
    async def get_minimum_order_size(self, base_currency: Currency, quote_currency: Currency) -> Optional[float]:
        """
        Get minimum order size for a trading pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            
        Returns:
            Minimum order size or None if not available
        """
        pass
    
    @abstractmethod
    async def get_tick_size(self, base_currency: Currency, quote_currency: Currency) -> Optional[float]:
        """
        Get tick size (minimum price increment) for a trading pair.
        
        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            
        Returns:
            Tick size or None if not available
        """
        pass
    
    @abstractmethod
    async def refresh_pairs(self) -> int:
        """
        Refresh the list of available trading pairs from the exchange.
        
        Returns:
            Number of pairs updated/added
        """
        pass
