"""
Execution Strategy Interface - Open/Closed Principle implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..entities.arbitrage_operation import ArbitrageOperation
from ..entities.opportunity import Opportunity


class ExecutionStatus(Enum):
    """Status of execution result."""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


@dataclass
class ExecutionResult:
    """
    Result of an execution strategy.
    
    Encapsulates all information about the execution outcome.
    """
    
    # Core result data
    status: ExecutionStatus
    operation: ArbitrageOperation
    
    # Financial results
    initial_capital: float
    final_capital: Optional[float] = None
    actual_profit: Optional[float] = None
    profit_percentage: Optional[float] = None
    
    # Execution metrics
    execution_time_seconds: Optional[float] = None
    total_fees: float = 0.0
    total_slippage: float = 0.0
    steps_completed: int = 0
    steps_total: int = 0
    
    # Error information
    error_message: Optional[str] = None
    failed_step: Optional[int] = None
    
    # Metadata
    strategy_name: str = ""
    execution_timestamp: datetime = None
    
    def __post_init__(self):
        if self.execution_timestamp is None:
            self.execution_timestamp = datetime.utcnow()
    
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status in [ExecutionStatus.SUCCESS, ExecutionStatus.PARTIAL_SUCCESS]
    
    def is_profitable(self) -> bool:
        """Check if execution was profitable."""
        return self.actual_profit is not None and self.actual_profit > 0
    
    def get_completion_rate(self) -> float:
        """Get the completion rate of execution steps."""
        if self.steps_total == 0:
            return 0.0
        return self.steps_completed / self.steps_total
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "operation_id": self.operation.operation_id,
            "strategy_name": self.strategy_name,
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "actual_profit": self.actual_profit,
            "profit_percentage": self.profit_percentage,
            "execution_time_seconds": self.execution_time_seconds,
            "total_fees": self.total_fees,
            "total_slippage": self.total_slippage,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "completion_rate": self.get_completion_rate(),
            "error_message": self.error_message,
            "failed_step": self.failed_step,
            "execution_timestamp": self.execution_timestamp.isoformat(),
            "is_successful": self.is_successful(),
            "is_profitable": self.is_profitable()
        }


class IExecutionStrategy(ABC):
    """
    Interface for execution strategies.
    
    Applies Open/Closed Principle - new execution strategies can be added
    without modifying existing code. Each strategy encapsulates a different
    approach to executing arbitrage operations.
    """
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of the execution strategy."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the execution strategy."""
        pass
    
    @abstractmethod
    async def validate_opportunity(self, opportunity: Opportunity) -> Dict[str, Any]:
        """
        Validate if the opportunity is suitable for this execution strategy.
        
        Args:
            opportunity: The opportunity to validate
            
        Returns:
            Validation result with is_valid boolean and details
        """
        pass
    
    @abstractmethod
    async def estimate_execution(self, opportunity: Opportunity) -> Dict[str, Any]:
        """
        Estimate execution parameters for the opportunity.
        
        Args:
            opportunity: The opportunity to estimate
            
        Returns:
            Estimation result with expected metrics
        """
        pass
    
    @abstractmethod
    async def execute(self, opportunity: Opportunity) -> ExecutionResult:
        """
        Execute the arbitrage opportunity using this strategy.
        
        Args:
            opportunity: The opportunity to execute
            
        Returns:
            Execution result with all relevant information
        """
        pass
    
    @abstractmethod
    async def cancel_execution(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """
        Cancel an ongoing execution.
        
        Args:
            operation: The operation to cancel
            
        Returns:
            Cancellation result
        """
        pass
    
    @abstractmethod
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """
        Get the parameters and configuration of this strategy.
        
        Returns:
            Strategy parameters
        """
        pass
    
    @abstractmethod
    def update_strategy_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update strategy parameters.
        
        Args:
            parameters: New parameters to set
            
        Returns:
            Updated parameters
        """
        pass
    
    @abstractmethod
    def get_risk_assessment(self, opportunity: Opportunity) -> Dict[str, Any]:
        """
        Get risk assessment specific to this execution strategy.
        
        Args:
            opportunity: The opportunity to assess
            
        Returns:
            Risk assessment result
        """
        pass
    
    def supports_opportunity_type(self, opportunity_type: str) -> bool:
        """
        Check if this strategy supports a specific opportunity type.
        
        Args:
            opportunity_type: Type of opportunity (e.g., 'triangular', 'simple')
            
        Returns:
            True if supported, False otherwise
        """
        # Default implementation - can be overridden
        return True
    
    def get_expected_performance_metrics(self) -> Dict[str, Any]:
        """
        Get expected performance metrics for this strategy.
        
        Returns:
            Performance metrics (success rate, avg profit, etc.)
        """
        # Default implementation - can be overridden
        return {
            "expected_success_rate": 0.8,
            "avg_execution_time_seconds": 30,
            "typical_slippage_percentage": 0.1,
            "min_profit_threshold": 0.1
        }


class BaseExecutionStrategy(IExecutionStrategy):
    """
    Base implementation of execution strategy with common functionality.
    
    Provides default implementations and utility methods that can be
    shared across different concrete strategies.
    """
    
    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description
        self._parameters = {}
        
    @property
    def strategy_name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        return self._parameters.copy()
    
    def update_strategy_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update strategy parameters with validation."""
        # Basic validation - can be overridden in concrete strategies
        for key, value in parameters.items():
            if key in self._parameters:
                self._parameters[key] = value
        
        return self.get_strategy_parameters()
    
    async def validate_opportunity(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Basic validation that can be extended by concrete strategies."""
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Basic checks
        if opportunity.estimated_profit_percentage.value <= 0:
            validation["is_valid"] = False
            validation["errors"].append("Profit percentage must be positive")
        
        if opportunity.required_capital <= 0:
            validation["is_valid"] = False
            validation["errors"].append("Required capital must be positive")
        
        if opportunity.is_expired():
            validation["is_valid"] = False
            validation["errors"].append("Opportunity has expired")
        
        return validation
    
    async def estimate_execution(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Basic estimation that can be extended by concrete strategies."""
        return {
            "estimated_execution_time": 30,  # seconds
            "estimated_slippage": 0.1,  # percentage
            "estimated_fees": float(opportunity.required_capital) * 0.003,  # 0.3%
            "confidence_level": 0.8
        }
    
    def get_risk_assessment(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Basic risk assessment that can be extended by concrete strategies."""
        return {
            "risk_level": "MEDIUM",
            "risk_factors": [],
            "risk_score": 0.5,
            "recommended_capital_percentage": 1.0  # 100% of suggested capital
        }
    
    def _create_execution_result(
        self, 
        operation: ArbitrageOperation, 
        status: ExecutionStatus,
        **kwargs
    ) -> ExecutionResult:
        """Helper method to create execution results."""
        return ExecutionResult(
            status=status,
            operation=operation,
            strategy_name=self.strategy_name,
            initial_capital=float(operation.initial_capital),
            **kwargs
        )
