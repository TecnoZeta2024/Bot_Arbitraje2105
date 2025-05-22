"""
ExecutionStep Entity - Represents a single trading step in an arbitrage operation.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

from ..value_objects.currency import Currency
from ..value_objects.price import Price


class StepStatus(Enum):
    """Status of an execution step."""
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OrderSide(Enum):
    """Order side for trading."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type for trading."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


@dataclass
class ExecutionStep:
    """
    Domain entity representing a single execution step in an arbitrage operation.
    
    Each step represents one trade in the arbitrage sequence.
    """
    
    # Identity and order
    step_id: str
    step_number: int
    operation_id: str
    
    # Trading details
    trading_pair: str
    order_side: OrderSide
    order_type: OrderType
    
    # Quantities and prices
    requested_quantity: Decimal
    executed_quantity: Optional[Decimal] = None
    requested_price: Optional[Price] = None  # For limit orders
    executed_price: Optional[Price] = None
    
    # Currencies involved
    from_currency: Currency
    to_currency: Currency
    
    # Status and timing
    status: StepStatus = StepStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Financial details
    fee_amount: Optional[Decimal] = None
    fee_currency: Optional[Currency] = None
    slippage_percentage: Optional[float] = None
    
    # Exchange details
    exchange_order_id: Optional[str] = None
    exchange_trade_ids: list = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        """Initialize post-creation logic."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.exchange_trade_ids is None:
            self.exchange_trade_ids = []
        
        self._validate_step()
    
    def _validate_step(self) -> None:
        """Validate step business rules."""
        if self.step_number <= 0:
            raise ValueError("Step number must be positive")
        
        if self.requested_quantity <= 0:
            raise ValueError("Requested quantity must be positive")
        
        # Validate currency pair consistency
        expected_pair = f"{self.from_currency.symbol}{self.to_currency.symbol}"
        reverse_pair = f"{self.to_currency.symbol}{self.from_currency.symbol}"
        
        if self.trading_pair not in [expected_pair, reverse_pair]:
            raise ValueError(f"Trading pair {self.trading_pair} doesn't match currencies")
    
    def start_execution(self) -> None:
        """Mark step as started."""
        if self.status != StepStatus.PENDING:
            raise ValueError("Can only start pending steps")
        
        self.status = StepStatus.EXECUTING
        self.started_at = datetime.utcnow()
    
    def complete_successfully(
        self, 
        executed_quantity: Decimal, 
        executed_price: Price,
        fee_amount: Optional[Decimal] = None,
        exchange_order_id: Optional[str] = None,
        trade_ids: Optional[list] = None
    ) -> None:
        """Mark step as successfully completed."""
        if self.status != StepStatus.EXECUTING:
            raise ValueError("Can only complete executing steps")
        
        if executed_quantity <= 0:
            raise ValueError("Executed quantity must be positive")
        
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.executed_quantity = executed_quantity
        self.executed_price = executed_price
        
        if fee_amount is not None:
            self.fee_amount = fee_amount
            # Fee currency is typically the quote currency
            if self.order_side == OrderSide.BUY:
                self.fee_currency = self.to_currency
            else:
                self.fee_currency = self.from_currency
        
        if exchange_order_id:
            self.exchange_order_id = exchange_order_id
        
        if trade_ids:
            self.exchange_trade_ids.extend(trade_ids)
        
        # Calculate slippage if we had a target price
        if self.requested_price:
            self._calculate_slippage()
    
    def fail_step(self, error_message: str) -> None:
        """Mark step as failed."""
        if self.status not in [StepStatus.EXECUTING, StepStatus.PENDING]:
            raise ValueError("Can only fail executing or pending steps")
        
        self.status = StepStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def cancel_step(self, reason: str) -> None:
        """Cancel the step."""
        if self.status not in [StepStatus.PENDING, StepStatus.EXECUTING]:
            raise ValueError("Can only cancel pending or executing steps")
        
        self.status = StepStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.error_message = f"Cancelled: {reason}"
    
    def retry_step(self) -> None:
        """Retry a failed step."""
        if self.status != StepStatus.FAILED:
            raise ValueError("Can only retry failed steps")
        
        if self.retry_count >= self.max_retries:
            raise ValueError(f"Maximum retries ({self.max_retries}) exceeded")
        
        self.retry_count += 1
        self.status = StepStatus.PENDING
        self.error_message = None
        self.started_at = None
        self.completed_at = None
    
    def _calculate_slippage(self) -> None:
        """Calculate slippage based on requested vs executed price."""
        if not self.requested_price or not self.executed_price:
            return
        
        requested = self.requested_price.amount
        executed = self.executed_price.amount
        
        if requested == 0:
            return
        
        # Slippage calculation depends on order side
        if self.order_side == OrderSide.BUY:
            # For buy orders, slippage is positive if we paid more than expected
            slippage = ((executed - requested) / requested) * 100
        else:
            # For sell orders, slippage is positive if we received less than expected
            slippage = ((requested - executed) / requested) * 100
        
        self.slippage_percentage = float(slippage)
    
    def get_execution_duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def get_fill_percentage(self) -> float:
        """Get the percentage of the order that was filled."""
        if not self.executed_quantity:
            return 0.0
        
        return float((self.executed_quantity / self.requested_quantity) * 100)
    
    def is_successful(self) -> bool:
        """Check if the step was successfully completed."""
        return self.status == StepStatus.COMPLETED
    
    def is_partial_fill(self) -> bool:
        """Check if the step was partially filled."""
        return (
            self.is_successful() and 
            self.executed_quantity and 
            self.executed_quantity < self.requested_quantity
        )
    
    def get_effective_price(self) -> Optional[Price]:
        """Get the effective price including fees."""
        if not self.executed_price or not self.executed_quantity:
            return None
        
        if not self.fee_amount:
            return self.executed_price
        
        # Adjust price for fees
        if self.order_side == OrderSide.BUY:
            # For buy orders, add fee to the cost
            total_cost = (self.executed_price.amount * self.executed_quantity) + self.fee_amount
            effective_price = total_cost / self.executed_quantity
        else:
            # For sell orders, subtract fee from proceeds
            total_proceeds = (self.executed_price.amount * self.executed_quantity) - self.fee_amount
            effective_price = total_proceeds / self.executed_quantity
        
        return Price(effective_price, self.executed_price.currency)
    
    def get_step_summary(self) -> Dict[str, Any]:
        """Get a summary of the step execution."""
        return {
            "step_id": self.step_id,
            "step_number": self.step_number,
            "trading_pair": self.trading_pair,
            "order_side": self.order_side.value,
            "status": self.status.value,
            "requested_quantity": float(self.requested_quantity),
            "executed_quantity": float(self.executed_quantity) if self.executed_quantity else None,
            "executed_price": float(self.executed_price.amount) if self.executed_price else None,
            "fee_amount": float(self.fee_amount) if self.fee_amount else None,
            "slippage_percentage": self.slippage_percentage,
            "fill_percentage": self.get_fill_percentage(),
            "execution_duration": self.get_execution_duration(),
            "retry_count": self.retry_count,
            "error_message": self.error_message
        }
    
    def __str__(self) -> str:
        """String representation of the step."""
        return (f"Step {self.step_number}: {self.order_side.value} {self.requested_quantity} "
                f"{self.trading_pair} - {self.status.value}")
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on step ID."""
        if not isinstance(other, ExecutionStep):
            return False
        return self.step_id == other.step_id
    
    def __hash__(self) -> int:
        """Hash based on step ID."""
        return hash(self.step_id)
