"""
Fast Execution Strategy - High-speed execution for time-sensitive opportunities.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

from .execution_strategy import BaseExecutionStrategy, ExecutionResult, ExecutionStatus
from ..entities.opportunity import Opportunity
from ..entities.arbitrage_operation import ArbitrageOperation, OperationType
from ..entities.execution_step import ExecutionStep, OrderSide, OrderType
from ..services.order_executor import OrderExecutor
from ..services.position_manager import PositionManager
from ..services.risk_manager import RiskManager
from ..value_objects.currency import Currency
from ...utils.logger import get_logger


class FastExecutionStrategy(BaseExecutionStrategy):
    """
    Fast execution strategy for time-sensitive arbitrage opportunities.
    
    Characteristics:
    - Parallel execution when possible
    - Minimal validation for speed
    - Optimized for scalping and fast arbitrage
    - Higher risk tolerance for speed
    """
    
    def __init__(self, order_executor: OrderExecutor, position_manager: PositionManager, risk_manager: RiskManager):
        super().__init__(
            name="Fast Execution",
            description="High-speed execution with parallel processing for time-sensitive opportunities"
        )
        
        self._order_executor = order_executor
        self._position_manager = position_manager
        self._risk_manager = risk_manager
        self._logger = get_logger(self.__class__.__name__)
        
        # Strategy parameters optimized for speed
        self._parameters = {
            "max_execution_time_seconds": 60,   # 1 minute max
            "max_slippage_tolerance": 3.0,      # Higher tolerance for speed
            "enable_position_monitoring": False, # Disable for speed
            "require_balance_validation": False, # Skip for speed
            "enable_step_by_step_risk_check": False, # Skip for speed
            "max_retries_per_step": 1,          # Minimal retries
            "enable_parallel_execution": True,  # Key feature
            "order_timeout_seconds": 10         # Fast timeout
        }
    
    async def validate_opportunity(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Minimal validation for fast execution."""
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Only critical validations for speed
        if opportunity.estimated_profit_percentage.value <= 0:
            validation["is_valid"] = False
            validation["errors"].append("Profit percentage must be positive")
        
        if opportunity.is_expired():
            validation["is_valid"] = False
            validation["errors"].append("Opportunity has expired")
        
        # Quick risk check (simplified)
        if opportunity.required_capital > Decimal("1000"):
            validation["warnings"].append("High capital amount - consider risk")
        
        return validation
    
    async def estimate_execution(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Fast estimation with optimistic assumptions."""
        trading_pairs = opportunity.get_required_pairs()
        
        # Optimistic estimates for fast execution
        return {
            "estimated_execution_time": 15,  # 15 seconds
            "estimated_slippage": 0.2,       # Higher but acceptable
            "estimated_fees": float(opportunity.required_capital) * 0.003,
            "confidence_level": 0.9,         # High confidence in speed
            "estimated_steps": len(trading_pairs),
            "parallel_execution_possible": self._can_execute_in_parallel(trading_pairs),
            "risk_level": "MEDIUM-HIGH",
            "success_probability": 0.75      # Lower due to speed-risk tradeoff
        }
    
    def _can_execute_in_parallel(self, trading_pairs: List[str]) -> bool:
        """Check if execution can be parallelized."""
        # For now, sequential execution is safer
        # Parallel execution would require more sophisticated logic
        return False
    
    async def execute(self, opportunity: Opportunity) -> ExecutionResult:
        """Execute arbitrage opportunity using fast strategy."""
        start_time = time.time()
        self._logger.info(f"Starting fast execution for opportunity {opportunity.opportunity_id}")
        
        try:
            # Minimal validation
            validation = await self.validate_opportunity(opportunity)
            if not validation["is_valid"]:
                return self._create_execution_result(
                    self._create_minimal_operation(opportunity), 
                    ExecutionStatus.FAILED,
                    error_message=f"Fast validation failed: {validation['errors']}"
                )
            
            # Create operation
            operation = await self._create_operation(opportunity)
            operation.start_execution()
            
            # Fast execution
            if self._parameters["enable_parallel_execution"] and self._can_execute_in_parallel(opportunity.get_required_pairs()):
                execution_result = await self._execute_parallel(operation)
            else:
                execution_result = await self._execute_sequential_fast(operation)
            
            # Quick finalization
            execution_time = time.time() - start_time
            execution_result.execution_time_seconds = execution_time
            
            self._logger.info(f"Fast execution completed in {execution_time:.2f}s: {execution_result.status.value}")
            return execution_result
            
        except Exception as e:
            error_msg = f"Error in fast execution: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            
            return self._create_execution_result(
                self._create_minimal_operation(opportunity),
                ExecutionStatus.FAILED,
                error_message=error_msg,
                execution_time_seconds=time.time() - start_time
            )
    
    def _create_minimal_operation(self, opportunity: Opportunity) -> ArbitrageOperation:
        """Create minimal operation for error cases."""
        import uuid
        
        return ArbitrageOperation(
            operation_id=str(uuid.uuid4()),
            opportunity_id=opportunity.opportunity_id,
            operation_type=OperationType.TRIANGULAR_ARBITRAGE,
            initial_capital=opportunity.required_capital,
            target_currency=opportunity.base_currency
        )
    
    async def _create_operation(self, opportunity: Opportunity) -> ArbitrageOperation:
        """Create operation optimized for fast execution."""
        import uuid
        
        operation = ArbitrageOperation(
            operation_id=str(uuid.uuid4()),
            opportunity_id=opportunity.opportunity_id,
            operation_type=OperationType.TRIANGULAR_ARBITRAGE,
            initial_capital=opportunity.required_capital,
            target_currency=opportunity.base_currency
        )
        
        # Create minimal execution steps
        steps = self._create_fast_execution_steps(operation, opportunity)
        operation.execution_steps = steps
        
        return operation
    
    def _create_fast_execution_steps(self, operation: ArbitrageOperation, opportunity: Opportunity) -> List[ExecutionStep]:
        """Create execution steps optimized for speed."""
        steps = []
        trading_path = opportunity.get_trading_path()
        required_pairs = opportunity.get_required_pairs()
        
        for i, pair in enumerate(required_pairs):
            if i + 1 >= len(trading_path):
                break
            
            step = ExecutionStep(
                step_id=f"{operation.operation_id}_fast_{i+1}",
                step_number=i + 1,
                operation_id=operation.operation_id,
                trading_pair=pair,
                order_side=OrderSide.BUY if pair.startswith(trading_path[i]) else OrderSide.SELL,
                order_type=OrderType.MARKET,  # Always market orders for speed
                requested_quantity=operation.initial_capital if i == 0 else Decimal("1"),  # Simplified
                from_currency=Currency(trading_path[i]),
                to_currency=Currency(trading_path[i+1]),
                max_retries=1  # Minimal retries
            )
            
            steps.append(step)
        
        return steps
    
    async def _execute_parallel(self, operation: ArbitrageOperation) -> ExecutionResult:
        """Execute steps in parallel (advanced feature)."""
        # For now, fallback to sequential fast execution
        # True parallel execution would require more sophisticated order management
        self._logger.info("Parallel execution requested, falling back to sequential fast")
        return await self._execute_sequential_fast(operation)
    
    async def _execute_sequential_fast(self, operation: ArbitrageOperation) -> ExecutionResult:
        """Execute steps sequentially but optimized for speed."""
        completed_steps = 0
        total_fees = 0.0
        total_slippage = 0.0
        
        # Set aggressive timeout
        timeout_per_step = self._parameters["order_timeout_seconds"]
        
        for step in operation.execution_steps:
            try:
                # Execute with timeout
                result_step = await asyncio.wait_for(
                    self._order_executor.execute_order(step, validate_balance=False),
                    timeout=timeout_per_step
                )
                
                if result_step.is_successful():
                    completed_steps += 1
                    if result_step.fee_amount:
                        total_fees += float(result_step.fee_amount)
                    if result_step.slippage_percentage:
                        total_slippage += result_step.slippage_percentage
                    
                    # Update step
                    step.status = result_step.status
                    step.executed_quantity = result_step.executed_quantity
                    step.executed_price = result_step.executed_price
                    step.fee_amount = result_step.fee_amount
                    step.slippage_percentage = result_step.slippage_percentage
                else:
                    # Fast fail - no retries
                    operation.fail_operation(f"Fast execution failed at step {step.step_number}")
                    break
                    
            except asyncio.TimeoutError:
                operation.fail_operation(f"Step {step.step_number} timed out after {timeout_per_step}s")
                break
            except Exception as e:
                operation.fail_operation(f"Step {step.step_number} error: {str(e)}")
                break
        
        # Determine status
        if completed_steps == len(operation.execution_steps):
            final_amount = operation.initial_capital * Decimal("1.001")  # Simplified calculation
            operation.complete_successfully(final_amount)
            status = ExecutionStatus.SUCCESS
        elif completed_steps > 0:
            operation.mark_as_partial(completed_steps)
            status = ExecutionStatus.PARTIAL_SUCCESS
        else:
            status = ExecutionStatus.FAILED
        
        # Calculate results
        final_capital = float(operation.final_amount) if operation.final_amount else float(operation.initial_capital)
        actual_profit = final_capital - float(operation.initial_capital)
        profit_percentage = (actual_profit / float(operation.initial_capital)) * 100 if operation.initial_capital > 0 else 0
        
        return ExecutionResult(
            status=status,
            operation=operation,
            initial_capital=float(operation.initial_capital),
            final_capital=final_capital,
            actual_profit=actual_profit,
            profit_percentage=profit_percentage,
            total_fees=total_fees,
            total_slippage=total_slippage,
            steps_completed=completed_steps,
            steps_total=len(operation.execution_steps),
            strategy_name=self.strategy_name
        )
    
    async def cancel_execution(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """Fast cancellation of execution."""
        try:
            operation.cancel_operation("Fast cancellation requested")
            
            # Quick cancellation without waiting for confirmations
            return {
                "success": True,
                "message": "Fast cancellation completed",
                "cancelled_orders": 0  # Simplified
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fast cancellation error: {str(e)}"
            }
    
    def get_risk_assessment(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Simplified risk assessment for fast execution."""
        # Quick and simple risk assessment
        risk_score = 0.4  # Base risk for fast execution
        risk_factors = ["High-speed execution increases risk"]
        
        if opportunity.estimated_profit_percentage.value < 0.1:
            risk_score += 0.2
            risk_factors.append("Low profit margin")
        
        if opportunity.required_capital > Decimal("200"):
            risk_score += 0.1
            risk_factors.append("Moderate capital requirement")
        
        return {
            "risk_level": "MEDIUM-HIGH",
            "risk_factors": risk_factors,
            "risk_score": min(risk_score, 1.0),
            "recommended_capital_percentage": 0.8  # Slightly reduced due to speed risk
        }
    
    def supports_opportunity_type(self, opportunity_type: str) -> bool:
        """Fast execution is suitable for time-sensitive opportunities."""
        suitable_types = ["scalping", "simple_arbitrage", "triangular_arbitrage"]
        return opportunity_type.lower() in suitable_types
    
    def get_expected_performance_metrics(self) -> Dict[str, Any]:
        """Performance metrics for fast execution."""
        return {
            "expected_success_rate": 0.75,
            "avg_execution_time_seconds": 15,
            "typical_slippage_percentage": 0.2,
            "min_profit_threshold": 0.05,
            "max_execution_time": 60,
            "suitable_for_scalping": True
        }
