"""
OrderExecutor - Single responsibility for executing trading orders.
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
import time

from ...domain.entities.execution_step import ExecutionStep, StepStatus, OrderSide, OrderType
from ...domain.entities.arbitrage_operation import ArbitrageOperation
from ...domain.value_objects.currency import Currency
from ...domain.value_objects.price import Price
from ...infrastructure.external_apis.binance_client import BinanceClient
from ...utils.logger import get_logger


class OrderExecutor:
    """
    Responsible ONLY for executing individual trading orders.
    
    Applies Single Responsibility Principle - this class has only one reason to change:
    when the order execution logic changes.
    """
    
    def __init__(self, binance_client: BinanceClient):
        self._binance_client = binance_client
        self._logger = get_logger(self.__class__.__name__)
    
    async def execute_order(
        self, 
        step: ExecutionStep,
        validate_balance: bool = True
    ) -> ExecutionStep:
        """
        Execute a single trading order.
        
        Args:
            step: Execution step to execute
            validate_balance: Whether to validate balance before execution
            
        Returns:
            Updated execution step with results
        """
        self._logger.info(f"Executing order: {step}")
        
        try:
            # Start execution
            step.start_execution()
            
            # Validate balance if requested
            if validate_balance:
                if not await self._validate_balance(step):
                    step.fail_step("Insufficient balance for order")
                    return step
            
            # Get current market price for slippage calculation
            current_price = await self._get_current_price(step.trading_pair)
            if current_price:
                step.requested_price = Price(current_price, step.from_currency)
            
            # Execute the order
            order_result = await self._place_market_order(step)
            
            if not order_result:
                step.fail_step("Order execution failed")
                return step
            
            # Process order result
            await self._process_order_result(step, order_result)
            
            self._logger.info(f"Order executed successfully: {step.step_id}")
            return step
            
        except Exception as e:
            error_msg = f"Error executing order {step.step_id}: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            step.fail_step(error_msg)
            return step
    
    async def _validate_balance(self, step: ExecutionStep) -> bool:
        """Validate that sufficient balance is available for the order."""
        try:
            balances = self._binance_client.get_balances()
            if not balances:
                self._logger.error("Could not retrieve balances for validation")
                return False
            
            # Find balance for the currency we're trading from
            available_balance = next(
                (float(b["free"]) for b in balances if b["asset"] == step.from_currency.symbol), 
                0.0
            )
            
            required_amount = float(step.requested_quantity)
            
            if available_balance < required_amount:
                self._logger.error(
                    f"Insufficient balance. Required: {required_amount} {step.from_currency.symbol}, "
                    f"Available: {available_balance}"
                )
                return False
            
            self._logger.info(f"Balance validation passed: {available_balance} {step.from_currency.symbol} available")
            return True
            
        except Exception as e:
            self._logger.error(f"Error validating balance: {e}")
            return False
    
    async def _get_current_price(self, trading_pair: str) -> Optional[Decimal]:
        """Get current market price for a trading pair."""
        try:
            ticker = self._binance_client.obtener_precio_ticker(trading_pair)
            if ticker and "price" in ticker:
                return Decimal(str(ticker["price"]))
            
            self._logger.warning(f"Could not get current price for {trading_pair}")
            return None
            
        except Exception as e:
            self._logger.error(f"Error getting current price for {trading_pair}: {e}")
            return None
    
    async def _place_market_order(self, step: ExecutionStep) -> Optional[Dict[str, Any]]:
        """Place a market order on the exchange."""
        try:
            # Round quantity according to trading pair rules
            rounded_quantity = self._binance_client.redondear_cantidad(
                step.trading_pair, 
                step.requested_quantity
            )
            
            if rounded_quantity <= 0:
                self._logger.error(f"Rounded quantity is zero for {step.trading_pair}")
                return None
            
            # Place market order
            order_result = self._binance_client.crear_orden_mercado(
                symbol=step.trading_pair,
                side=step.order_side.value,
                quantity=float(rounded_quantity)
            )
            
            if not order_result:
                self._logger.error(f"Order placement failed for {step.trading_pair}")
                return None
            
            # Validate order result
            if order_result.get("status") != "FILLED":
                self._logger.error(f"Order not filled. Status: {order_result.get('status')}")
                return None
            
            self._logger.info(f"Market order placed successfully: {order_result.get('orderId')}")
            return order_result
            
        except Exception as e:
            self._logger.error(f"Error placing market order: {e}")
            return None
    
    async def _process_order_result(self, step: ExecutionStep, order_result: Dict[str, Any]) -> None:
        """Process the order result and update the execution step."""
        try:
            # Extract execution details
            executed_qty = Decimal(str(order_result.get("executedQty", 0)))
            cummulative_quote_qty = Decimal(str(order_result.get("cummulativeQuoteQty", 0)))
            
            # Calculate average executed price
            if executed_qty > 0:
                avg_price = cummulative_quote_qty / executed_qty
            else:
                avg_price = Decimal("0")
            
            # Calculate fees
            total_commission = Decimal("0")
            fee_asset = step.from_currency.symbol  # Default
            
            if "fills" in order_result:
                for fill in order_result["fills"]:
                    commission = Decimal(str(fill.get("commission", 0)))
                    total_commission += commission
                    
                    # Use the commission asset from the first fill
                    if fill.get("commissionAsset"):
                        fee_asset = fill["commissionAsset"]
            
            # Update step with execution results
            step.complete_successfully(
                executed_quantity=executed_qty,
                executed_price=Price(avg_price, step.from_currency),
                fee_amount=total_commission,
                exchange_order_id=order_result.get("orderId"),
                trade_ids=[fill.get("tradeId") for fill in order_result.get("fills", [])]
            )
            
            self._logger.info(
                f"Order processed: {executed_qty} at {avg_price}, "
                f"fees: {total_commission} {fee_asset}"
            )
            
        except Exception as e:
            error_msg = f"Error processing order result: {e}"
            self._logger.error(error_msg)
            step.fail_step(error_msg)
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a pending order."""
        try:
            result = self._binance_client.cancelar_orden(symbol, order_id)
            if result:
                self._logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                self._logger.error(f"Failed to cancel order {order_id}")
                return False
                
        except Exception as e:
            self._logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an order."""
        try:
            return self._binance_client.obtener_estado_orden(symbol, order_id)
        except Exception as e:
            self._logger.error(f"Error getting order status for {order_id}: {e}")
            return None
