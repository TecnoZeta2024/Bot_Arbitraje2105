"""
Concrete implementation of IMarketDataRepository using Supabase and external APIs.
"""

from datetime import datetime
from typing import Dict, List, Optional

from ...domain.repositories.market_data_repository import IMarketDataRepository
from ...domain.value_objects.currency import Currency
from ...domain.value_objects.price import Price
from ...utils.logger import get_logger
from ..external_apis.supabase_client import SupabaseClient


class MarketDataRepositoryImpl(IMarketDataRepository):
    """
    Concrete implementation of market data repository using Supabase and external APIs.
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self._supabase = supabase_client
        self._logger = get_logger(self.__class__.__name__)
        self._market_data_table = "market_data"
    
    async def get_current_price(self, base_currency: Currency, quote_currency: Currency) -> Optional[Price]:
        """
        Get current price for a currency pair.
        """
        try:
            # This is a mock implementation
            # In production, this would fetch from real market data APIs
            self._logger.info(f"Getting current price for {base_currency.symbol}/{quote_currency.symbol}")
            
            # Mock price data
            from decimal import Decimal
            mock_price = Decimal("50000.0")  # Mock BTC price
            
            return Price(mock_price, quote_currency)
            
        except Exception as e:
            self._logger.error(f"Error getting current price: {e}")
            return None
    
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
        """
        try:
            self._logger.info(
                f"Getting historical prices for {base_currency.symbol}/{quote_currency.symbol} "
                f"from {start_time} to {end_time} with interval {interval}"
            )
            
            # Mock historical data
            return [
                {
                    "timestamp": start_time.isoformat(),
                    "open": 50000.0,
                    "high": 51000.0,
                    "low": 49000.0,
                    "close": 50500.0,
                    "volume": 1000.0
                }
            ]
            
        except Exception as e:
            self._logger.error(f"Error getting historical prices: {e}")
            return []
    
    async def get_order_book(
        self, 
        base_currency: Currency, 
        quote_currency: Currency,
        depth: int = 10
    ) -> Dict:
        """
        Get order book for a currency pair.
        """
        try:
            self._logger.info(
                f"Getting order book for {base_currency.symbol}/{quote_currency.symbol} "
                f"with depth {depth}"
            )
            
            # Mock order book data
            return {
                "bids": [
                    {"price": 49950.0, "quantity": 0.1},
                    {"price": 49900.0, "quantity": 0.2}
                ],
                "asks": [
                    {"price": 50050.0, "quantity": 0.1},
                    {"price": 50100.0, "quantity": 0.2}
                ]
            }
            
        except Exception as e:
            self._logger.error(f"Error getting order book: {e}")
            return {"bids": [], "asks": []}
    
    async def get_volume_24h(self, base_currency: Currency, quote_currency: Currency) -> Optional[float]:
        """
        Get 24-hour trading volume for a currency pair.
        """
        try:
            self._logger.info(f"Getting 24h volume for {base_currency.symbol}/{quote_currency.symbol}")
            
            # Mock volume data
            return 1000000.0
            
        except Exception as e:
            self._logger.error(f"Error getting 24h volume: {e}")
            return None
    
    async def is_market_open(self, base_currency: Currency, quote_currency: Currency) -> bool:
        """
        Check if market is open for trading for a currency pair.
        """
        try:
            self._logger.info(f"Checking if market is open for {base_currency.symbol}/{quote_currency.symbol}")
            
            # Crypto markets are always open
            return True
            
        except Exception as e:
            self._logger.error(f"Error checking market status: {e}")
            return False
    
    async def get_supported_pairs(self) -> List[str]:
        """
        Get list of supported trading pairs.
        """
        try:
            self._logger.info("Getting supported trading pairs")
            
            # Mock supported pairs
            return [
                "BTCUSDT",
                "ETHUSDT",
                "ADAUSDT",
                "DOTUSDT",
                "LINKUSDT"
            ]
            
        except Exception as e:
            self._logger.error(f"Error getting supported pairs: {e}")
            return []
