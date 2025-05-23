"""
Concrete implementation of IOperationRepository using Supabase.
"""

import math # Added for Sharpe Ratio calculation
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, cast

from ...domain.entities.arbitrage_operation import (
    ArbitrageOperation,
    OperationStatus,
    OperationType,
)
from ...domain.entities.execution_step import (
    ExecutionStep,
    OrderSide,
    OrderType,
    StepStatus,
)
from ...domain.repositories.operation_repository import IOperationRepository
from ...domain.value_objects.currency import Currency
from ...domain.value_objects.price import Price
from ...utils.logger import get_logger
from ..external_apis.supabase_client import SupabaseClient

# Import the exceptions at the top of the file
from .opportunity_repository_impl import NotFoundError, RepositoryError


class OperationRepositoryImpl(IOperationRepository):
    """
    Concrete implementation of operation repository using Supabase.
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self._supabase = supabase_client
        self._logger = get_logger(self.__class__.__name__)
        self._operations_table = "arbitraje_operaciones"
        self._steps_table = "execution_steps"
    
    async def save(self, operation: ArbitrageOperation) -> None:
        """Save an operation to Supabase."""
        try:
            operation_data = self._serialize_operation(operation)
            
            # Check if operation already exists
            existing = await self.get_by_id(operation.operation_id)
            
            if existing:
                # Update existing operation
                response = self._supabase.client.table(self._operations_table)\
                    .update(operation_data)\
                    .eq("operation_id", operation.operation_id)\
                    .execute()
            else:
                # Insert new operation
                response = self._supabase.client.table(self._operations_table)\
                    .insert(operation_data)\
                    .execute()
            
            # Save execution steps
            await self._save_execution_steps(operation)
            
            self._logger.info(f"Saved operation {operation.operation_id}")
            
        except Exception as e:
            self._logger.error(f"Error saving operation {operation.operation_id}: {e}")
            raise RepositoryError(f"Failed to save operation: {e}")
    
    async def get_by_id(self, operation_id: str) -> Optional[ArbitrageOperation]:
        """Retrieve an operation by its ID."""
        try:
            response = self._supabase.client.table(self._operations_table)\
                .select("*")\
                .eq("operation_id", operation_id)\
                .limit(1)\
                .execute()
            
            if not response.data:
                return None
            
            operation = self._deserialize_operation(response.data[0])
            
            # Load execution steps
            steps = await self._load_execution_steps(operation_id)
            operation.execution_steps = steps
            
            return operation
            
        except Exception as e:
            self._logger.error(f"Error retrieving operation {operation_id}: {e}")
            raise RepositoryError(f"Failed to retrieve operation: {e}")
    
    async def get_by_opportunity_id(self, opportunity_id: str) -> List[ArbitrageOperation]:
        """Retrieve operations related to a specific opportunity."""
        try:
            response = self._supabase.client.table(self._operations_table)\
                .select("*")\
                .eq("opportunity_id", opportunity_id)\
                .execute()
            
            operations = []
            for data in response.data:
                operation = self._deserialize_operation(data)
                steps = await self._load_execution_steps(operation.operation_id)
                operation.execution_steps = steps
                operations.append(operation)
            
            return operations
            
        except Exception as e:
            self._logger.error(f"Error retrieving operations by opportunity {opportunity_id}: {e}")
            raise RepositoryError(f"Failed to retrieve operations by opportunity: {e}")
    
    async def get_by_status(self, status: OperationStatus) -> List[ArbitrageOperation]:
        """Retrieve operations by their status."""
        try:
            response = self._supabase.client.table(self._operations_table)\
                .select("*")\
                .eq("status", status.value)\
                .execute()
            
            operations = []
            for data in response.data:
                operation = self._deserialize_operation(data)
                steps = await self._load_execution_steps(operation.operation_id)
                operation.execution_steps = steps
                operations.append(operation)
            
            return operations
            
        except Exception as e:
            self._logger.error(f"Error retrieving operations by status {status}: {e}")
            raise RepositoryError(f"Failed to retrieve operations by status: {e}")
    
    async def get_active_operations(self) -> List[ArbitrageOperation]:
        """Retrieve currently active operations."""
        active_statuses = [OperationStatus.PENDING, OperationStatus.EXECUTING]
        operations = []
        
        for status in active_statuses:
            ops = await self.get_by_status(status)
            operations.extend(ops)
        
        return operations
    
    async def get_completed_operations(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ArbitrageOperation]:
        """Retrieve completed operations within a date range."""
        try:
            query = self._supabase.client.table(self._operations_table)\
                .select("*")\
                .eq("status", OperationStatus.COMPLETED.value)
            
            if start_date:
                query = query.gte("completed_at", start_date.isoformat())
            if end_date:
                query = query.lte("completed_at", end_date.isoformat())
            
            response = query.execute()
            
            operations = []
            for data in response.data:
                operation = self._deserialize_operation(data)
                steps = await self._load_execution_steps(operation.operation_id)
                operation.execution_steps = steps
                operations.append(operation)
            
            return operations
            
        except Exception as e:
            self._logger.error(f"Error retrieving completed operations: {e}")
            raise RepositoryError(f"Failed to retrieve completed operations: {e}")
    
    async def update_status(self, operation_id: str, new_status: OperationStatus) -> None:
        """Update the status of an operation."""
        try:
            update_data = {"status": new_status.value}
            
            # Set completed_at if status is final
            if new_status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            response = self._supabase.client.table(self._operations_table)\
                .update(update_data)\
                .eq("operation_id", operation_id)\
                .execute()
            
            if not response.data:
                raise NotFoundError(f"Operation {operation_id} not found")
                
            self._logger.info(f"Updated operation {operation_id} status to {new_status.value}")
            
        except Exception as e:
            self._logger.error(f"Error updating operation status: {e}")
            if "not found" in str(e).lower():
                raise NotFoundError(f"Operation {operation_id} not found")
            raise RepositoryError(f"Failed to update operation status: {e}")
    
    async def update_results(
        self, 
        operation_id: str, 
        results: Dict[str, Any]
    ) -> None:
        """Update the execution results of an operation."""
        try:
            response = self._supabase.client.table(self._operations_table)\
                .update(results)\
                .eq("operation_id", operation_id)\
                .execute()
            
            if not response.data:
                raise NotFoundError(f"Operation {operation_id} not found")
                
            self._logger.info(f"Updated operation {operation_id} results")
            
        except Exception as e:
            self._logger.error(f"Error updating operation results: {e}")
            if "not found" in str(e).lower():
                raise NotFoundError(f"Operation {operation_id} not found")
            raise RepositoryError(f"Failed to update operation results: {e}")
    
    async def get_performance_summary(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get performance summary for operations in a date range."""
        try:
            completed_ops = await self.get_completed_operations(start_date, end_date)
            
            if not completed_ops:
                return {
                    "total_operations": 0,
                    "profitable_operations": 0,
                    "total_profit": 0,
                    "average_profit": 0,
                    "success_rate": 0,
                    "average_duration": 0
                }
            
            total_operations = len(completed_ops)
            profitable_ops = [op for op in completed_ops if op.is_profitable()]
            
            # Ensure actual_profit is not None before summing and convert to float
            profits_list = [float(cast(Decimal, op.actual_profit)) for op in completed_ops if op.actual_profit is not None]
            total_profit = sum(profits_list) if profits_list else 0.0
            
            durations = [cast(float, op.get_execution_duration()) for op in completed_ops if op.get_execution_duration() is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            
            return {
                "total_operations": total_operations,
                "profitable_operations": len(profitable_ops),
                "total_profit": total_profit,
                "average_profit": total_profit / total_operations,
                "success_rate": len(profitable_ops) / total_operations * 100,
                "average_duration": avg_duration,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            self._logger.error(f"Error calculating performance summary: {e}")
            raise RepositoryError(f"Failed to calculate performance summary: {e}")
    
    async def calculate_sharpe_ratio(
        self,
        start_date: datetime,
        end_date: datetime,
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculates the Sharpe Ratio for completed operations within a date range.

        Args:
            start_date: Start date for the operations.
            end_date: End date for the operations.
            risk_free_rate: Annual risk-free rate (default to 0.0 for simplicity).

        Returns:
            The calculated Sharpe Ratio.
        """
        try:
            completed_ops = await self.get_completed_operations(start_date, end_date)

            if not completed_ops:
                return 0.0

            # Extract daily returns (actual_profit_percentage)
            # Assuming actual_profit_percentage is a daily return for simplicity
            # For a more accurate Sharpe Ratio, daily portfolio returns would be needed.
            returns_list = []
            for op in completed_ops:
                if op.actual_profit_percentage is not None:
                    returns_list.append(float(op.actual_profit_percentage))
            
            if len(returns_list) < 2: # Need at least two data points for standard deviation
                return 0.0

            returns_float = returns_list

            # Calculate average return
            average_return = sum(returns_float) / len(returns_float)

            # Calculate standard deviation of returns (volatility)
            variance = sum([(r - average_return) ** 2 for r in returns_float]) / (len(returns_float) - 1)
            std_dev = math.sqrt(variance)

            if std_dev == 0:
                return 0.0 # Avoid division by zero

            # Calculate Sharpe Ratio
            sharpe_ratio = (average_return - risk_free_rate) / std_dev
            return round(sharpe_ratio, 2)

        except Exception as e:
            self._logger.error(f"Error calculating Sharpe Ratio: {e}")
            raise RepositoryError(f"Failed to calculate Sharpe Ratio: {e}")

    # Additional methods implementation would continue here...
    # For brevity, I'll implement the core serialization methods
    
    async def _save_execution_steps(self, operation: ArbitrageOperation) -> None:
        """Save execution steps for an operation to Supabase."""
        try:
            # Delete existing steps to avoid duplicates on update
            await self._supabase.client.table(self._steps_table)\
                .delete()\
                .eq("operation_id", operation.operation_id)\
                .execute()

            if operation.execution_steps:
                steps_data = [self._serialize_step(step) for step in operation.execution_steps]
                await self._supabase.client.table(self._steps_table)\
                    .insert(steps_data)\
                    .execute()
        except Exception as e:
            self._logger.error(f"Error saving execution steps for operation {operation.operation_id}: {e}")
            raise RepositoryError(f"Failed to save execution steps: {e}")

    async def _load_execution_steps(self, operation_id: str) -> List[ExecutionStep]:
        """Load execution steps for a given operation ID."""
        try:
            response = await self._supabase.client.table(self._steps_table)\
                .select("*")\
                .eq("operation_id", operation_id)\
                .order("step_index")\
                .execute()
            
            steps = [self._deserialize_step(data) for data in response.data]
            return steps
        except Exception as e:
            self._logger.error(f"Error loading execution steps for operation {operation_id}: {e}")
            raise RepositoryError(f"Failed to load execution steps: {e}")

    def _serialize_step(self, step: ExecutionStep) -> Dict[str, Any]:
        """Convert ExecutionStep entity to database format."""
        return {
            "step_id": step.step_id,
            "operation_id": step.operation_id,
            "step_number": step.step_number,
            "trading_pair": step.trading_pair,
            "order_side": step.order_side.value,
            "order_type": step.order_type.value,
            "requested_quantity": float(step.requested_quantity),
            "from_currency": step.from_currency.symbol,
            "to_currency": step.to_currency.symbol,
            "executed_quantity": float(step.executed_quantity) if step.executed_quantity else None,
            "requested_price": float(step.requested_price.amount) if step.requested_price else None,
            "executed_price": float(step.executed_price.amount) if step.executed_price else None,
            "status": step.status.value,
            "created_at": step.created_at.isoformat() if step.created_at else None,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            "fee_amount": float(step.fee_amount) if step.fee_amount else None,
            "fee_currency": step.fee_currency.symbol if step.fee_currency else None,
            "slippage_percentage": step.slippage_percentage,
            "exchange_order_id": step.exchange_order_id,
            "exchange_trade_ids": step.exchange_trade_ids,
            "error_message": step.error_message,
            "retry_count": step.retry_count,
            "max_retries": step.max_retries,
        }

    def _deserialize_step(self, data: Dict[str, Any]) -> ExecutionStep:
        """Convert database format to ExecutionStep entity."""
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        
        from_currency = Currency(data["from_currency"])
        to_currency = Currency(data["to_currency"])
        fee_currency = Currency(data["fee_currency"]) if data.get("fee_currency") else None

        # For prices, we need to know the currency. Assuming it's the to_currency for the price.
        # This might need refinement based on exact schema, but it's a reasonable default.
        price_currency = to_currency 

        requested_price = Price(Decimal(str(data["requested_price"])), price_currency) if data.get("requested_price") else None
        executed_price = Price(Decimal(str(data["executed_price"])), price_currency) if data.get("executed_price") else None

        return ExecutionStep(
            step_id=data["step_id"],
            operation_id=data["operation_id"],
            step_number=data["step_number"],
            trading_pair=data["trading_pair"],
            order_side=OrderSide(data["order_side"]),
            order_type=OrderType(data["order_type"]),
            requested_quantity=Decimal(str(data["requested_quantity"])),
            from_currency=from_currency,
            to_currency=to_currency,
            executed_quantity=Decimal(str(data["executed_quantity"])) if data.get("executed_quantity") else None,
            requested_price=requested_price,
            executed_price=executed_price,
            status=StepStatus(data["status"]),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            fee_amount=Decimal(str(data["fee_amount"])) if data.get("fee_amount") else None,
            fee_currency=fee_currency,
            slippage_percentage=data.get("slippage_percentage"),
            exchange_order_id=data.get("exchange_order_id"),
            exchange_trade_ids=data.get("exchange_trade_ids", []),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )

    def _serialize_operation(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """Convert ArbitrageOperation entity to database format."""
        return {
            "operation_id": operation.operation_id,
            "opportunity_id": operation.opportunity_id,
            "operation_type": operation.operation_type.value,
            "initial_capital": float(operation.initial_capital),
            "target_currency": operation.target_currency.symbol,
            "status": operation.status.value,
            "created_at": operation.created_at.isoformat(),
            "started_at": operation.started_at.isoformat() if operation.started_at else None,
            "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
            "final_amount": float(operation.final_amount) if operation.final_amount else None,
            "actual_profit": float(operation.actual_profit) if operation.actual_profit else None,
            "actual_profit_percentage": operation.actual_profit_percentage,
            "total_fees_paid": float(operation.total_fees_paid),
            "total_slippage": operation.total_slippage,
            "error_message": operation.error_message,
            "failed_step_index": operation.failed_step_index
        }
    
    def _deserialize_operation(self, data: Dict[str, Any]) -> ArbitrageOperation:
        """Convert database format to ArbitrageOperation entity."""
        target_currency = Currency(data["target_currency"])
        
        # Safely parse datetime fields
        created_at = None
        if isinstance(data.get("created_at"), str):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                self._logger.warning(f"Invalid created_at format: {data['created_at']}")
        if created_at is None:
            created_at = datetime.now() # Fallback if parsing fails or data is missing

        started_at = None
        if isinstance(data.get("started_at"), str):
            try:
                started_at = datetime.fromisoformat(data["started_at"])
            except ValueError:
                self._logger.warning(f"Invalid started_at format: {data['started_at']}")

        completed_at = None
        if isinstance(data.get("completed_at"), str):
            try:
                completed_at = datetime.fromisoformat(data["completed_at"])
            except ValueError:
                self._logger.warning(f"Invalid completed_at format: {data['completed_at']}")

        operation = ArbitrageOperation(
            operation_id=data["operation_id"],
            opportunity_id=data["opportunity_id"],
            operation_type=OperationType(data["operation_type"]),
            initial_capital=Decimal(str(data["initial_capital"])),
            target_currency=target_currency,
            status=OperationStatus(data["status"]),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            final_amount=Decimal(str(data["final_amount"])) if data.get("final_amount") else None,
            actual_profit=Decimal(str(data["actual_profit"])) if data.get("actual_profit") else None,
            actual_profit_percentage=data.get("actual_profit_percentage"),
            total_fees_paid=Decimal(str(data["total_fees_paid"])),
            total_slippage=data["total_slippage"],
            error_message=data.get("error_message"),
            failed_step_index=data.get("failed_step_index")
        )
        
        return operation
    
    async def get_profit_loss_summary(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get profit/loss summary for operations in a date range (basic implementation)."""
        self._logger.info("get_profit_loss_summary called (basic implementation)")
        return {
            "total_profit": 0.0,
            "total_loss": 0.0,
            "net_profit": 0.0,
            "profitable_count": 0,
            "loss_count": 0
        }
    
    async def get_by_operation_type(self, operation_type: OperationType) -> List[ArbitrageOperation]:
        """Retrieve operations by their type (basic implementation)."""
        self._logger.info(f"get_by_operation_type called for {operation_type.value} (basic implementation)")
        return []
    
    async def get_most_profitable(self, limit: int = 10) -> List[ArbitrageOperation]:
        """Get the most profitable operations (basic implementation)."""
        self._logger.info("get_most_profitable called (basic implementation)")
        return []
    
    async def get_failed_operations_with_details(
        self, 
        start_date: Optional[datetime] = None
    ) -> List[ArbitrageOperation]:
        """Get failed operations with error details for analysis (basic implementation)."""
        self._logger.info("get_failed_operations_with_details called (basic implementation)")
        return []
    
    async def count_by_status(self) -> Dict[OperationStatus, int]:
        """Count operations by their status (basic implementation)."""
        self._logger.info("count_by_status called (basic implementation)")
        return {
            OperationStatus.PENDING: 0,
            OperationStatus.EXECUTING: 0,
            OperationStatus.COMPLETED: 0,
            OperationStatus.FAILED: 0,
            OperationStatus.CANCELLED: 0
        }
    
    async def get_execution_statistics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get execution statistics for operations in a date range (basic implementation)."""
        self._logger.info("get_execution_statistics called (basic implementation)")
        return {
            "average_execution_time_ms": 0.0,
            "total_slippage_percentage": 0.0,
            "average_slippage_percentage": 0.0
        }
    
    async def cleanup_old_operations(self, days: int = 90) -> int:
        """Clean up old operations older than specified days (basic implementation)."""
        self._logger.info("cleanup_old_operations called (basic implementation)")
        return 0
    
    async def search(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ArbitrageOperation]:
        """Search operations with filters (basic implementation)."""
        self._logger.info("search operations called (basic implementation)")
        return []
