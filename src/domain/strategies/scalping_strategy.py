"""
Scalping Strategy Implementation
High-frequency trading strategy for small, quick profits
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from domain.entities.market_data import MarketData
from domain.trading_signals.trading_signal import (
    RiskLevel,
    SignalAction,
    StrategyType,
    TradingSignal,
)

from .base_strategy import BaseStrategy


class ScalpingStrategy(BaseStrategy):
    """
    Scalping strategy for capturing small price movements (0.01%-0.1%)
    
    Characteristics:
    - Very short holding periods (5 seconds - 5 minutes)
    - High frequency (50-200 trades per day)
    - Small profit targets with tight stop losses
    - AI-enhanced signal validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ScalpingStrategy")
        
        # Scalping parameters
        self.min_profit_threshold = 0.0001  # 0.01% minimum profit
        self.max_profit_target = 0.001      # 0.1% maximum profit target
        self.stop_loss_percentage = 0.0005  # 0.05% stop loss
        self.max_hold_time = timedelta(minutes=5)  # Maximum 5 minutes hold
        
        # Market condition requirements
        self.min_volume_threshold = 1000000  # $1M minimum 24h volume
        self.max_spread_percentage = 0.05    # 0.05% maximum spread
        
        # Technical indicator settings
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        # Performance tracking
        self.signals_generated = 0
        self.last_signal_time = None
        
        self.logger.info("ScalpingStrategy initialized")
    
    async def analyze(self, market_data: MarketData) -> Optional[TradingSignal]:
        """
        Analyze market data and generate scalping signals
        
        Args:
            market_data: Market data for analysis
            
        Returns:
            Trading signal or None if no signal generated
        """
        try:
            # Pre-filter: Check basic market conditions
            if not self._meets_basic_requirements(market_data):
                return None
            
            # Prevent overtrading - minimum 30 seconds between signals
            if self.last_signal_time and (datetime.now() - self.last_signal_time).total_seconds() < 30:
                return None
            
            # Simple scalping logic based on price movement and volume
            signal = await self._generate_scalping_signal(market_data)
            
            if signal:
                self.signals_generated += 1
                self.last_signal_time = datetime.now()
                self.logger.info(f"Scalping signal generated for {market_data.symbol}: {signal.action.value}")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing {market_data.symbol} for scalping: {e}")
            return None
    
    def _meets_basic_requirements(self, market_data: MarketData) -> bool:
        """Check if market data meets basic scalping requirements"""
        
        # Volume requirement
        if market_data.volume < self.min_volume_threshold:
            return False
        
        # Liquidity requirement
        if not market_data.is_liquid:
            return False
        
        # Spread requirement (if available)
        if (market_data.spread_percentage is not None and 
            market_data.spread_percentage > self.max_spread_percentage):
            return False
        
        return True
    
    async def _generate_scalping_signal(self, market_data: MarketData) -> Optional[TradingSignal]:
        """Generate scalping signal based on simple momentum and mean reversion"""
        
        # Simulate simple momentum/mean reversion analysis
        current_price = market_data.price
        
        # Simulate RSI calculation (simplified)
        simulated_rsi = self._calculate_simple_rsi(market_data)
        
        # Simulate volume analysis
        volume_ratio = self._analyze_volume(market_data)
        
        action = None
        confidence = 0.0
        reasoning = []
        
        # BUY conditions (oversold + volume)
        if simulated_rsi < self.rsi_oversold and volume_ratio > 1.2:
            action = SignalAction.BUY
            confidence = 0.7
            reasoning.append("RSI oversold with volume confirmation")
        
        # SELL conditions (overbought + volume)
        elif simulated_rsi > self.rsi_overbought and volume_ratio > 1.2:
            action = SignalAction.SELL
            confidence = 0.7
            reasoning.append("RSI overbought with volume confirmation")
        
        # Additional momentum signals
        if market_data.price_change_24h:
            if abs(market_data.price_change_24h) > 2.0:  # Strong price movement
                if market_data.price_change_24h > 0:
                    if action == SignalAction.BUY:
                        confidence += 0.1
                        reasoning.append("Positive momentum confirmation")
                elif market_data.price_change_24h < 0:
                    if action == SignalAction.SELL:
                        confidence += 0.1
                        reasoning.append("Negative momentum confirmation")
        
        if action and confidence >= 0.6:  # Minimum confidence threshold
            # Calculate profit target and stop loss
            profit_target = min(
                self.max_profit_target,
                max(self.min_profit_threshold, abs(market_data.price_change_24h or 0) * 0.01)
            )
            
            stop_loss_price = None
            take_profit_price = None
            
            if action == SignalAction.BUY:
                stop_loss_price = current_price * (1 - self.stop_loss_percentage)
                take_profit_price = current_price * (1 + profit_target)
            else:  # SELL
                stop_loss_price = current_price * (1 + self.stop_loss_percentage)
                take_profit_price = current_price * (1 - profit_target)
            
            signal_id = f"scalping_{market_data.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            return TradingSignal(
                signal_id=signal_id,
                timestamp=datetime.now(),
                strategy_name=StrategyType.SCALPING,
                symbol=market_data.symbol,
                action=action,
                confidence=min(confidence, 1.0),
                expected_profit=profit_target * 100,  # Convert to percentage
                risk_level=RiskLevel.MEDIUM,
                timeframe="1m",
                entry_price=current_price,
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                ai_analysis={
                    'reasoning': reasoning,
                    'rsi': simulated_rsi,
                    'volume_ratio': volume_ratio,
                    'confidence': confidence
                }
            )
        
        return None
    
    def _calculate_simple_rsi(self, market_data: MarketData) -> float:
        """Calculate simplified RSI based on available data"""
        # Simplified RSI calculation using 24h price change
        if market_data.price_change_24h is None:
            return 50.0  # Neutral
        
        # Convert price change to RSI-like value
        price_change_pct = market_data.price_change_24h
        
        # Simple mapping: large negative changes -> low RSI, large positive -> high RSI
        if price_change_pct < -5:
            return 20  # Very oversold
        elif price_change_pct < -2:
            return 35  # Oversold
        elif price_change_pct > 5:
            return 80  # Very overbought
        elif price_change_pct > 2:
            return 65  # Overbought
        else:
            return 50  # Neutral
    
    def _analyze_volume(self, market_data: MarketData) -> float:
        """Analyze volume patterns"""
        # Simplified volume analysis
        if market_data.volume_ratio is not None:
            return market_data.volume_ratio
        
        # Fallback: assume normal volume
        return 1.0
    
    def get_risk_parameters(self) -> Dict[str, float]:
        """Get risk parameters specific to scalping"""
        return {
            'max_position_size': 0.02,  # 2% of capital per position
            'stop_loss_percentage': self.stop_loss_percentage,
            'max_daily_loss': 0.05,     # 5% maximum daily loss
            'max_concurrent_positions': 5,
            'min_profit_target': self.min_profit_threshold,
            'max_hold_time_minutes': self.max_hold_time.total_seconds() / 60
        }
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics"""
        return {
            'strategy_name': StrategyType.SCALPING.value,
            'signals_generated': self.signals_generated,
            'min_profit_threshold': self.min_profit_threshold,
            'max_profit_target': self.max_profit_target,
            'stop_loss_percentage': self.stop_loss_percentage,
            'max_hold_time_minutes': self.max_hold_time.total_seconds() / 60
        }
