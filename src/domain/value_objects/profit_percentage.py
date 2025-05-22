"""
ProfitPercentage Value Object - Represents a profit percentage with validation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Union


@dataclass(frozen=True)
class ProfitPercentage:
    """
    Value object representing a profit percentage.
    
    Immutable object that ensures profit percentage consistency
    and provides methods for profit calculations.
    """
    
    value: float  # Percentage value (e.g., 2.5 for 2.5%)
    
    def __post_init__(self):
        """Validate profit percentage after initialization."""
        if not isinstance(self.value, (int, float)):
            raise TypeError("Profit percentage value must be a number")
        
        # Convert to float if needed
        if isinstance(self.value, int):
            object.__setattr__(self, 'value', float(self.value))
        
        # Business rule: reasonable profit percentage range
        if self.value < -100.0:
            raise ValueError("Profit percentage cannot be less than -100%")
        
        if self.value > 10000.0:  # 100x profit seems unreasonable
            raise ValueError("Profit percentage cannot exceed 10000%")
    
    def __add__(self, other: 'ProfitPercentage') -> 'ProfitPercentage':
        """Add two profit percentages."""
        if not isinstance(other, ProfitPercentage):
            raise TypeError("Can only add ProfitPercentage objects")
        
        return ProfitPercentage(self.value + other.value)
    
    def __sub__(self, other: 'ProfitPercentage') -> 'ProfitPercentage':
        """Subtract two profit percentages."""
        if not isinstance(other, ProfitPercentage):
            raise TypeError("Can only subtract ProfitPercentage objects")
        
        return ProfitPercentage(self.value - other.value)
    
    def __mul__(self, factor: Union[int, float]) -> 'ProfitPercentage':
        """Multiply profit percentage by a factor."""
        if not isinstance(factor, (int, float)):
            raise TypeError("Can only multiply by numbers")
        
        return ProfitPercentage(self.value * factor)
    
    def __truediv__(self, divisor: Union[int, float]) -> 'ProfitPercentage':
        """Divide profit percentage by a divisor."""
        if not isinstance(divisor, (int, float)):
            raise TypeError("Can only divide by numbers")
        
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        
        return ProfitPercentage(self.value / divisor)
    
    def __lt__(self, other: 'ProfitPercentage') -> bool:
        """Less than comparison."""
        if not isinstance(other, ProfitPercentage):
            raise TypeError("Can only compare ProfitPercentage objects")
        
        return self.value < other.value
    
    def __le__(self, other: 'ProfitPercentage') -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, ProfitPercentage):
            raise TypeError("Can only compare ProfitPercentage objects")
        
        return self.value <= other.value
    
    def __gt__(self, other: 'ProfitPercentage') -> bool:
        """Greater than comparison."""
        if not isinstance(other, ProfitPercentage):
            raise TypeError("Can only compare ProfitPercentage objects")
        
        return self.value > other.value
    
    def __ge__(self, other: 'ProfitPercentage') -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, ProfitPercentage):
            raise TypeError("Can only compare ProfitPercentage objects")
        
        return self.value >= other.value
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, ProfitPercentage):
            return False
        
        # Use small epsilon for float comparison
        return abs(self.value - other.value) < 1e-9
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        # Round to avoid floating point precision issues
        return hash(round(self.value, 9))
    
    def is_positive(self) -> bool:
        """Check if profit percentage is positive."""
        return self.value > 0
    
    def is_negative(self) -> bool:
        """Check if profit percentage is negative (loss)."""
        return self.value < 0
    
    def is_zero(self) -> bool:
        """Check if profit percentage is zero (break-even)."""
        return abs(self.value) < 1e-9
    
    def is_significant(self, threshold: float = 0.01) -> bool:
        """Check if profit percentage is significant (above threshold)."""
        return abs(self.value) >= threshold
    
    def exceeds_threshold(self, threshold: float) -> bool:
        """Check if profit percentage exceeds a given threshold."""
        return self.value > threshold
    
    def as_decimal(self) -> Decimal:
        """Convert to decimal representation (e.g., 2.5% -> 0.025)."""
        return Decimal(str(self.value)) / 100
    
    def as_multiplier(self) -> Decimal:
        """Convert to multiplier representation (e.g., 2.5% -> 1.025)."""
        return Decimal("1") + self.as_decimal()
    
    def apply_to_amount(self, amount: Union[Decimal, float]) -> Decimal:
        """Apply profit percentage to an amount."""
        if isinstance(amount, float):
            amount = Decimal(str(amount))
        
        return amount * self.as_multiplier()
    
    def calculate_profit_amount(self, principal: Union[Decimal, float]) -> Decimal:
        """Calculate the profit amount from a principal."""
        if isinstance(principal, float):
            principal = Decimal(str(principal))
        
        return principal * self.as_decimal()
    
    def round_to_precision(self, decimal_places: int) -> 'ProfitPercentage':
        """Round profit percentage to specified decimal places."""
        if decimal_places < 0:
            raise ValueError("Decimal places cannot be negative")
        
        rounded_value = round(self.value, decimal_places)
        return ProfitPercentage(rounded_value)
    
    def to_basis_points(self) -> int:
        """Convert to basis points (1% = 100 basis points)."""
        return int(self.value * 100)
    
    def risk_adjusted(self, risk_factor: float) -> 'ProfitPercentage':
        """Apply risk adjustment to profit percentage."""
        if risk_factor < 0 or risk_factor > 1:
            raise ValueError("Risk factor must be between 0 and 1")
        
        adjusted_value = self.value * risk_factor
        return ProfitPercentage(adjusted_value)
    
    @classmethod
    def from_decimal(cls, decimal_value: Decimal) -> 'ProfitPercentage':
        """Create from decimal representation (e.g., 0.025 -> 2.5%)."""
        percentage_value = float(decimal_value * 100)
        return cls(percentage_value)
    
    @classmethod
    def from_basis_points(cls, basis_points: int) -> 'ProfitPercentage':
        """Create from basis points (e.g., 250 basis points -> 2.5%)."""
        percentage_value = float(basis_points) / 100
        return cls(percentage_value)
    
    @classmethod
    def from_ratio(cls, new_value: Union[Decimal, float], old_value: Union[Decimal, float]) -> 'ProfitPercentage':
        """Create from ratio of new value to old value."""
        if isinstance(new_value, float):
            new_value = Decimal(str(new_value))
        if isinstance(old_value, float):
            old_value = Decimal(str(old_value))
        
        if old_value == 0:
            if new_value == 0:
                return cls(0.0)
            else:
                raise ValueError("Cannot calculate percentage from zero base value")
        
        ratio = (new_value - old_value) / old_value
        percentage_value = float(ratio * 100)
        return cls(percentage_value)
    
    @classmethod
    def zero(cls) -> 'ProfitPercentage':
        """Create zero profit percentage."""
        return cls(0.0)
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.value:.4f}%"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ProfitPercentage({self.value}%)"
