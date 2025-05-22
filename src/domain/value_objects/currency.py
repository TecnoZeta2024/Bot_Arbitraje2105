"""
Currency Value Object - Represents a cryptocurrency or fiat currency.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Currency:
    """
    Value object representing a currency.
    
    Immutable object that encapsulates currency information
    and enforces business rules about valid currencies.
    """
    
    symbol: str
    name: Optional[str] = None
    decimals: int = 8
    
    def __post_init__(self):
        """Validate currency after initialization."""
        if not self.symbol:
            raise ValueError("Currency symbol cannot be empty")
        
        if len(self.symbol) < 2 or len(self.symbol) > 10:
            raise ValueError("Currency symbol must be between 2 and 10 characters")
        
        if not self.symbol.isupper():
            raise ValueError("Currency symbol must be uppercase")
        
        if self.decimals < 0 or self.decimals > 18:
            raise ValueError("Currency decimals must be between 0 and 18")
    
    def is_stablecoin(self) -> bool:
        """Check if this is a stablecoin."""
        stablecoins = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD", "USDP"}
        return self.symbol in stablecoins
    
    def is_fiat(self) -> bool:
        """Check if this is a fiat currency."""
        fiat_currencies = {"USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "KRW"}
        return self.symbol in fiat_currencies
    
    def is_major_crypto(self) -> bool:
        """Check if this is a major cryptocurrency."""
        major_cryptos = {"BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOT", "MATIC"}
        return self.symbol in major_cryptos
    
    def __str__(self) -> str:
        """String representation."""
        return self.symbol
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Currency(symbol='{self.symbol}', name='{self.name}', decimals={self.decimals})"
