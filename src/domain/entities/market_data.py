"""
Market Data Entity - Represents real-time market data
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal


@dataclass(frozen=True)
class PriceData:
    """Price data for a specific timestamp"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    
    @property
    def ohlc_tuple(self) -> tuple:
        """Return OHLC as tuple for calculations"""
        return (float(self.open), float(self.high), float(self.low), float(self.close))


@dataclass(frozen=True)
class OrderBookLevel:
    """Single level of order book (bid or ask)"""
    price: Decimal
    quantity: Decimal
    
    @property
    def value(self) -> Decimal:
        """Calculate total value at this level"""
        return self.price * self.quantity


@dataclass(frozen=True)
class OrderBook:
    """Order book data for a symbol"""
    timestamp: datetime
    symbol: str
    bids: List[OrderBookLevel]  # Sorted by price descending
    asks: List[OrderBookLevel]  # Sorted by price ascending
    
    @property
    def best_bid(self) -> Optional[OrderBookLevel]:
        """Get best bid price"""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[OrderBookLevel]:
        """Get best ask price"""
        return self.asks[0] if self.asks else None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread"""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return None
    
    @property
    def spread_percentage(self) -> Optional[Decimal]:
        """Calculate spread as percentage of mid price"""
        if self.spread and self.best_ask:
            return (self.spread / self.best_ask.price) * 100
        return None
    
    @property
    def liquidity_score(self) -> Decimal:
        """Calculate liquidity score based on top 5 levels"""
        top_bids = sum(level.quantity for level in self.bids[:5])
        top_asks = sum(level.quantity for level in self.asks[:5])
        return (top_bids + top_asks) / 2


@dataclass(frozen=True)
class MarketData:
    """Complete market data for a symbol"""
    symbol: str
    exchange: str
    timestamp: datetime
    
    # Current price data
    current_price: Decimal
    price_24h_ago: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    
    # Historical price data
    price_history: Optional[List[PriceData]] = None
    
    # Order book
    order_book: Optional[OrderBook] = None
    
    # Technical indicators (calculated separately)
    technical_indicators: Optional[Dict[str, Any]] = None
    
    # Market conditions
    volatility: Optional[Decimal] = None
    trend_strength: Optional[Decimal] = None
    
    @property
    def price_change_24h(self) -> Optional[Decimal]:
        """Calculate 24h price change percentage"""
        if self.price_24h_ago and self.price_24h_ago > 0:
            return ((self.current_price - self.price_24h_ago) / self.price_24h_ago) * 100
        return None
    
    @property
    def is_liquid(self) -> bool:
        """Check if market has sufficient liquidity"""
        if self.order_book:
            return self.order_book.liquidity_score > Decimal('1000')  # Configurable threshold
        return False
    
    @property
    def has_tight_spread(self) -> bool:
        """Check if spread is tight (< 0.1%)"""
        if self.order_book and self.order_book.spread_percentage:
            return self.order_book.spread_percentage < Decimal('0.1')
        return False
    
    def get_indicator_value(self, indicator_name: str) -> Optional[Any]:
        """Get specific technical indicator value"""
        if self.technical_indicators:
            return self.technical_indicators.get(indicator_name)
        return None
