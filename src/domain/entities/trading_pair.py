"""
TradingPair Entity - Represents a trading pair with its rules and constraints.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

from ..value_objects.currency import Currency
from ..value_objects.price import Price


class PairStatus(Enum):
    """Trading status of a pair."""
    TRADING = "TRADING"
    BREAK = "BREAK"
    AUCTION_ONLY = "AUCTION_ONLY"
    HALT = "HALT"
    MAINTENANCE = "MAINTENANCE"


class OrderType(Enum):
    """Supported order types for the pair."""
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"


@dataclass
class TradingPair:
    """
    Domain entity representing a trading pair with its business rules and constraints.
    
    Contains all trading rules, filters, and constraints for a specific trading pair.
    """
    
    # Identity
    symbol: str
    base_asset: Currency
    quote_asset: Currency
    
    # Trading status
    status: PairStatus = PairStatus.TRADING
    
    # Price constraints
    min_price: Optional[Price] = None
    max_price: Optional[Price] = None
    tick_size: Optional[Decimal] = None  # Minimum price increment
    
    # Quantity constraints
    min_qty: Optional[Decimal] = None
    max_qty: Optional[Decimal] = None
    step_size: Optional[Decimal] = None  # Minimum quantity increment
    
    # Notional constraints (price * quantity)
    min_notional: Optional[Decimal] = None
    max_notional: Optional[Decimal] = None
    
    # Order types and permissions
    allowed_order_types: List[OrderType] = None
    spot_trading_allowed: bool = True
    margin_trading_allowed: bool = False
    
    # Market maker protections
    max_num_orders: Optional[int] = None
    max_num_algo_orders: Optional[int] = None
    
    # Commission and fees
    base_commission_precision: int = 8
    quote_commission_precision: int = 8
    
    # Liquidity and volume
    iceberg_allowed: bool = True
    oco_allowed: bool = True  # One-Cancels-Other orders
    quote_order_qty_market_allowed: bool = True
    
    # Exchange specific
    exchange: str = "BINANCE"
    
    def __post_init__(self):
        """Initialize default values and validate constraints."""
        if self.allowed_order_types is None:
            self.allowed_order_types = [OrderType.LIMIT, OrderType.MARKET]
        
        self._validate_trading_pair()
    
    def _validate_trading_pair(self) -> None:
        """Validate trading pair business rules."""
        # Validate symbol format
        expected_symbol = f"{self.base_asset.symbol}{self.quote_asset.symbol}"
        if self.symbol != expected_symbol:
            raise ValueError(f"Symbol {self.symbol} doesn't match assets {expected_symbol}")
        
        # Validate price constraints
        if self.min_price and self.max_price:
            if self.min_price.amount >= self.max_price.amount:
                raise ValueError("Min price must be less than max price")
        
        # Validate quantity constraints
        if self.min_qty and self.max_qty:
            if self.min_qty >= self.max_qty:
                raise ValueError("Min quantity must be less than max quantity")
        
        # Validate notional constraints
        if self.min_notional and self.max_notional:
            if self.min_notional >= self.max_notional:
                raise ValueError("Min notional must be less than max notional")
        
        # Validate step sizes are positive
        if self.tick_size and self.tick_size <= 0:
            raise ValueError("Tick size must be positive")
        
        if self.step_size and self.step_size <= 0:
            raise ValueError("Step size must be positive")
    
    def is_tradeable(self) -> bool:
        """Check if the pair is currently tradeable."""
        return self.status == PairStatus.TRADING and self.spot_trading_allowed
    
    def supports_order_type(self, order_type: OrderType) -> bool:
        """Check if the pair supports a specific order type."""
        return order_type in self.allowed_order_types
    
    def round_price(self, price: Decimal) -> Decimal:
        """Round price according to tick size constraints."""
        if not self.tick_size:
            return price
        
        # Round to nearest tick size
        return (price / self.tick_size).quantize(Decimal('1')) * self.tick_size
    
    def round_quantity(self, quantity: Decimal) -> Decimal:
        """Round quantity according to step size constraints."""
        if not self.step_size:
            return quantity
        
        # Round down to nearest step size to ensure we don't exceed order limits
        return (quantity / self.step_size).quantize(Decimal('1'), rounding='ROUND_DOWN') * self.step_size
    
    def validate_price(self, price: Decimal) -> bool:
        """Validate if a price is within allowed constraints."""
        if self.min_price and price < self.min_price.amount:
            return False
        
        if self.max_price and price > self.max_price.amount:
            return False
        
        # Check if price conforms to tick size
        if self.tick_size:
            remainder = price % self.tick_size
            if remainder != 0:
                return False
        
        return True
    
    def validate_quantity(self, quantity: Decimal) -> bool:
        """Validate if a quantity is within allowed constraints."""
        if self.min_qty and quantity < self.min_qty:
            return False
        
        if self.max_qty and quantity > self.max_qty:
            return False
        
        # Check if quantity conforms to step size
        if self.step_size:
            remainder = quantity % self.step_size
            if remainder != 0:
                return False
        
        return True
    
    def validate_notional(self, price: Decimal, quantity: Decimal) -> bool:
        """Validate if the notional value (price * quantity) is within constraints."""
        notional = price * quantity
        
        if self.min_notional and notional < self.min_notional:
            return False
        
        if self.max_notional and notional > self.max_notional:
            return False
        
        return True
    
    def validate_order(self, order_type: OrderType, price: Decimal, quantity: Decimal) -> Dict[str, Any]:
        """Comprehensive order validation."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if pair is tradeable
        if not self.is_tradeable():
            validation_result["valid"] = False
            validation_result["errors"].append(f"Pair {self.symbol} is not tradeable (status: {self.status.value})")
        
        # Check order type support
        if not self.supports_order_type(order_type):
            validation_result["valid"] = False
            validation_result["errors"].append(f"Order type {order_type.value} not supported for {self.symbol}")
        
        # Validate price (for limit orders)
        if order_type in [OrderType.LIMIT, OrderType.STOP_LOSS_LIMIT, OrderType.TAKE_PROFIT_LIMIT]:
            if not self.validate_price(price):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Price {price} violates price constraints")
        
        # Validate quantity
        if not self.validate_quantity(quantity):
            validation_result["valid"] = False
            validation_result["errors"].append(f"Quantity {quantity} violates quantity constraints")
        
        # Validate notional
        if not self.validate_notional(price, quantity):
            validation_result["valid"] = False
            validation_result["errors"].append(f"Notional value {price * quantity} violates notional constraints")
        
        return validation_result
    
    def get_adjusted_order_params(self, price: Decimal, quantity: Decimal) -> Dict[str, Decimal]:
        """Get adjusted order parameters that comply with pair constraints."""
        adjusted_price = self.round_price(price)
        adjusted_quantity = self.round_quantity(quantity)
        
        # Ensure minimum constraints are met
        if self.min_qty and adjusted_quantity < self.min_qty:
            adjusted_quantity = self.min_qty
        
        # Ensure notional constraints are met
        if self.min_notional:
            notional = adjusted_price * adjusted_quantity
            if notional < self.min_notional:
                # Increase quantity to meet min notional
                adjusted_quantity = self.round_quantity(self.min_notional / adjusted_price)
        
        return {
            "price": adjusted_price,
            "quantity": adjusted_quantity,
            "notional": adjusted_price * adjusted_quantity
        }
    
    def calculate_max_quantity_for_notional(self, price: Decimal, max_notional: Decimal) -> Decimal:
        """Calculate maximum quantity that can be traded for a given notional value."""
        if price <= 0:
            return Decimal("0")
        
        max_qty_from_notional = max_notional / price
        
        # Apply quantity constraints
        if self.max_qty:
            max_qty_from_notional = min(max_qty_from_notional, self.max_qty)
        
        # Round down to valid step size
        return self.round_quantity(max_qty_from_notional)
    
    def get_minimum_order_value(self) -> Optional[Decimal]:
        """Get the minimum order value required for this pair."""
        if not self.min_notional:
            return None
        
        return self.min_notional
    
    def get_pair_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the trading pair."""
        return {
            "symbol": self.symbol,
            "base_asset": self.base_asset.symbol,
            "quote_asset": self.quote_asset.symbol,
            "status": self.status.value,
            "is_tradeable": self.is_tradeable(),
            "min_price": float(self.min_price.amount) if self.min_price else None,
            "max_price": float(self.max_price.amount) if self.max_price else None,
            "tick_size": float(self.tick_size) if self.tick_size else None,
            "min_qty": float(self.min_qty) if self.min_qty else None,
            "max_qty": float(self.max_qty) if self.max_qty else None,
            "step_size": float(self.step_size) if self.step_size else None,
            "min_notional": float(self.min_notional) if self.min_notional else None,
            "max_notional": float(self.max_notional) if self.max_notional else None,
            "allowed_order_types": [ot.value for ot in self.allowed_order_types],
            "spot_trading_allowed": self.spot_trading_allowed,
            "margin_trading_allowed": self.margin_trading_allowed,
            "exchange": self.exchange
        }
    
    def __str__(self) -> str:
        """String representation of the trading pair."""
        return f"TradingPair {self.symbol} ({self.status.value})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on symbol."""
        if not isinstance(other, TradingPair):
            return False
        return self.symbol == other.symbol
    
    def __hash__(self) -> int:
        """Hash based on symbol."""
        return hash(self.symbol)
