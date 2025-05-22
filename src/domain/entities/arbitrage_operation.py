"""
ArbitrageOperation Entity - Represents the execution of an arbitrage opportunity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from ..value_objects.currency import Currency
from ..value_objects.price import Price
from .execution_step import ExecutionStep


class OperationStatus(Enum):
    """Status of an arbitrage operation execution."""
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PARTIAL = "PARTIAL"


class OperationType(Enum):
    """Type of operation."""
    TRIANGULAR_ARBITRAGE = "TRIANGULAR_ARBITRAGE"
    SIMPLE_ARBITRAGE = "SIMPLE_ARBITRAGE"
    TEST_OPERATION = "TEST_OPERATION"


@dataclass
class ArbitrageOperation:
    """
    Domain entity representing the execution of an arbitrage operation.
    
    Contains all execution details, results, and business logic
    related to the actual trading operation.
    """
    
    # Identity
    operation_id: str
    opportunity_id: str
    
    # Operation details
    operation_type: OperationType
    initial_capital: Decimal
    target_currency: Currency
    
    # Execution tracking
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    status: OperationStatus = OperationStatus.PENDING
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    final_amount: Optional[Decimal] = None
    actual_profit: Optional[Decimal] = None
    actual_profit_percentage: Optional[float] = None
    total_fees_paid: Decimal = field(default_factory=lambda: Decimal("0"))
    total_slippage: float = 0.0
    
    # Risk and compliance
    risk_assessment: Optional[Dict[str, Any]] = None
    compliance_checks: Optional[Dict[str, bool]] = None
    
    # Error tracking
    error_message: Optional[str] = None
    failed_step_index: Optional[int] = None
    
    def __post_init__(self):
        """Validate business rules after initialization."""
        self._validate_initial_capital()
        self._validate_operation_type()
    
    def _validate_initial_capital(self) -> None:
        """Validate initial capital meets requirements."""
        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        
        # Business rule: minimum capital for arbitrage
        MIN_CAPITAL = Decimal("10.0")
        if self.initial_capital < MIN_CAPITAL:
            raise ValueError(f"Initial capital must be at least {MIN_CAPITAL}")
    
    def _validate_operation_type(self) -> None:
        """Validate operation type is supported."""
        if self.operation_type not in OperationType:
            raise ValueError(f"Unsupported operation type: {self.operation_type}")
    
    def start_execution(self) -> None:
        """Mark the operation as started."""
        if self.status != OperationStatus.PENDING:
            raise ValueError("Can only start pending operations")
        
        self.status = OperationStatus.EXECUTING
        self.started_at = datetime.utcnow()
    
    def add_execution_step(self, step: ExecutionStep) -> None:
        """Add an execution step to the operation."""
        if self.status not in [OperationStatus.EXECUTING, OperationStatus.PENDING]:
            raise ValueError("Cannot add steps to non-executing operations")
        
        # Validate step order
        expected_step_number = len(self.execution_steps) + 1
        if step.step_number != expected_step_number:
            raise ValueError(f"Expected step {expected_step_number}, got {step.step_number}")
        
        self.execution_steps.append(step)
        
        # Update total fees and slippage
        if step.fee_amount:
            self.total_fees_paid += step.fee_amount
        if step.slippage_percentage:
            self.total_slippage += step.slippage_percentage
    
    def complete_successfully(self, final_amount: Decimal) -> None:
        """Mark the operation as successfully completed."""
        if self.status != OperationStatus.EXECUTING:
            raise ValueError("Can only complete executing operations")
        
        if len(self.execution_steps) == 0:
            raise ValueError("Cannot complete operation without execution steps")
        
        self.status = OperationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.final_amount = final_amount
        
        # Calculate actual profit
        self.actual_profit = final_amount - self.initial_capital
        if self.initial_capital > 0:
            self.actual_profit_percentage = float(
                (self.actual_profit / self.initial_capital) * 100
            )
    
    def fail_operation(self, error_message: str, failed_step_index: Optional[int] = None) -> None:
        """Mark the operation as failed."""
        if self.status not in [OperationStatus.EXECUTING, OperationStatus.PENDING]:
            raise ValueError("Can only fail executing or pending operations")
        
        self.status = OperationStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.failed_step_index = failed_step_index
    
    def cancel_operation(self, reason: str) -> None:
        """Cancel the operation."""
        if self.status not in [OperationStatus.PENDING, OperationStatus.EXECUTING]:
            raise ValueError("Can only cancel pending or executing operations")
        
        self.status = OperationStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.error_message = f"Cancelled: {reason}"
    
    def mark_as_partial(self, completed_steps: int) -> None:
        """Mark operation as partially completed."""
        if self.status != OperationStatus.EXECUTING:
            raise ValueError("Can only mark executing operations as partial")
        
        if completed_steps >= len(self.execution_steps):
            raise ValueError("Completed steps cannot exceed total steps")
        
        self.status = OperationStatus.PARTIAL
        self.completed_at = datetime.utcnow()
    
    def get_execution_duration(self) -> Optional[float]:
        """Get the execution duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def get_success_rate(self) -> float:
        """Get the success rate of execution steps."""
        if not self.execution_steps:
            return 0.0
        
        successful_steps = sum(1 for step in self.execution_steps if step.is_successful())
        return successful_steps / len(self.execution_steps)
    
    def get_total_volume_traded(self) -> Decimal:
        """Get the total volume traded across all steps."""
        return sum(
            step.executed_quantity or Decimal("0")
            for step in self.execution_steps
        )
    
    def is_profitable(self) -> bool:
        """Check if the operation was profitable."""
        return self.actual_profit is not None and self.actual_profit > 0
    
    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """Get efficiency metrics for the operation."""
        duration = self.get_execution_duration()
        
        return {
            "execution_duration_seconds": duration,
            "steps_count": len(self.execution_steps),
            "success_rate": self.get_success_rate(),
            "total_fees_paid": float(self.total_fees_paid),
            "total_slippage": self.total_slippage,
            "profit_per_second": float(self.actual_profit / Decimal(str(duration))) if duration and self.actual_profit else 0,
            "volume_traded": float(self.get_total_volume_traded())
        }
    
    def can_be_retried(self) -> bool:
        """Check if the operation can be retried."""
        return (
            self.status in [OperationStatus.FAILED, OperationStatus.CANCELLED] and
            self.failed_step_index is not None and
            self.failed_step_index == 0  # Only retry if failed at first step
        )
    
    def __str__(self) -> str:
        """String representation of the operation."""
        duration = self.get_execution_duration()
        duration_str = f" ({duration:.2f}s)" if duration else ""
        
        return (f"Operation {self.operation_id}: {self.status.value} "
                f"- Capital: {self.initial_capital}, "
                f"Profit: {self.actual_profit or 'TBD'}{duration_str}")
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on operation ID."""
        if not isinstance(other, ArbitrageOperation):
            return False
        return self.operation_id == other.operation_id
    
    def __hash__(self) -> int:
        """Hash based on operation ID."""
        return hash(self.operation_id)
