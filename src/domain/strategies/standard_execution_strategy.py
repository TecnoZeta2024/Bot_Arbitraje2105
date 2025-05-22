"""
Standard Execution Strategy - Conservative execution approach.
"""

import time
from typing import Dict, Any, Optional
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


class StandardExecutionStrategy(BaseExecutionStrategy):
    """
    Standard execution strategy for conservative arbitrage execution.
    
    Characteristics:
    - Conservative approach with thorough validation
    - Step-by-step execution with monitoring
    - Risk management at each step
    - Suitable for triangular and simple arbitrage
    """
    
    def __init__(self, order_executor: OrderExecutor, position_manager: PositionManager, risk_manager: RiskManager):
        super().__init__(
            name="Standard Execution",
            description="Conservative step-by-step execution with thorough risk management"
        )
        
        self._order_executor = order_executor
        self._position_manager = position_manager
        self._risk_manager = risk_manager
        self._logger = get_logger(self.__class__.__name__)
        
        # Strategy parameters
        self._parameters = {
            "max_execution_time_seconds": 300,  # 5 minutes
            "max_slippage_tolerance": 2.0,      # 2%
            "enable_position_monitoring": True,
            "require_balance_validation": True,
            "enable_step_by_step_risk_check": True,
            "max_retries_per_step": 2
        }
    
    async def validate_opportunity(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Validate opportunity for standard execution."""
        validation = await super().validate_opportunity(opportunity)
        
        # Additional validations for standard execution
        if validation["is_valid"]:
            # Risk assessment
            risk_assessment = self._risk_manager.assess_opportunity_risk(opportunity)
            if not risk_assessment["is_approved"]:
                validation["is_valid"] = False
                validation["errors"].extend(risk_assessment.get("risk_factors", []))
            
            # Check if opportunity is executable
            if not opportunity.is_executable():
                validation["is_valid"] = False
                validation["errors"].append("Opportunity is not in executable state")
        
        return validation
    
    async def estimate_execution(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Estimate execution parameters for standard strategy."""
        base_estimate = await super().estimate_execution(opportunity)
        
        # Enhanced estimation for standard execution
        trading_pairs = opportunity.get_required_pairs()
        
        estimated_steps = len(trading_pairs)
        estimated_time_per_step = 30  # seconds
        
        enhanced_estimate = {
            **base_estimate,
            "estimated_steps": estimated_steps,
            "estimated_time_per_step": estimated_time_per_step,
            "total_estimated_time": estimated_steps * estimated_time_per_step,
            "risk_level": "MEDIUM",
            "recommended_capital_factor": 1.0,  # Use full suggested capital
            "success_probability": 0.85
        }
        
        return enhanced_estimate
    
    async def execute(self, opportunity: Opportunity) -> ExecutionResult:
        """Execute arbitrage opportunity using standard strategy."""
        start_time = time.time()
        self._logger.info(f"Starting standard execution for opportunity {opportunity.opportunity_id}")
        
        try:
            # Create operation
            operation = await self._create_operation(opportunity)
            
            # Pre-execution validation
            validation = await self.validate_opportunity(opportunity)
            if not validation["is_valid"]:
                return self._create_execution_result(
                    operation, ExecutionStatus.FAILED,
                    error_message=f"Validation failed: {validation['errors']}"
                )
            
            # Start execution
            operation.start_execution()
            
            # Execute step by step
            execution_result = await self._execute_steps(operation)
            
            # Finalize result
            execution_time = time.time() - start_time
            execution_result.execution_time_seconds = execution_time
            
            self._logger.info(f"Standard execution completed: {execution_result.status.value}")
            return execution_result
            
        except Exception as e:
            error_msg = f"Unexpected error in standard execution: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            
            operation = ArbitrageOperation(
                operation_id=f"failed_{opportunity.opportunity_id}",
                opportunity_id=opportunity.opportunity_id,
                operation_type=OperationType.TRIANGULAR_ARBITRAGE,
                initial_capital=opportunity.required_capital,
                target_currency=opportunity.base_currency
            )
            
            return self._create_execution_result(
                operation, ExecutionStatus.FAILED,
                error_message=error_msg,
                execution_time_seconds=time.time() - start_time
            )
    
    async def _create_operation(self, opportunity: Opportunity) -> ArbitrageOperation:
        """Create arbitrage operation from opportunity."""
        import uuid
        
        operation_id = str(uuid.uuid4())
        
        # Determine operation type
        trading_pairs = opportunity.get_required_pairs()
        if len(trading_pairs) == 3:
            op_type = OperationType.TRIANGULAR_ARBITRAGE
        else:
            op_type = OperationType.TRIANGULAR_ARBITRAGE  # Default
        
        operation = ArbitrageOperation(
            operation_id=operation_id,
            opportunity_id=opportunity.opportunity_id,
            operation_type=op_type,
            initial_capital=opportunity.required_capital,
            target_currency=opportunity.base_currency
        )
        
        # Create execution steps
        steps = await self._create_execution_steps(operation, opportunity)
        operation.execution_steps = steps
        
        return operation
    
    async def _create_execution_steps(self, operation: ArbitrageOperation, opportunity: Opportunity) -> list:
        """Create execution steps for the operation."""
        steps = []
        trading_path = opportunity.get_trading_path()
        required_pairs = opportunity.get_required_pairs()
        
        current_amount = operation.initial_capital
        
        for i, pair in enumerate(required_pairs):
            if i + 1 >= len(trading_path):
                break
            
            step_id = f"{operation.operation_id}_step_{i+1}"
            from_currency = Currency(trading_path[i])
            to_currency = Currency(trading_path[i+1])
            
            # Determine order side
            if pair == f"{trading_path[i]}{trading_path[i+1]}":
                order_side = OrderSide.BUY
            else:
                order_side = OrderSide.SELL
            
            step = ExecutionStep(
                step_id=step_id,
                step_number=i + 1,
                operation_id=operation.operation_id,
                trading_pair=pair,
                order_side=order_side,
                order_type=OrderType.MARKET,
                requested_quantity=current_amount,
                from_currency=from_currency,
                to_currency=to_currency
            )
            
            steps.append(step)
        
        return steps
    
    async def _execute_steps(self, operation: ArbitrageOperation) -> ExecutionResult:
        """Execute all steps of the operation."""
        completed_steps = 0
        total_fees = 0.0
        total_slippage = 0.0
        
        for step in operation.execution_steps:
            # Pre-step risk check
            if self._parameters["enable_step_by_step_risk_check"]:
                risk_check = self._risk_manager.monitor_execution_risks(operation)
                if risk_check["should_abort"]:
                    operation.fail_operation(f"Risk check failed: {risk_check['alerts']}")
                    break
            
            # Execute step with retries
            success = await self._execute_step_with_retries(step)
            
            if success:
                completed_steps += 1
                if step.fee_amount:
                    total_fees += float(step.fee_amount)
                if step.slippage_percentage:
                    total_slippage += step.slippage_percentage
            else:
                # Step failed, abort operation
                operation.fail_operation(f"Step {step.step_number} failed: {step.error_message}")
                break
        
        # Determine final status
        if completed_steps == len(operation.execution_steps):
            # All steps completed
            final_amount = self._calculate_final_amount(operation)
            operation.complete_successfully(final_amount)
            status = ExecutionStatus.SUCCESS
        elif completed_steps > 0:
            # Partial completion
            operation.mark_as_partial(completed_steps)
            status = ExecutionStatus.PARTIAL_SUCCESS
        else:
            # Complete failure
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
    
    async def _execute_step_with_retries(self, step: ExecutionStep) -> bool:
        """Execute a step with retry logic."""
        max_retries = self._parameters["max_retries_per_step"]
        
        for attempt in range(max_retries + 1):
            try:
                # Execute the step
                result_step = await self._order_executor.execute_order(
                    step, 
                    validate_balance=self._parameters["require_balance_validation"]
                )
                
                if result_step.is_successful():
                    # Update the step with results
                    step.status = result_step.status
                    step.executed_quantity = result_step.executed_quantity
                    step.executed_price = result_step.executed_price
                    step.fee_amount = result_step.fee_amount
                    step.slippage_percentage = result_step.slippage_percentage
                    step.completed_at = result_step.completed_at
                    
                    return True
                else:
                    # Step failed
                    if attempt < max_retries:
                        self._logger.warning(f"Step {step.step_id} failed on attempt {attempt + 1}, retrying...")
                        step.retry_step()
                        await self._wait_before_retry(attempt)
                    else:
                        step.error_message = result_step.error_message
                        return False
                        
            except Exception as e:
                error_msg = f"Error executing step {step.step_id}: {str(e)}"
                self._logger.error(error_msg)
                
                if attempt < max_retries:
                    self._logger.warning(f"Retrying step {step.step_id} after error...")
                    await self._wait_before_retry(attempt)
                else:
                    step.fail_step(error_msg)
                    return False
        
        return False
    
    async def _wait_before_retry(self, attempt: int) -> None:
        """Wait before retrying with exponential backoff."""
        import asyncio
        wait_time = min(2 ** attempt, 10)  # Max 10 seconds
        await asyncio.sleep(wait_time)
    
    def _calculate_final_amount(self, operation: ArbitrageOperation) -> Decimal:
        """Calculate final amount after all steps."""
        # Simplified calculation - in reality would track through each step
        if operation.execution_steps:
            last_step = operation.execution_steps[-1]
            if last_step.executed_quantity:
                return last_step.executed_quantity
        
        return operation.initial_capital
    
    async def cancel_execution(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """Cancel ongoing execution."""
        try:
            operation.cancel_operation("User requested cancellation")
            
            # Cancel any pending orders
            cancelled_orders = 0
            for step in operation.execution_steps:
                if step.exchange_order_id and step.status.value == "EXECUTING":
                    success = await self._order_executor.cancel_order(
                        step.trading_pair, 
                        step.exchange_order_id
                    )
                    if success:
                        cancelled_orders += 1
            
            return {
                "success": True,
                "message": f"Operation cancelled, {cancelled_orders} orders cancelled",
                "cancelled_orders": cancelled_orders
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cancelling operation: {str(e)}"
            }
    
    def get_risk_assessment(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Get risk assessment for standard execution."""
        base_assessment = super().get_risk_assessment(opportunity)
        
        # Enhanced risk assessment for standard execution
        risk_factors = []
        risk_score = 0.3  # Base risk for standard execution
        
        # Check profit margin
        if opportunity.estimated_profit_percentage.value < 0.5:
            risk_factors.append("Low profit margin")
            risk_score += 0.2
        
        # Check capital amount
        if opportunity.required_capital > Decimal("500"):
            risk_factors.append("High capital requirement")
            risk_score += 0.1
        
        # Check number of steps
        required_pairs = opportunity.get_required_pairs()
        if len(required_pairs) > 3:
            risk_factors.append("Complex execution path")
            risk_score += 0.2
        
        return {
            "risk_level": "MEDIUM" if risk_score < 0.6 else "HIGH",
            "risk_factors": risk_factors,
            "risk_score": min(risk_score, 1.0),
            "recommended_capital_percentage": max(0.5, 1.0 - risk_score)
        }


# Import required modules at the end to avoid circular imports
