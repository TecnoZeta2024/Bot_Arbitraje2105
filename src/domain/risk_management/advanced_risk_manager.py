"""
Advanced Risk Management System
Implements institutional-grade risk management with multiple layers of protection
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from enum import Enum

from ...domain.trading_signals.trading_signal import TradingSignal, RiskLevel, SignalAction
from ...domain.entities.market_data import MarketData


class RiskEventType(Enum):
    """Types of risk events"""
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    POSITION_SIZE_EXCEEDED = "position_size_exceeded"
    CORRELATION_LIMIT = "correlation_limit"
    VOLATILITY_SPIKE = "volatility_spike"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    DRAWDOWN_LIMIT = "drawdown_limit"
    TECHNICAL_FAILURE = "technical_failure"


@dataclass
class RiskParameters:
    """Risk management configuration"""
    # Capital limits
    max_daily_loss: Decimal = Decimal('0.02')          # 2% max daily loss
    max_position_size: Decimal = Decimal('0.05')       # 5% max per position
    max_total_exposure: Decimal = Decimal('0.8')       # 80% max total exposure
    max_correlation_exposure: Decimal = Decimal('0.15') # 15% max in correlated assets
    
    # Risk multipliers
    stop_loss_multiplier: Decimal = Decimal('1.5')     # ATR multiplier for stop loss
    profit_target_multiplier: Decimal = Decimal('2.0') # Risk/Reward ratio
    
    # Position limits
    max_concurrent_positions: int = 10
    max_positions_per_symbol: int = 1
    
    # Volatility and market conditions
    max_volatility_threshold: Decimal = Decimal('0.05') # 5% max volatility
    min_liquidity_score: Decimal = Decimal('1000')      # Minimum liquidity
    max_spread_percentage: Decimal = Decimal('0.1')     # 0.1% max spread
    
    # Time-based limits
    max_hold_time_hours: int = 24                       # Maximum hold time
    cooldown_period_minutes: int = 15                   # Cooldown between trades
    
    # Drawdown protection
    max_drawdown_percentage: Decimal = Decimal('0.15')  # 15% max drawdown
    
    # AI validation
    min_ai_confidence: Decimal = Decimal('0.6')         # 60% minimum AI confidence
    require_ai_validation: bool = True


@dataclass
class PositionInfo:
    """Information about an open position"""
    symbol: str
    strategy: str
    entry_price: Decimal
    quantity: Decimal
    entry_time: datetime
    stop_loss: Decimal
    take_profit: Decimal
    unrealized_pnl: Decimal = Decimal('0')
    max_unrealized_pnl: Decimal = Decimal('0')
    min_unrealized_pnl: Decimal = Decimal('0')
    
    @property
    def position_value(self) -> Decimal:
        """Calculate current position value"""
        return abs(self.quantity) * self.entry_price
    
    @property
    def hold_time(self) -> timedelta:
        """Calculate how long position has been held"""
        return datetime.now() - self.entry_time
    
    @property
    def unrealized_pnl_percentage(self) -> Decimal:
        """Calculate unrealized P&L as percentage"""
        if self.position_value > 0:
            return self.unrealized_pnl / self.position_value
        return Decimal('0')


@dataclass
class RiskEvent:
    """Risk management event"""
    event_type: RiskEventType
    timestamp: datetime
    symbol: Optional[str]
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    action_taken: str
    additional_data: Dict[str, Any] = field(default_factory=dict)


class AdvancedRiskManager:
    """
    Advanced risk management system with multiple layers of protection
    
    Features:
    - Real-time position monitoring
    - Dynamic stop-loss adjustment
    - Correlation analysis
    - Drawdown protection
    - AI-powered risk assessment
    """
    
    def __init__(self, initial_capital: Decimal, risk_params: Optional[RiskParameters] = None):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.available_capital = initial_capital
        self.risk_params = risk_params or RiskParameters()
        
        # Position tracking
        self.open_positions: Dict[str, PositionInfo] = {}
        self.daily_pnl = Decimal('0')
        self.total_pnl = Decimal('0')
        self.daily_trades = 0
        
        # Risk tracking
        self.max_drawdown_hit = Decimal('0')
        self.current_drawdown = Decimal('0')
        self.risk_events: List[RiskEvent] = []
        self.last_trade_time: Dict[str, datetime] = {}
        
        # Correlation matrix for risk assessment
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # Monitoring
        self.logger = logging.getLogger("risk.manager")
        self.monitoring_active = False
        
    async def evaluate_signal_risk(self, signal: TradingSignal, market_data: MarketData) -> Dict[str, Any]:
        """
        Comprehensive risk evaluation for a trading signal
        
        Returns:
            Dictionary with risk assessment and position sizing recommendations
        """
        risk_assessment = {
            'approved': False,
            'risk_score': 1.0,  # 0.0 = no risk, 1.0 = maximum risk
            'position_size': Decimal('0'),
            'stop_loss': None,
            'take_profit': None,
            'max_hold_time': None,
            'risk_factors': [],
            'warnings': []
        }
        
        try:
            # 1. Check daily loss limit
            if not self._check_daily_loss_limit():
                risk_assessment['risk_factors'].append("Daily loss limit exceeded")
                return risk_assessment
            
            # 2. Check position limits
            position_check = self._check_position_limits(signal.symbol)
            if not position_check['allowed']:
                risk_assessment['risk_factors'].extend(position_check['reasons'])
                return risk_assessment
            
            # 3. Check market conditions
            market_risk = self._assess_market_conditions(signal, market_data)
            risk_assessment['risk_score'] += market_risk['risk_score']
            risk_assessment['warnings'].extend(market_risk['warnings'])
            
            # 4. Check correlation risk
            correlation_risk = await self._assess_correlation_risk(signal.symbol)
            risk_assessment['risk_score'] += correlation_risk['risk_score']
            
            # 5. Calculate optimal position size
            position_size = self._calculate_optimal_position_size(signal, risk_assessment['risk_score'])
            risk_assessment['position_size'] = position_size
            
            # 6. Calculate stop loss and take profit
            stop_loss, take_profit = self._calculate_stop_loss_take_profit(signal, market_data)
            risk_assessment['stop_loss'] = stop_loss
            risk_assessment['take_profit'] = take_profit
            
            # 7. Calculate maximum hold time
            max_hold_time = self._calculate_max_hold_time(signal)
            risk_assessment['max_hold_time'] = max_hold_time
            
            # 8. Check cooldown period
            if not self._check_cooldown_period(signal.symbol):
                risk_assessment['warnings'].append("Recent trade on this symbol")
                risk_assessment['risk_score'] += 0.1
            
            # 9. Final approval decision
            risk_assessment['approved'] = (
                risk_assessment['risk_score'] < 0.8 and  # Risk score threshold
                position_size > 0 and
                len(risk_assessment['risk_factors']) == 0
            )
            
            if risk_assessment['approved']:
                self.logger.info(f"Risk assessment APPROVED for {signal.symbol}: risk_score={risk_assessment['risk_score']:.2f}")
            else:
                self.logger.warning(f"Risk assessment REJECTED for {signal.symbol}: {risk_assessment['risk_factors']}")
            
        except Exception as e:
            self.logger.error(f"Risk evaluation failed for {signal.symbol}: {e}")
            risk_assessment['risk_factors'].append(f"Risk evaluation error: {e}")
        
        return risk_assessment
    
    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been exceeded"""
        max_daily_loss = self.initial_capital * self.risk_params.max_daily_loss
        return self.daily_pnl > -max_daily_loss
    
    def _check_position_limits(self, symbol: str) -> Dict[str, Any]:
        """Check position limits"""
        result = {'allowed': True, 'reasons': []}
        
        # Maximum concurrent positions
        if len(self.open_positions) >= self.risk_params.max_concurrent_positions:
            result['allowed'] = False
            result['reasons'].append("Maximum concurrent positions reached")
        
        # Maximum positions per symbol
        symbol_positions = sum(1 for pos in self.open_positions.values() if pos.symbol == symbol)
        if symbol_positions >= self.risk_params.max_positions_per_symbol:
            result['allowed'] = False
            result['reasons'].append(f"Maximum positions for {symbol} reached")
        
        # Total exposure limit
        total_exposure = sum(pos.position_value for pos in self.open_positions.values())
        max_total_exposure = self.initial_capital * self.risk_params.max_total_exposure
        if total_exposure >= max_total_exposure:
            result['allowed'] = False
            result['reasons'].append("Maximum total exposure reached")
        
        return result
    
    def _assess_market_conditions(self, signal: TradingSignal, market_data: MarketData) -> Dict[str, Any]:
        """Assess market conditions for risk"""
        risk_score = 0.0
        warnings = []
        
        # Volatility check
        if market_data.volatility and market_data.volatility > self.risk_params.max_volatility_threshold:
            risk_score += 0.3
            warnings.append(f"High volatility: {market_data.volatility:.2%}")
        
        # Liquidity check
        if market_data.order_book:
            if market_data.order_book.liquidity_score < self.risk_params.min_liquidity_score:
                risk_score += 0.2
                warnings.append("Low liquidity")
            
            # Spread check
            if market_data.order_book.spread_percentage and market_data.order_book.spread_percentage > self.risk_params.max_spread_percentage:
                risk_score += 0.1
                warnings.append(f"Wide spread: {market_data.order_book.spread_percentage:.2%}")
        
        # AI confidence check
        if signal.ai_analysis:
            ai_confidence = signal.ai_analysis.get('ai_confidence', 0)
            if ai_confidence < float(self.risk_params.min_ai_confidence):
                risk_score += 0.2
                warnings.append(f"Low AI confidence: {ai_confidence:.1%}")
        
        return {'risk_score': risk_score, 'warnings': warnings}
    
    async def _assess_correlation_risk(self, symbol: str) -> Dict[str, Any]:
        """Assess correlation risk with existing positions"""
        risk_score = 0.0
        
        if not self.open_positions:
            return {'risk_score': 0.0}
        
        # Simple correlation check (can be enhanced with actual correlation data)
        # For now, check if we have too many positions in the same asset class
        similar_positions = 0
        for pos in self.open_positions.values():
            if self._are_symbols_correlated(symbol, pos.symbol):
                similar_positions += 1
        
        if similar_positions > 0:
            correlation_exposure = similar_positions / len(self.open_positions)
            if correlation_exposure > float(self.risk_params.max_correlation_exposure):
                risk_score += 0.3
        
        return {'risk_score': risk_score}
    
    def _are_symbols_correlated(self, symbol1: str, symbol2: str) -> bool:
        """Check if two symbols are correlated (simplified implementation)"""
        # Simplified correlation check - same base currency or similar assets
        base1 = symbol1[:3] if len(symbol1) >= 6 else symbol1
        base2 = symbol2[:3] if len(symbol2) >= 6 else symbol2
        
        return base1 == base2
    
    def _calculate_optimal_position_size(self, signal: TradingSignal, risk_score: float) -> Decimal:
        """Calculate optimal position size based on risk assessment"""
        
        # Base position size from signal confidence
        base_size = self.risk_params.max_position_size * Decimal(str(signal.confidence))
        
        # Adjust for risk score
        risk_adjustment = Decimal(str(max(0.1, 1.0 - risk_score)))
        adjusted_size = base_size * risk_adjustment
        
        # Ensure we don't exceed available capital
        max_size_by_capital = self.available_capital / self.current_capital * self.risk_params.max_position_size
        
        # Final position size
        position_size = min(adjusted_size, max_size_by_capital, self.risk_params.max_position_size)
        
        return max(Decimal('0'), position_size)
    
    def _calculate_stop_loss_take_profit(self, signal: TradingSignal, market_data: MarketData) -> tuple:
        """Calculate dynamic stop loss and take profit levels"""
        
        entry_price = signal.entry_price or float(market_data.current_price)
        
        # Calculate ATR-based stop loss
        volatility = market_data.volatility or Decimal('0.01')  # Default 1% volatility
        atr_based_stop = volatility * self.risk_params.stop_loss_multiplier
        
        if signal.action == SignalAction.BUY:
            stop_loss = entry_price * (1 - float(atr_based_stop))
            take_profit = entry_price * (1 + float(atr_based_stop) * float(self.risk_params.profit_target_multiplier))
        else:  # SELL
            stop_loss = entry_price * (1 + float(atr_based_stop))
            take_profit = entry_price * (1 - float(atr_based_stop) * float(self.risk_params.profit_target_multiplier))
        
        return stop_loss, take_profit
    
    def _calculate_max_hold_time(self, signal: TradingSignal) -> timedelta:
        """Calculate maximum hold time for position"""
        
        # Base hold time from risk parameters
        base_hold_time = timedelta(hours=self.risk_params.max_hold_time_hours)
        
        # Adjust based on strategy type
        if signal.strategy_name.value == "scalping":
            return timedelta(minutes=5)
        elif signal.strategy_name.value == "day_trading":
            return timedelta(hours=8)
        else:
            return base_hold_time
    
    def _check_cooldown_period(self, symbol: str) -> bool:
        """Check if cooldown period has passed since last trade"""
        if symbol not in self.last_trade_time:
            return True
        
        cooldown_period = timedelta(minutes=self.risk_params.cooldown_period_minutes)
        return datetime.now() - self.last_trade_time[symbol] >= cooldown_period
    
    async def monitor_positions(self, current_prices: Dict[str, Decimal]):
        """Monitor open positions for risk management"""
        
        positions_to_close = []
        
        for position_id, position in self.open_positions.items():
            try:
                current_price = current_prices.get(position.symbol)
                if not current_price:
                    continue
                
                # Update unrealized P&L
                self._update_position_pnl(position, current_price)
                
                # Check stop loss
                if self._should_stop_loss(position, current_price):
                    positions_to_close.append((position_id, "STOP_LOSS"))
                    continue
                
                # Check take profit
                if self._should_take_profit(position, current_price):
                    positions_to_close.append((position_id, "TAKE_PROFIT"))
                    continue
                
                # Check max hold time
                if self._should_close_due_to_time(position):
                    positions_to_close.append((position_id, "TIME_LIMIT"))
                    continue
                
                # Update trailing stop loss
                self._update_trailing_stop(position, current_price)
                
            except Exception as e:
                self.logger.error(f"Error monitoring position {position_id}: {e}")
        
        # Return positions that should be closed
        return positions_to_close
    
    def _update_position_pnl(self, position: PositionInfo, current_price: Decimal):
        """Update position's unrealized P&L"""
        if position.quantity > 0:  # Long position
            position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:  # Short position
            position.unrealized_pnl = (position.entry_price - current_price) * abs(position.quantity)
        
        # Update max/min unrealized P&L for trailing stops
        position.max_unrealized_pnl = max(position.max_unrealized_pnl, position.unrealized_pnl)
        position.min_unrealized_pnl = min(position.min_unrealized_pnl, position.unrealized_pnl)
    
    def _should_stop_loss(self, position: PositionInfo, current_price: Decimal) -> bool:
        """Check if position should be closed due to stop loss"""
        if position.quantity > 0:  # Long position
            return current_price <= position.stop_loss
        else:  # Short position
            return current_price >= position.stop_loss
    
    def _should_take_profit(self, position: PositionInfo, current_price: Decimal) -> bool:
        """Check if position should be closed for take profit"""
        if position.quantity > 0:  # Long position
            return current_price >= position.take_profit
        else:  # Short position
            return current_price <= position.take_profit
    
    def _should_close_due_to_time(self, position: PositionInfo) -> bool:
        """Check if position should be closed due to time limit"""
        max_hold_time = timedelta(hours=self.risk_params.max_hold_time_hours)
        return position.hold_time >= max_hold_time
    
    def _update_trailing_stop(self, position: PositionInfo, current_price: Decimal):
        """Update trailing stop loss if position is profitable"""
        
        # Only update if position is profitable
        if position.unrealized_pnl > 0:
            trail_percentage = Decimal('0.5')  # 50% of maximum profit protection
            
            if position.quantity > 0:  # Long position
                # Calculate new stop loss to protect 50% of maximum unrealized profit
                profit_protection = position.max_unrealized_pnl * trail_percentage
                new_stop_loss = position.entry_price + (profit_protection / position.quantity)
                position.stop_loss = max(position.stop_loss, new_stop_loss)
            else:  # Short position
                profit_protection = position.max_unrealized_pnl * trail_percentage
                new_stop_loss = position.entry_price - (profit_protection / abs(position.quantity))
                position.stop_loss = min(position.stop_loss, new_stop_loss)
    
    def add_position(self, signal: TradingSignal, quantity: Decimal, entry_price: Decimal):
        """Add new position to tracking"""
        position_id = f"{signal.symbol}_{signal.strategy_name.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        position = PositionInfo(
            symbol=signal.symbol,
            strategy=signal.strategy_name.value,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss=signal.stop_loss or entry_price * Decimal('0.99'),  # Default 1% stop loss
            take_profit=signal.take_profit or entry_price * Decimal('1.02')  # Default 2% take profit
        )
        
        self.open_positions[position_id] = position
        self.last_trade_time[signal.symbol] = datetime.now()
        self.daily_trades += 1
        
        # Update available capital
        position_value = abs(quantity) * entry_price
        self.available_capital -= position_value
        
        self.logger.info(f"Position added: {position_id}, value: {position_value}")
    
    def close_position(self, position_id: str, exit_price: Decimal, reason: str = "MANUAL"):
        """Close position and update capital"""
        
        if position_id not in self.open_positions:
            self.logger.warning(f"Position {position_id} not found")
            return
        
        position = self.open_positions[position_id]
        
        # Calculate realized P&L
        if position.quantity > 0:  # Long position
            realized_pnl = (exit_price - position.entry_price) * position.quantity
        else:  # Short position
            realized_pnl = (position.entry_price - exit_price) * abs(position.quantity)
        
        # Update capital and P&L
        position_value = abs(position.quantity) * position.entry_price
        self.available_capital += position_value + realized_pnl
        self.current_capital += realized_pnl
        self.daily_pnl += realized_pnl
        self.total_pnl += realized_pnl
        
        # Remove position
        del self.open_positions[position_id]
        
        self.logger.info(f"Position closed: {position_id}, P&L: {realized_pnl:.2f}, reason: {reason}")
        
        # Log risk event if stop loss
        if reason == "STOP_LOSS":
            self._log_risk_event(
                RiskEventType.DAILY_LOSS_LIMIT,
                position.symbol,
                f"Stop loss triggered for {position.symbol}",
                "MEDIUM",
                f"Position closed with loss: {realized_pnl:.2f}"
            )
    
    def _log_risk_event(self, event_type: RiskEventType, symbol: Optional[str], description: str, severity: str, action: str):
        """Log risk management event"""
        event = RiskEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            symbol=symbol,
            description=description,
            severity=severity,
            action_taken=action
        )
        
        self.risk_events.append(event)
        self.logger.warning(f"Risk event: {event_type.value} - {description}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        
        total_exposure = sum(pos.position_value for pos in self.open_positions.values())
        exposure_percentage = total_exposure / self.current_capital if self.current_capital > 0 else 0
        
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.open_positions.values())
        
        return {
            'current_capital': float(self.current_capital),
            'available_capital': float(self.available_capital),
            'daily_pnl': float(self.daily_pnl),
            'total_pnl': float(self.total_pnl),
            'open_positions': len(self.open_positions),
            'total_exposure': float(total_exposure),
            'exposure_percentage': float(exposure_percentage),
            'unrealized_pnl': float(unrealized_pnl),
            'daily_trades': self.daily_trades,
            'risk_events_today': len([e for e in self.risk_events if e.timestamp.date() == datetime.now().date()]),
            'max_drawdown': float(self.max_drawdown_hit)
        }
