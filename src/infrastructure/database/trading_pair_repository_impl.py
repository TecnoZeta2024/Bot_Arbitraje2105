"""
Concrete implementation of ITradingPairRepository using Binance API and Supabase.
"""

from typing import List, Optional

from ...domain.repositories.trading_pair_repository import ITradingPairRepository
from ...domain.value_objects.currency import Currency
from ...utils.logger import get_logger
from ..external_apis.binance_client import BinanceClient
from ..external_apis.supabase_client import SupabaseClient


class TradingPairRepositoryImpl(ITradingPairRepository):
    """
    Concrete implementation of trading pair repository using Binance API and Supabase.
    """
    
    def __init__(self, binance_client: BinanceClient, supabase_client: SupabaseClient):
        self._binance = binance_client
        self._supabase = supabase_client
        self._logger = get_logger(self.__class__.__name__)
        self._pairs_table = "trading_pairs"
    
    async def get_all_pairs(self) -> List[str]:
        """
        Get all available trading pairs.
        """
        try:
            # Mock implementation - in production this would fetch from Binance API
            self._logger.info("Getting all trading pairs")
            
            return [
                "BTCUSDT",
                "ETHUSDT",
                "ADAUSDT",
                "DOTUSDT",
                "LINKUSDT",
                "BNBUSDT",
                "SOLUSDT",
                "AVAXUSDT",
                "MATICUSDT",
                "ATOMUSDT"
            ]
            
        except Exception as e:
            self._logger.error(f"Error getting all pairs: {e}")
            return []
    
    async def get_pairs_by_base_currency(self, base_currency: Currency) -> List[str]:
        """
        Get trading pairs that have the specified base currency.
        """
        try:
            self._logger.info(f"Getting pairs for base currency: {base_currency.symbol}")
            
            all_pairs = await self.get_all_pairs()
            return [pair for pair in all_pairs if pair.startswith(base_currency.symbol)]
            
        except Exception as e:
            self._logger.error(f"Error getting pairs by base currency: {e}")
            return []
    
    async def get_pairs_by_quote_currency(self, quote_currency: Currency) -> List[str]:
        """
        Get trading pairs that have the specified quote currency.
        """
        try:
            self._logger.info(f"Getting pairs for quote currency: {quote_currency.symbol}")
            
            all_pairs = await self.get_all_pairs()
            return [pair for pair in all_pairs if pair.endswith(quote_currency.symbol)]
            
        except Exception as e:
            self._logger.error(f"Error getting pairs by quote currency: {e}")
            return []
    
    async def is_pair_supported(self, base_currency: Currency, quote_currency: Currency) -> bool:
        """
        Check if a trading pair is supported.
        """
        try:
            pair_symbol = f"{base_currency.symbol}{quote_currency.symbol}"
            all_pairs = await self.get_all_pairs()
            
            return pair_symbol in all_pairs
            
        except Exception as e:
            self._logger.error(f"Error checking pair support: {e}")
            return False
    
    async def get_pair_info(self, base_currency: Currency, quote_currency: Currency) -> Optional[dict]:
        """
        Get detailed information about a trading pair.
        """
        try:
            pair_symbol = f"{base_currency.symbol}{quote_currency.symbol}"
            self._logger.info(f"Getting pair info for: {pair_symbol}")
            
            # Mock pair information
            if await self.is_pair_supported(base_currency, quote_currency):
                return {
                    "symbol": pair_symbol,
                    "base_currency": base_currency.symbol,
                    "quote_currency": quote_currency.symbol,
                    "min_order_size": 0.001,
                    "tick_size": 0.01,
                    "status": "TRADING",
                    "permissions": ["SPOT"]
                }
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error getting pair info: {e}")
            return None
    
    async def get_minimum_order_size(self, base_currency: Currency, quote_currency: Currency) -> Optional[float]:
        """
        Get minimum order size for a trading pair.
        """
        try:
            pair_info = await self.get_pair_info(base_currency, quote_currency)
            
            if pair_info:
                return pair_info.get("min_order_size")
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error getting minimum order size: {e}")
            return None
    
    async def get_tick_size(self, base_currency: Currency, quote_currency: Currency) -> Optional[float]:
        """
        Get tick size (minimum price increment) for a trading pair.
        """
        try:
            pair_info = await self.get_pair_info(base_currency, quote_currency)
            
            if pair_info:
                return pair_info.get("tick_size")
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error getting tick size: {e}")
            return None
    
    async def refresh_pairs(self) -> int:
        """
        Refresh the list of available trading pairs from the exchange.
        """
        try:
            self._logger.info("Refreshing trading pairs from exchange")
            
            # Mock implementation - in production this would:
            # 1. Fetch latest pairs from Binance API
            # 2. Update the database
            # 3. Return count of updated pairs
            
            all_pairs = await self.get_all_pairs()
            return len(all_pairs)
            
        except Exception as e:
            self._logger.error(f"Error refreshing pairs: {e}")
            return 0
