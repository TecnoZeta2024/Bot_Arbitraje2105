"""
PositionManager - Single responsibility for managing trading positions.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ...domain.entities.arbitrage_operation import ArbitrageOperation
from ...domain.entities.execution_step import ExecutionStep
from ...domain.value_objects.currency import Currency
from ...infrastructure.external_apis.binance_client import BinanceClient
from ...utils.logger import get_logger


class PositionManager:
    """
    Responsible ONLY for managing trading positions and capital flow.
    
    Applies Single Responsibility Principle - this class has only one reason to change:
    when position management logic changes.
    """
    
    def __init__(self, binance_client: BinanceClient):
        self._binance_client = binance_client
        self._logger = get_logger(self.__class__.__name__)
    
    def track_position_flow(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """
        Track the flow of capital through an arbitrage operation.
        
        Args:
            operation: The arbitrage operation to track
            
        Returns:
            Dictionary with position flow information
        """
        self._logger.info(f"Tracking position flow for operation {operation.operation_id}")
        
        try:
            flow_data = {
                "operation_id": operation.operation_id,
                "initial_capital": float(operation.initial_capital),
                "initial_currency": operation.target_currency.symbol,
                "steps": [],
                "current_position": {
                    "amount": float(operation.initial_capital),
                    "currency": operation.target_currency.symbol
                },
                "total_fees": 0.0,
                "total_slippage": 0.0
            }
            
            current_amount = operation.initial_capital
            current_currency = operation.target_currency.symbol
            
            for i, step in enumerate(operation.execution_steps):
                step_flow = self._calculate_step_flow(step, current_amount, current_currency)
                flow_data["steps"].append(step_flow)
                
                # Update current position
                if step.is_successful():
                    current_amount = step_flow["amount_out"]
                    current_currency = step.to_currency.symbol
                    flow_data["total_fees"] += step_flow["fee_amount"]
                    flow_data["total_slippage"] += step_flow.get("slippage", 0.0)
                
                # Update current position
                flow_data["current_position"] = {
                    "amount": float(current_amount),
                    "currency": current_currency
                }
            
            # Calculate final metrics
            if operation.status.value in ["COMPLETED", "FAILED"]:
                flow_data["final_position"] = flow_data["current_position"]
                flow_data["net_profit"] = float(current_amount - operation.initial_capital)
                flow_data["profit_percentage"] = (
                    (float(current_amount) / float(operation.initial_capital) - 1) * 100
                    if operation.initial_capital > 0 else 0
                )
            
            return flow_data
            
        except Exception as e:
            self._logger.error(f"Error tracking position flow: {e}")
            return {"error": str(e)}
    
    def _calculate_step_flow(
        self, 
        step: ExecutionStep, 
        amount_in: Decimal, 
        currency_in: str
    ) -> Dict[str, Any]:
        """Calculate the capital flow for a single execution step."""
        step_data = {
            "step_number": step.step_number,
            "trading_pair": step.trading_pair,
            "order_side": step.order_side.value,
            "currency_in": currency_in,
            "amount_in": float(amount_in),
            "currency_out": step.to_currency.symbol,
            "amount_out": 0.0,
            "fee_amount": 0.0,
            "fee_currency": "",
            "slippage": 0.0,
            "status": step.status.value
        }
        
        if step.is_successful() and step.executed_quantity and step.executed_price:
            # Calculate amount out based on order side
            if step.order_side.value == "BUY":
                # Buying: amount out is the executed quantity
                step_data["amount_out"] = float(step.executed_quantity)
            else:
                # Selling: amount out is the quote proceeds
                step_data["amount_out"] = float(step.executed_quantity * step.executed_price.amount)
            
            # Fee information
            if step.fee_amount:
                step_data["fee_amount"] = float(step.fee_amount)
                step_data["fee_currency"] = step.fee_currency.symbol if step.fee_currency else ""
            
            # Slippage information
            if step.slippage_percentage:
                step_data["slippage"] = step.slippage_percentage
        
        return step_data
    
    def get_current_balances(self, currencies: List[str]) -> Dict[str, Decimal]:
        """
        Get current balances for specified currencies.
        
        Args:
            currencies: List of currency symbols to check
            
        Returns:
            Dictionary mapping currency to available balance
        """
        try:
            balances = self._binance_client.get_balances()
            if not balances:
                self._logger.error("Could not retrieve balances")
                return {}
            
            currency_balances = {}
            for currency in currencies:
                balance = next(
                    (Decimal(str(b["free"])) for b in balances if b["asset"] == currency),
                    Decimal("0")
                )
                currency_balances[currency] = balance
            
            self._logger.info(f"Retrieved balances for {len(currencies)} currencies")
            return currency_balances
            
        except Exception as e:
            self._logger.error(f"Error getting current balances: {e}")
            return {}
    
    def calculate_position_requirements(
        self, 
        operation: ArbitrageOperation
    ) -> Dict[str, Any]:
        """
        Calculate position requirements for an arbitrage operation.
        
        Args:
            operation: The arbitrage operation
            
        Returns:
            Dictionary with position requirements
        """
        try:
            requirements = {
                "operation_id": operation.operation_id,
                "required_balance": {
                    "currency": operation.target_currency.symbol,
                    "amount": float(operation.initial_capital)
                },
                "estimated_steps": len(operation.execution_steps),
                "risk_factors": self._assess_position_risks(operation)
            }
            
            return requirements
            
        except Exception as e:
            self._logger.error(f"Error calculating position requirements: {e}")
            return {"error": str(e)}
    
    def _assess_position_risks(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """Assess risks associated with the position."""
        risks = {
            "capital_at_risk": float(operation.initial_capital),
            "number_of_trades": len(operation.execution_steps),
            "estimated_total_fees": self._estimate_total_fees(operation),
            "market_risk_factors": []
        }
        
        # Add specific risk factors
        if len(operation.execution_steps) > 3:
            risks["market_risk_factors"].append("High number of execution steps")
        
        if operation.initial_capital > Decimal("1000"):
            risks["market_risk_factors"].append("Large capital amount")
        
        return risks
    
    def _estimate_total_fees(self, operation: ArbitrageOperation) -> float:
        """Estimate total fees for the operation."""
        # Simple estimation: 0.1% per trade
        estimated_fee_rate = 0.001  # 0.1%
        num_trades = len(operation.execution_steps)
        return float(operation.initial_capital) * estimated_fee_rate * num_trades
    
    def validate_position_safety(
        self, 
        operation: ArbitrageOperation, 
        max_capital_percentage: float = 0.1
    ) -> Dict[str, Any]:
        """
        Validate that the position is safe to execute.
        
        Args:
            operation: The arbitrage operation
            max_capital_percentage: Maximum percentage of total capital to risk
            
        Returns:
            Validation result
        """
        try:
            # Get total account balance in USDT equivalent (simplified)
            total_balance = self._get_total_account_value()
            
            validation = {
                "is_safe": True,
                "warnings": [],
                "errors": [],
                "risk_percentage": 0.0
            }
            
            if total_balance > 0:
                risk_percentage = float(operation.initial_capital) / total_balance * 100
                validation["risk_percentage"] = risk_percentage
                
                if risk_percentage > max_capital_percentage * 100:
                    validation["is_safe"] = False
                    validation["errors"].append(
                        f"Operation risks {risk_percentage:.2f}% of total capital "
                        f"(max allowed: {max_capital_percentage * 100:.2f}%)"
                    )
            
            # Additional safety checks
            if operation.initial_capital < Decimal("10"):
                validation["warnings"].append("Very small capital amount")
            
            if len(operation.execution_steps) == 0:
                validation["is_safe"] = False
                validation["errors"].append("No execution steps defined")
            
            return validation
            
        except Exception as e:
            self._logger.error(f"Error validating position safety: {e}")
            return {
                "is_safe": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "risk_percentage": 0.0
            }
    
    def _get_total_account_value(self) -> float:
        """Get total account value in USDT equivalent."""
        try:
            account_info = self._binance_client.get_account_info()
            if account_info and "totalWalletBalance" in account_info:
                return float(account_info["totalWalletBalance"])
            
            # Fallback: sum USDT-like balances
            balances = self._binance_client.get_balances()
            if balances:
                usdt_like = ["USDT", "USDC", "BUSD", "DAI"]
                total = sum(
                    float(b["free"]) + float(b["locked"])
                    for b in balances
                    if b["asset"] in usdt_like
                )
                return total
            
            return 0.0
            
        except Exception as e:
            self._logger.error(f"Error getting total account value: {e}")
            return 0.0
    
    def cleanup_dust_balances(self, min_value_usdt: float = 1.0) -> Dict[str, Any]:
        """
        Identify and optionally clean up dust balances.
        
        Args:
            min_value_usdt: Minimum value in USDT to not consider dust
            
        Returns:
            Information about dust balances
        """
        try:
            balances = self._binance_client.get_balances()
            if not balances:
                return {"error": "Could not retrieve balances"}
            
            dust_balances = []
            significant_balances = []
            
            for balance in balances:
                total_balance = float(balance["free"]) + float(balance["locked"])
                if total_balance > 0:
                    # Simple heuristic: assume non-stablecoin assets need price conversion
                    if balance["asset"] in ["USDT", "USDC", "BUSD", "DAI"]:
                        value_usdt = total_balance
                    else:
                        # For simplicity, assume small amounts are dust
                        value_usdt = total_balance * 0.01  # Very rough estimate
                    
                    if value_usdt < min_value_usdt:
                        dust_balances.append({
                            "asset": balance["asset"],
                            "amount": total_balance,
                            "estimated_value_usdt": value_usdt
                        })
                    else:
                        significant_balances.append({
                            "asset": balance["asset"],
                            "amount": total_balance,
                            "estimated_value_usdt": value_usdt
                        })
            
            return {
                "dust_balances": dust_balances,
                "significant_balances": significant_balances,
                "dust_count": len(dust_balances),
                "total_dust_value": sum(b["estimated_value_usdt"] for b in dust_balances)
            }
            
        except Exception as e:
            self._logger.error(f"Error analyzing dust balances: {e}")
            return {"error": str(e)}
