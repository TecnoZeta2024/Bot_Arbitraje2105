"""
Price Value Object - Represents a price with currency information.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Union

from .currency import Currency


@dataclass(frozen=True)
class Price:
    """
    Value object representing a price amount with its currency.
    
    Immutable object that ensures price consistency and provides
    arithmetic operations with proper currency handling.
    """
    
    amount: Decimal
    currency: Currency
    
    def __post_init__(self):
        """Validate price after initialization."""
        if not isinstance(self.amount, Decimal):
            # Convert to Decimal if not already
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        
        if self.amount < 0:
            raise ValueError("Price amount cannot be negative")
        
        if not isinstance(self.currency, Currency):
            raise ValueError("Currency must be a Currency instance")
    
    def __add__(self, other: 'Price') -> 'Price':
        """Add two prices (must be same currency)."""
        if not isinstance(other, Price):
            raise TypeError("Can only add Price objects")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot add prices of different currencies: {self.currency} vs {other.currency}")
        
        return Price(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: 'Price') -> 'Price':
        """Subtract two prices (must be same currency)."""
        if not isinstance(other, Price):
            raise TypeError("Can only subtract Price objects")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract prices of different currencies: {self.currency} vs {other.currency}")
        
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Price subtraction cannot result in negative amount")
        
        return Price(result_amount, self.currency)
    
    def __mul__(self, factor: Union[Decimal, int, float]) -> 'Price':
        """Multiply price by a factor."""
        if not isinstance(factor, (Decimal, int, float)):
            raise TypeError("Price can only be multiplied by numbers")
        
        if isinstance(factor, (int, float)):
            factor = Decimal(str(factor))
        
        if factor < 0:
            raise ValueError("Cannot multiply price by negative factor")
        
        return Price(self.amount * factor, self.currency)
    
    def __truediv__(self, divisor: Union[Decimal, int, float]) -> 'Price':
        """Divide price by a divisor."""
        if not isinstance(divisor, (Decimal, int, float)):
            raise TypeError("Price can only be divided by numbers")
        
        if isinstance(divisor, (int, float)):
            divisor = Decimal(str(divisor))
        
        if divisor <= 0:
            raise ValueError("Cannot divide price by zero or negative number")
        
        return Price(self.amount / divisor, self.currency)
    
    def __rmul__(self, factor: Union[Decimal, int, float]) -> 'Price':
        """Right multiplication (factor * price)."""
        return self.__mul__(factor)
    
    def __lt__(self, other: 'Price') -> bool:
        """Less than comparison (must be same currency)."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price objects")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare prices of different currencies: {self.currency} vs {other.currency}")
        
        return self.amount < other.amount
    
    def __le__(self, other: 'Price') -> bool:
        """Less than or equal comparison (must be same currency)."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price objects")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare prices of different currencies: {self.currency} vs {other.currency}")
        
        return self.amount <= other.amount
    
    def __gt__(self, other: 'Price') -> bool:
        """Greater than comparison (must be same currency)."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price objects")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare prices of different currencies: {self.currency} vs {other.currency}")
        
        return self.amount > other.amount
    
    def __ge__(self, other: 'Price') -> bool:
        """Greater than or equal comparison (must be same currency)."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price objects")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare prices of different currencies: {self.currency} vs {other.currency}")
        
        return self.amount >= other.amount
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, Price):
            return False
        
        return self.amount == other.amount and self.currency == other.currency
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.amount, self.currency))
    
    def is_zero(self) -> bool:
        """Check if price is zero."""
        return self.amount == 0
    
    def percentage_change(self, other: 'Price') -> Decimal:
        """Calculate percentage change from this price to another."""
        if not isinstance(other, Price):
            raise TypeError("Can only calculate percentage change with Price objects")
        
        if self.currency != other.currency:
            raise ValueError(f"Cannot calculate percentage change for different currencies: {self.currency} vs {other.currency}")
        
        if self.amount == 0:
            if other.amount == 0:
                return Decimal("0")
            else:
                raise ValueError("Cannot calculate percentage change from zero price")
        
        return ((other.amount - self.amount) / self.amount) * 100
    
    def round_to_precision(self, precision: int) -> 'Price':
        """Round price to specified decimal places."""
        if precision < 0:
            raise ValueError("Precision cannot be negative")
        
        rounded_amount = self.amount.quantize(Decimal(f"0.{'0' * precision}"))
        return Price(rounded_amount, self.currency)
    
    def to_float(self) -> float:
        """Convert price amount to float (use with caution for display only)."""
        return float(self.amount)
    
    def to_string(self, precision: int = None) -> str:
        """Convert to string with optional precision."""
        if precision is None:
            return f"{self.amount} {self.currency.symbol}"
        else:
            rounded_price = self.round_to_precision(precision)
            return f"{rounded_price.amount} {self.currency.symbol}"
    
    @classmethod
    def zero(cls, currency: Currency) -> 'Price':
        """Create a zero price for a given currency."""
        return cls(Decimal("0"), currency)
    
    @classmethod
    def from_float(cls, amount: float, currency: Currency) -> 'Price':
        """Create price from float (use with caution)."""
        return cls(Decimal(str(amount)), currency)
    
    @classmethod
    def from_string(cls, amount_str: str, currency: Currency) -> 'Price':
        """Create price from string representation."""
        try:
            amount = Decimal(amount_str)
            return cls(amount, currency)
        except Exception as e:
            raise ValueError(f"Invalid price string '{amount_str}': {e}")
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.amount} {self.currency.symbol}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Price(amount={self.amount}, currency={self.currency.symbol})"
