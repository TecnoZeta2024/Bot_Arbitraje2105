"""
Opportunity Entity - Represents a triangular arbitrage opportunity.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from ..value_objects.currency import Currency
from ..value_objects.price import Price
from ..value_objects.profit_percentage import ProfitPercentage


class OpportunityStatus(Enum):
    """Status of an arbitrage opportunity."""
    DETECTED = "DETECTED"
    ANALYZING = "ANALYZING"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


@dataclass
class Opportunity:
    """
    Domain entity representing a triangular arbitrage opportunity.
    
    This entity encapsulates all the business rules and behavior
    related to arbitrage opportunities.
    """
    
    # Identity
    opportunity_id: str
    
    # Core opportunity data
    base_currency: Currency
    intermediate_currency: Currency 
    quote_currency: Currency
    
    # Financial data
    estimated_profit_percentage: ProfitPercentage
    required_capital: Decimal
    expected_profit: Decimal
    
    # Market data
    first_pair_price: Price
    second_pair_price: Price
    third_pair_price: Price
    
    # Metadata
    detection_timestamp: datetime
    status: OpportunityStatus
    expiry_timestamp: Optional[datetime] = None
    confidence_score: Optional[float] = None
    risk_score: Optional[float] = None
    
    def __post_init__(self):
        """Validate business rules after initialization."""
        self._validate_currencies()
        self._validate_profit_threshold()
        self._validate_capital_requirements()
    
    def _validate_currencies(self) -> None:
        """Ensure currencies form a valid triangular path."""
        currencies = {self.base_currency, self.intermediate_currency, self.quote_currency}
        if len(currencies) != 3:
            raise ValueError("Opportunity must involve exactly three different currencies")
    
    def _validate_profit_threshold(self) -> None:
        """Ensure profit meets minimum threshold."""
        if self.estimated_profit_percentage.value <= 0:
            raise ValueError("Profit percentage must be positive")
    
    def _validate_capital_requirements(self) -> None:
        """Ensure capital requirements are realistic."""
        if self.required_capital <= 0:
            raise ValueError("Required capital must be positive")
        
        # Business rule: minimum capital requirement
        MIN_CAPITAL = Decimal("10.0")  # Minimum 10 USDT
        if self.required_capital < MIN_CAPITAL:
            raise ValueError(f"Required capital must be at least {MIN_CAPITAL}")
    
    def is_expired(self) -> bool:
        """Check if the opportunity has expired."""
        if self.expiry_timestamp is None:
            return False
        return datetime.utcnow() > self.expiry_timestamp
    
    def is_executable(self) -> bool:
        """Check if the opportunity can be executed."""
        return (
            self.status == OpportunityStatus.APPROVED and
            not self.is_expired() and
            self.estimated_profit_percentage.value > 0
        )
    
    def mark_as_executing(self) -> None:
        """Mark opportunity as being executed."""
        if not self.is_executable():
            raise ValueError("Opportunity is not in executable state")
        self.status = OpportunityStatus.EXECUTING
    
    def mark_as_completed(self) -> None:
        """Mark opportunity as completed."""
        if self.status != OpportunityStatus.EXECUTING:
            raise ValueError("Can only complete an executing opportunity")
        self.status = OpportunityStatus.COMPLETED
    
    def mark_as_failed(self) -> None:
        """Mark opportunity as failed."""
        if self.status not in [OpportunityStatus.EXECUTING, OpportunityStatus.APPROVED]:
            raise ValueError("Can only fail an executing or approved opportunity")
        self.status = OpportunityStatus.FAILED
    
    def approve(self) -> None:
        """Approve the opportunity for execution."""
        if self.status != OpportunityStatus.PENDING_CONFIRMATION:
            raise ValueError("Can only approve opportunities pending confirmation")
        if self.is_expired():
            raise ValueError("Cannot approve expired opportunity")
        self.status = OpportunityStatus.APPROVED
    
    def reject(self) -> None:
        """Reject the opportunity."""
        if self.status not in [OpportunityStatus.PENDING_CONFIRMATION, OpportunityStatus.DETECTED]:
            raise ValueError("Can only reject pending or detected opportunities")
        self.status = OpportunityStatus.REJECTED
    
    def get_trading_path(self) -> List[str]:
        """Get the trading path as a list of currency symbols."""
        return [
            self.base_currency.symbol,
            self.intermediate_currency.symbol,
            self.quote_currency.symbol,
            self.base_currency.symbol  # Complete the cycle
        ]
    
    def get_required_pairs(self) -> List[str]:
        """Get the trading pairs required for this opportunity."""
        return [
            f"{self.base_currency.symbol}{self.intermediate_currency.symbol}",
            f"{self.intermediate_currency.symbol}{self.quote_currency.symbol}",
            f"{self.quote_currency.symbol}{self.base_currency.symbol}"
        ]
    
    def calculate_slippage_impact(self, slippage_percentage: float) -> ProfitPercentage:
        """Calculate the impact of slippage on profitability."""
        # Simple slippage calculation - can be enhanced with more sophisticated models
        adjusted_profit = self.estimated_profit_percentage.value - (slippage_percentage * 3)  # 3 trades
        return ProfitPercentage(max(0.0, adjusted_profit))
    
    def __str__(self) -> str:
        """String representation of the opportunity."""
        path = " -> ".join(self.get_trading_path())
        return (f"Opportunity {self.opportunity_id}: {path} "
                f"({self.estimated_profit_percentage.value:.4f}% profit)")
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on opportunity ID."""
        if not isinstance(other, Opportunity):
            return False
        return self.opportunity_id == other.opportunity_id
    
    def __hash__(self) -> int:
        """Hash based on opportunity ID."""
        return hash(self.opportunity_id)
