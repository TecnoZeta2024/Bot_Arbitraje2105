"""
MarketDataFetcher - Single responsibility for fetching market data.
"""

from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
import time

from ...domain.entities.market_data import MarketData
from ...domain.value_objects.currency import Currency
from ...utils.logger import get_logger


class IMarketDataFetcher(ABC):
    """Interface for market data fetching."""
    
    @abstractmethod
    async def fetch_symbols(self, limit: Optional[int] = None) -> List[str]:
        """Fetch available trading symbols."""
        pass
    
    @abstractmethod
    async def fetch_tickers(self, symbols: Optional[List[str]] = None) -> Dict[str, float]:
        """Fetch price tickers for symbols."""
        pass
    
    @abstractmethod
    async def fetch_market_data(
        self, 
        symbols: List[str], 
        include_volume: bool = True
    ) -> List[MarketData]:
        """Fetch comprehensive market data."""
        pass


class MarketDataFetcher:
    """
    Responsible ONLY for fetching market data from external sources.
    
    Applies Single Responsibility Principle - this class has only one reason to change:
    when the way we fetch market data changes.
    """
    
    def __init__(self, binance_client, mobula_client):
        self._binance_client = binance_client
        self._mobula_client = mobula_client
        self._logger = get_logger(self.__class__.__name__)
    
    async def fetch_symbols_and_tickers(
        self, 
        token_search_limit: int = 400,
        prefer_mobula: bool = True
    ) -> Tuple[List[str], Dict[str, float]]:
        """
        Fetch symbols and tickers from available sources.
        
        Args:
            token_search_limit: Maximum number of tokens to fetch
            prefer_mobula: Whether to prefer Mobula for symbols
            
        Returns:
            Tuple of (symbols, tickers)
        """
        self._logger.info("=== FETCHING MARKET DATA ===")
        self._logger.info(f"Parameters: limit={token_search_limit}, prefer_mobula={prefer_mobula}")
        
        symbols = []
        tickers = {}
        
        # Fetch symbols
        symbols = await self._fetch_symbols(token_search_limit, prefer_mobula)
        if not symbols:
            self._logger.error("Failed to fetch symbols from any source")
            return [], {}
        
        # Fetch tickers (always from Binance for price accuracy)
        tickers = await self._fetch_tickers_from_binance()
        if not tickers:
            self._logger.error("Failed to fetch tickers from Binance")
            return symbols, {}
        
        self._logger.info(f"Successfully fetched {len(symbols)} symbols and {len(tickers)} tickers")
        return symbols, tickers
    
    async def _fetch_symbols(self, limit: int, prefer_mobula: bool) -> List[str]:
        """Fetch symbols from preferred source with fallback."""
        symbols = []
        
        if prefer_mobula:
            # Try Mobula first
            symbols = await self._fetch_symbols_from_mobula(limit)
            if not symbols:
                self._logger.warning("Mobula symbol fetch failed, falling back to Binance")
                symbols = await self._fetch_symbols_from_binance()
        else:
            # Try Binance first
            symbols = await self._fetch_symbols_from_binance()
            if not symbols:
                self._logger.warning("Binance symbol fetch failed, falling back to Mobula")
                symbols = await self._fetch_symbols_from_mobula(limit)
        
        return symbols
    
    async def _fetch_symbols_from_mobula(self, limit: int) -> List[str]:
        """Fetch symbols from Mobula API."""
        try:
            self._logger.info(f"Fetching symbols from Mobula (limit: {limit})")
            
            mobula_tokens = self._mobula_client.obtener_tokens_top(limit=limit)
            if not mobula_tokens:
                self._logger.warning("Mobula returned no tokens")
                return []
            
            symbols = [token.get("symbol") for token in mobula_tokens if token.get("symbol")]
            symbols = symbols[:limit]  # Ensure we don't exceed limit
            
            self._logger.info(f"Fetched {len(symbols)} symbols from Mobula")
            return symbols
            
        except Exception as e:
            self._logger.error(f"Error fetching symbols from Mobula: {e}")
            return []
    
    async def _fetch_symbols_from_binance(self) -> List[str]:
        """Fetch symbols from Binance API."""
        try:
            self._logger.info("Fetching symbols from Binance")
            
            symbols = self._binance_client.obtener_simbolos_trading()
            if not symbols:
                self._logger.warning("Binance returned no symbols")
                return []
            
            self._logger.info(f"Fetched {len(symbols)} symbols from Binance")
            return symbols
            
        except Exception as e:
            self._logger.error(f"Error fetching symbols from Binance: {e}")
            return []
    
    async def _fetch_tickers_from_binance(self) -> Dict[str, float]:
        """Fetch price tickers from Binance."""
        try:
            self._logger.info("Fetching tickers from Binance")
            
            tickers = self._binance_client.obtener_precios_todos()
            if not tickers:
                self._logger.warning("Binance returned no tickers")
                return {}
            
            # Filter valid tickers (positive prices)
            valid_tickers = {
                symbol: price 
                for symbol, price in tickers.items() 
                if price is not None and price > 0
            }
            
            self._logger.info(f"Fetched {len(valid_tickers)} valid tickers from Binance")
            return valid_tickers
            
        except Exception as e:
            self._logger.error(f"Error fetching tickers from Binance: {e}")
            return {}
    
    async def validate_market_data_quality(
        self, 
        symbols: List[str], 
        tickers: Dict[str, float]
    ) -> Tuple[List[str], Dict[str, float]]:
        """
        Validate and filter market data for quality.
        
        Args:
            symbols: List of symbols to validate
            tickers: Dictionary of tickers to validate
            
        Returns:
            Tuple of (validated_symbols, validated_tickers)
        """
        self._logger.info("Validating market data quality")
        
        # Find symbols that have valid tickers
        valid_symbols = []
        valid_tickers = {}
        
        symbols_with_tickers = 0
        
        for symbol in symbols:
            if symbol in tickers and tickers[symbol] > 0:
                valid_symbols.append(symbol)
                valid_tickers[symbol] = tickers[symbol]
                symbols_with_tickers += 1
        
        # If we have very few matching symbols, try alternative matching
        if symbols_with_tickers < 10:
            self._logger.warning(f"Only {symbols_with_tickers} symbols have tickers, trying flexible matching")
            
            # Add tickers that don't have matching symbols but are valid
            for ticker_symbol, price in tickers.items():
                if price > 0 and ticker_symbol not in valid_tickers:
                    valid_symbols.append(ticker_symbol)
                    valid_tickers[ticker_symbol] = price
        
        self._logger.info(f"Validation complete: {len(valid_symbols)} valid symbols with tickers")
        
        return valid_symbols, valid_tickers
    
    def get_fetch_statistics(self) -> Dict[str, any]:
        """Get statistics about the last fetch operation."""
        # This could track success rates, latencies, etc.
        return {
            "last_fetch_time": time.time(),
            "sources_available": {
                "binance": self._binance_client is not None,
                "mobula": self._mobula_client is not None
            }
        }
