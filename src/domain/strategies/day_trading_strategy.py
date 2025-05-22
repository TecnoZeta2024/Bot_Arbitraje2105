"""
Day Trading Strategy Implementation
Multi-timeframe analysis for intraday trades
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from domain.trading_signals.trading_signal import TradingSignal, SignalAction, RiskLevel, StrategyType
from domain.entities.market_data import MarketData
from .base_strategy import BaseStrategy


class TrendDirection(Enum):
    """Trend direction enumeration"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    UNCERTAIN = "UNCERTAIN"


class MarketRegime(Enum):
    """Market regime classification"""
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    LOW_VOLUME = "LOW_VOLUME"


class DayTradingStrategy(BaseStrategy):
    """
    Day Trading strategy with trend analysis and pattern recognition
    
    Features:
    - Trend analysis
    - Dynamic profit targets (0.5% - 2%)
    - Risk/reward optimization
    - Market regime adaptation
    """
    
    def __init__(self):
        self.logger = logging.getLogger("DayTradingStrategy")
        
        # Day trading parameters
        self.profit_targets = {
            'conservative': 0.005,  # 0.5%
            'moderate': 0.01,       # 1.0%
            'aggressive': 0.02      # 2.0%
        }
        self.stop_loss_percentage = 0.008  # 0.8% stop loss
        self.risk_reward_ratio = 2.5       # 1:2.5 risk/reward
        
        # Market condition requirements
        self.min_volume_threshold = 500000      # $500K minimum 24h volume
        self.min_trend_strength = 0.6           # Minimum trend strength
        self.max_spread_percentage = 0.1        # 0.1% maximum spread
        
        # Signal generation settings
        self.min_price_change_threshold = 1.0   # Minimum 1% price change for signal
        self.volume_spike_threshold = 1.5       # 50% above average volume
        
        # Performance tracking
        self.signals_generated = 0
        self.last_signal_time = None
        
        self.logger.info("DayTradingStrategy initialized")
    
    async def analyze(self, market_data: MarketData) -> Optional[TradingSignal]:
        """
        Analyze market data and generate day trading signals
        
        Args:
            market_data: Market data for analysis
            
        Returns:
            Trading signal or None if no signal generated
        """
        try:
            # Pre-filter: Check basic requirements
            if not self._meets_day_trading_requirements(market_data):
                return None
            
            # Prevent overtrading - minimum 5 minutes between signals
            if self.last_signal_time and (datetime.now() - self.last_signal_time).total_seconds() < 300:
                return None
            
            # Analyze trend and market regime
            trend_analysis = self._analyze_trend(market_data)
            market_regime = self._classify_market_regime(market_data, trend_analysis)
            
            # Generate signal based on analysis
            signal = await self._generate_day_trading_signal(market_data, trend_analysis, market_regime)
            
            if signal:
                self.signals_generated += 1
                self.last_signal_time = datetime.now()
                self.logger.info(f"Day trading signal generated for {market_data.symbol}: {signal.action.value}")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing {market_data.symbol} for day trading: {e}")
            return None
    
    def _meets_day_trading_requirements(self, market_data: MarketData) -> bool:
        """Check if market data meets day trading requirements"""
        
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
        
        # Price movement requirement
        if (market_data.price_change_24h is not None and 
            abs(market_data.price_change_24h) < self.min_price_change_threshold):
            return False
        
        return True
    
    def _analyze_trend(self, market_data: MarketData) -> Dict[str, Any]:
        """Analyze market trend"""
        
        # Simple trend analysis based on price change
        price_change = market_data.price_change_24h or 0.0
        
        # Determine trend direction
        if price_change > 2.0:
            trend_direction = TrendDirection.BULLISH
            trend_strength = min(1.0, abs(price_change) / 10.0)  # Normalize to 0-1
        elif price_change < -2.0:
            trend_direction = TrendDirection.BEARISH
            trend_strength = min(1.0, abs(price_change) / 10.0)
        elif abs(price_change) > 0.5:
            trend_direction = TrendDirection.SIDEWAYS
            trend_strength = 0.5
        else:
            trend_direction = TrendDirection.UNCERTAIN
            trend_strength = 0.3
        
        return {
            'direction': trend_direction,
            'strength': trend_strength,
            'price_change_24h': price_change
        }
    
    def _classify_market_regime(self, market_data: MarketData, trend_analysis: Dict[str, Any]) -> MarketRegime:
        """Classify current market regime"""
        
        # Check price volatility (simplified)
        price_change = abs(trend_analysis['price_change_24h'])
        trend_strength = trend_analysis['strength']
        
        # Volume analysis
        volume_ratio = market_data.volume_ratio or 1.0
        
        # Classify regime
        if price_change > 5.0:  # High volatility
            return MarketRegime.VOLATILE
        elif trend_strength > 0.7:
            return MarketRegime.TRENDING
        elif volume_ratio < 0.7:
            return MarketRegime.LOW_VOLUME
        else:
            return MarketRegime.RANGING
    
    async def _generate_day_trading_signal(
        self, market_data: MarketData, trend_analysis: Dict[str, Any], market_regime: MarketRegime
    ) -> Optional[TradingSignal]:
        """Generate day trading signal based on analysis"""
        
        current_price = market_data.price
        trend_direction = trend_analysis['direction']
        trend_strength = trend_analysis['strength']
        volume_ratio = market_data.volume_ratio or 1.0
        
        action = None
        confidence = 0.0
        reasoning = []
        profit_target_type = 'moderate'
        
        # Signal generation logic based on market regime
        
        if market_regime == MarketRegime.TRENDING and trend_strength > self.min_trend_strength:
            # Trend following signals
            if trend_direction == TrendDirection.BULLISH:
                action = SignalAction.BUY
                confidence = 0.7 + (trend_strength * 0.2)
                reasoning.append(f"Strong bullish trend (strength: {trend_strength:.2f})")
                profit_target_type = 'moderate'
                
                # Volume confirmation
                if volume_ratio > 1.2:
                    confidence += 0.1
                    reasoning.append("Volume confirmation")
            
            elif trend_direction == TrendDirection.BEARISH:
                action = SignalAction.SELL
                confidence = 0.7 + (trend_strength * 0.2)
                reasoning.append(f"Strong bearish trend (strength: {trend_strength:.2f})")
                profit_target_type = 'moderate'
                
                # Volume confirmation
                if volume_ratio > 1.2:
                    confidence += 0.1
                    reasoning.append("Volume confirmation")
        
        elif market_regime == MarketRegime.VOLATILE:
            # Breakout signals in volatile markets
            price_change = trend_analysis['price_change_24h']
            
            if abs(price_change) > 3.0 and volume_ratio > self.volume_spike_threshold:
                if price_change > 0:
                    action = SignalAction.BUY
                    reasoning.append("Volatile breakout to upside")
                else:
                    action = SignalAction.SELL
                    reasoning.append("Volatile breakout to downside")
                
                confidence = 0.8
                profit_target_type = 'aggressive'
        
        elif market_regime == MarketRegime.RANGING:
            # Mean reversion signals in ranging markets
            price_change = trend_analysis['price_change_24h']
            
            if abs(price_change) > 1.0 and abs(price_change) < 3.0:
                # Contrarian signals in ranging market
                if price_change > 0:
                    action = SignalAction.SELL  # Sell strength in range
                    reasoning.append("Mean reversion: sell strength in range")
                else:
                    action = SignalAction.BUY   # Buy weakness in range
                    reasoning.append("Mean reversion: buy weakness in range")
                
                confidence = 0.6
                profit_target_type = 'conservative'
        
        # Generate signal if criteria met
        if action and confidence >= 0.6:
            
            # Calculate profit target and stop loss
            profit_target = self.profit_targets[profit_target_type]
            
            stop_loss_price = None
            take_profit_price = None
            
            if action == SignalAction.BUY:
                stop_loss_price = current_price * (1 - self.stop_loss_percentage)
                take_profit_price = current_price * (1 + profit_target)
            else:  # SELL
                stop_loss_price = current_price * (1 + self.stop_loss_percentage)
                take_profit_price = current_price * (1 - profit_target)
            
            signal_id = f"daytrading_{market_data.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            return TradingSignal(
                signal_id=signal_id,
                timestamp=datetime.now(),
                strategy_name=StrategyType.DAY_TRADING,
                symbol=market_data.symbol,
                action=action,
                confidence=min(confidence, 1.0),
                expected_profit=profit_target * 100,  # Convert to percentage
                risk_level=RiskLevel.MEDIUM,
                timeframe="15m",
                entry_price=current_price,
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                ai_analysis={
                    'reasoning': reasoning,
                    'trend_direction': trend_direction.value,
                    'trend_strength': trend_strength,
                    'market_regime': market_regime.value,
                    'volume_ratio': volume_ratio,
                    'profit_target_type': profit_target_type,
                    'confidence': confidence
                }
            )
        
        return None
    
    def get_risk_parameters(self) -> Dict[str, float]:
        """Get day trading risk parameters"""
        return {
            'max_position_size': 0.15,  # 15% of capital per position
            'stop_loss_percentage': self.stop_loss_percentage,
            'max_daily_loss': 0.08,     # 8% maximum daily loss
            'max_concurrent_positions': 3,
            'min_profit_target': self.profit_targets['conservative'],
            'max_profit_target': self.profit_targets['aggressive'],
            'risk_reward_ratio': self.risk_reward_ratio,
            'max_hold_time_hours': 8    # Close all positions before market close
        }
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics"""
        return {
            'strategy_name': StrategyType.DAY_TRADING.value,
            'signals_generated': self.signals_generated,
            'profit_targets': self.profit_targets,
            'risk_reward_ratio': self.risk_reward_ratio,
            'min_trend_strength': self.min_trend_strength,
            'volume_spike_threshold': self.volume_spike_threshold
        }
