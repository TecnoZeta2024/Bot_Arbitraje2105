"""
Day Trading Strategy Implementation
Multi-timeframe analysis with AI-enhanced decision making for intraday trades
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd

from ...domain.trading_signals.trading_signal import TradingSignal, SignalAction, RiskLevel, StrategyType
from ...domain.entities.market_data import MarketData, PriceData
from ...infrastructure.ai_analysis.gemini_analyzer import GeminiMarketAnalyzer, AIAnalysisResult
from .base_strategy import TradingStrategy


class TrendDirection(str, Enum):
    """Trend direction enumeration"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    UNCERTAIN = "UNCERTAIN"


class MarketRegime(str, Enum):
    """Market regime classification"""
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    LOW_VOLUME = "LOW_VOLUME"


class DayTradingStrategy(TradingStrategy):
    """
    Day Trading strategy with multi-timeframe analysis and AI validation
    
    Features:
    - Multi-timeframe trend analysis (5m, 15m, 1h)
    - Pattern recognition with AI confirmation
    - Dynamic profit targets (0.5% - 2%)
    - Risk/reward optimization
    - Market regime adaptation
    """
    
    def __init__(self, ai_analyzer: GeminiMarketAnalyzer):
        self.strategy_type = StrategyType.DAY_TRADING
        self.ai_analyzer = ai_analyzer
        self.logger = logging.getLogger("strategy.day_trading")
        
        # Day trading parameters
        self.timeframes = ['5m', '15m', '1h']
        self.profit_targets = {
            'conservative': Decimal('0.005'),  # 0.5%
            'moderate': Decimal('0.01'),       # 1.0%
            'aggressive': Decimal('0.02')      # 2.0%
        }
        self.stop_loss_percentage = Decimal('0.008')  # 0.8% stop loss
        self.risk_reward_ratio = Decimal('2.5')       # 1:2.5 risk/reward
        
        # Market condition requirements
        self.min_volume_24h = Decimal('500000')      # $500K minimum 24h volume
        self.min_trend_strength = 0.6                # Minimum trend strength
        self.max_spread_percentage = Decimal('0.1')  # 0.1% maximum spread
        
        # Technical indicator settings
        self.trend_timeframes = {
            '5m': {'sma_fast': 10, 'sma_slow': 20, 'rsi_period': 14},
            '15m': {'sma_fast': 20, 'sma_slow': 50, 'rsi_period': 14},
            '1h': {'sma_fast': 50, 'sma_slow': 100, 'rsi_period': 14}
        }
        
        # Pattern recognition settings
        self.support_resistance_lookback = 50
        self.breakout_confirmation_candles = 2
        self.volume_spike_threshold = 1.5  # 50% above average
        
        # AI validation settings
        self.min_ai_confidence = 0.7
        self.ai_pattern_weight = 0.3
        self.ai_sentiment_weight = 0.4
        self.technical_weight = 0.3
        
        # Performance tracking
        self.signals_generated = 0
        self.multi_timeframe_confirmations = 0
        self.ai_pattern_matches = 0
        
    async def analyze_market(self, market_data: Dict[str, MarketData]) -> List[TradingSignal]:
        """
        Analyze market using multi-timeframe approach with AI validation
        
        Process:
        1. Filter symbols by basic requirements
        2. Multi-timeframe trend analysis
        3. Pattern recognition and support/resistance
        4. AI sentiment and pattern confirmation
        5. Generate final signals with risk parameters
        """
        signals = []
        
        for symbol, data in market_data.items():
            try:
                # Pre-filter: Basic market requirements
                if not self._meets_day_trading_requirements(symbol, data):
                    continue
                
                # Multi-timeframe analysis
                timeframe_analysis = await self._analyze_multiple_timeframes(symbol, data)
                if not timeframe_analysis['is_actionable']:
                    continue
                
                # Pattern recognition and levels
                pattern_analysis = await self._analyze_patterns_and_levels(symbol, data)
                
                # Market regime classification
                market_regime = self._classify_market_regime(data, timeframe_analysis)
                
                # Generate preliminary signals
                preliminary_signals = await self._generate_preliminary_signals(
                    symbol, data, timeframe_analysis, pattern_analysis, market_regime
                )
                
                # AI validation and enhancement
                for prelim_signal in preliminary_signals:
                    ai_validation = await self._validate_and_enhance_with_ai(
                        prelim_signal, data, timeframe_analysis, pattern_analysis
                    )
                    
                    if ai_validation['approved']:
                        final_signal = await self._create_day_trading_signal(
                            prelim_signal, ai_validation, market_regime
                        )
                        signals.append(final_signal)
                        self.signals_generated += 1
                        
                        self.logger.info(f"Day trading signal: {symbol} {final_signal.action.value} - Confidence: {final_signal.confidence:.2f}")
                
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol} for day trading: {e}")
                continue
        
        # Sort by confidence and expected profit
        signals.sort(key=lambda s: (s.confidence * s.expected_profit), reverse=True)
        
        # Return top signals (limit concurrent day trades)
        return signals[:3]  # Maximum 3 day trading positions
    
    def _meets_day_trading_requirements(self, symbol: str, data: MarketData) -> bool:
        """Check if symbol meets day trading requirements"""
        
        # Volume requirement
        if data.volume_24h and data.volume_24h < self.min_volume_24h:
            return False
        
        # Liquidity requirement
        if not data.is_liquid:
            return False
        
        # Spread requirement
        if not data.has_tight_spread:
            return False
        
        # Sufficient price history
        if not data.price_history or len(data.price_history) < 100:
            return False
        
        return True
    
    async def _analyze_multiple_timeframes(self, symbol: str, data: MarketData) -> Dict[str, Any]:
        """
        Analyze multiple timeframes to determine overall trend and strength
        
        Returns analysis with trend direction, strength, and actionability
        """
        
        try:
            # Convert price history to DataFrame
            df = self._prepare_price_dataframe(data.price_history)
            
            timeframe_results = {}
            trend_consensus = []
            strength_scores = []
            
            for timeframe, params in self.trend_timeframes.items():
                # Resample data for timeframe (simplified - in production would use actual timeframe data)
                tf_data = self._resample_for_timeframe(df, timeframe)
                
                # Calculate trend indicators
                trend_analysis = self._analyze_trend_for_timeframe(tf_data, params)
                timeframe_results[timeframe] = trend_analysis
                
                trend_consensus.append(trend_analysis['direction'])
                strength_scores.append(trend_analysis['strength'])
            
            # Determine overall trend consensus
            overall_trend = self._determine_trend_consensus(trend_consensus)
            overall_strength = np.mean(strength_scores)
            
            # Check if actionable (strong trend consensus)
            is_actionable = (
                overall_strength >= self.min_trend_strength and
                trend_consensus.count(overall_trend) >= 2  # At least 2 timeframes agree
            )
            
            return {
                'timeframe_results': timeframe_results,
                'overall_trend': overall_trend,
                'overall_strength': overall_strength,
                'is_actionable': is_actionable,
                'trend_consensus_score': trend_consensus.count(overall_trend) / len(trend_consensus)
            }
            
        except Exception as e:
            self.logger.error(f"Multi-timeframe analysis failed for {symbol}: {e}")
            return {'is_actionable': False, 'overall_trend': TrendDirection.UNCERTAIN}
    
    def _analyze_trend_for_timeframe(self, df: pd.DataFrame, params: Dict[str, int]) -> Dict[str, Any]:
        """Analyze trend for specific timeframe"""
        
        if len(df) < max(params.values()) + 10:
            return {'direction': TrendDirection.UNCERTAIN, 'strength': 0.0}
        
        # Calculate SMAs
        sma_fast = df['close'].rolling(window=params['sma_fast']).mean()
        sma_slow = df['close'].rolling(window=params['sma_slow']).mean()
        
        # Calculate RSI
        rsi = self._calculate_rsi(df['close'], params['rsi_period'])
        
        # Determine trend direction
        current_fast = sma_fast.iloc[-1]
        current_slow = sma_slow.iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_fast > current_slow and current_price > current_fast:
            trend_direction = TrendDirection.BULLISH
        elif current_fast < current_slow and current_price < current_fast:
            trend_direction = TrendDirection.BEARISH
        else:
            trend_direction = TrendDirection.SIDEWAYS
        
        # Calculate trend strength
        sma_separation = abs(current_fast - current_slow) / current_price
        price_position = self._calculate_price_position_in_range(df['close'].tail(20))
        
        trend_strength = min(1.0, sma_separation * 100 + price_position * 0.5)
        
        return {
            'direction': trend_direction,
            'strength': trend_strength,
            'sma_fast': current_fast,
            'sma_slow': current_slow,
            'rsi': rsi.iloc[-1] if not rsi.empty else 50,
            'price_vs_sma_fast': (current_price - current_fast) / current_price,
            'sma_separation': sma_separation
        }
    
    async def _analyze_patterns_and_levels(self, symbol: str, data: MarketData) -> Dict[str, Any]:
        """
        Analyze chart patterns and support/resistance levels
        """
        
        try:
            df = self._prepare_price_dataframe(data.price_history)
            
            # Identify support and resistance levels
            support_levels = self._find_support_levels(df, self.support_resistance_lookback)
            resistance_levels = self._find_resistance_levels(df, self.support_resistance_lookback)
            
            # Check for breakout patterns
            breakout_analysis = self._analyze_breakout_patterns(df, support_levels, resistance_levels)
            
            # Volume analysis
            volume_analysis = self._analyze_volume_patterns(df)
            
            # Get AI pattern recognition
            ai_patterns = await self.ai_analyzer.detect_price_patterns(
                symbol, [Decimal(str(price)) for price in df['close'].tail(50).tolist()]
            )
            
            return {
                'support_levels': support_levels,
                'resistance_levels': resistance_levels,
                'breakout_analysis': breakout_analysis,
                'volume_analysis': volume_analysis,
                'ai_patterns': ai_patterns,
                'current_price': float(data.current_price)
            }
            
        except Exception as e:
            self.logger.error(f"Pattern analysis failed for {symbol}: {e}")
            return {'support_levels': [], 'resistance_levels': [], 'ai_patterns': {}}
    
    def _classify_market_regime(self, data: MarketData, timeframe_analysis: Dict[str, Any]) -> MarketRegime:
        """Classify current market regime"""
        
        # Check volatility
        volatility = data.volatility or Decimal('0.01')
        
        # Check volume
        volume_ratio = 1.0
        if data.volume_24h and data.price_24h_ago:
            # Simplified volume analysis
            avg_volume = float(data.volume_24h) / 24  # Rough hourly average
            volume_ratio = 1.0  # Would need current hour volume for accurate calculation
        
        # Check trend strength
        trend_strength = timeframe_analysis.get('overall_strength', 0.5)
        
        # Classify regime
        if volatility > Decimal('0.03'):  # High volatility
            return MarketRegime.VOLATILE
        elif trend_strength > 0.7:
            return MarketRegime.TRENDING
        elif volume_ratio < 0.7:
            return MarketRegime.LOW_VOLUME
        else:
            return MarketRegime.RANGING
    
    async def _generate_preliminary_signals(
        self, symbol: str, data: MarketData, timeframe_analysis: Dict[str, Any], 
        pattern_analysis: Dict[str, Any], market_regime: MarketRegime
    ) -> List[Dict[str, Any]]:
        """Generate preliminary trading signals"""
        
        signals = []
        current_price = float(data.current_price)
        
        overall_trend = timeframe_analysis['overall_trend']
        trend_strength = timeframe_analysis['overall_strength']
        
        # Generate signals based on market regime and trend
        
        if market_regime == MarketRegime.TRENDING and trend_strength > 0.7:
            # Trend following signals
            if overall_trend == TrendDirection.BULLISH:
                # Look for pullback entries
                signal = self._generate_pullback_buy_signal(
                    symbol, current_price, timeframe_analysis, pattern_analysis
                )
                if signal:
                    signals.append(signal)
            
            elif overall_trend == TrendDirection.BEARISH:
                # Look for pullback entries for short
                signal = self._generate_pullback_sell_signal(
                    symbol, current_price, timeframe_analysis, pattern_analysis
                )
                if signal:
                    signals.append(signal)
        
        elif market_regime == MarketRegime.RANGING:
            # Range trading signals
            range_signals = self._generate_range_trading_signals(
                symbol, current_price, pattern_analysis
            )
            signals.extend(range_signals)
        
        elif market_regime == MarketRegime.VOLATILE:
            # Breakout signals only in volatile markets
            breakout_signals = self._generate_breakout_signals(
                symbol, current_price, pattern_analysis, timeframe_analysis
            )
            signals.extend(breakout_signals)
        
        return signals
    
    def _generate_pullback_buy_signal(self, symbol: str, current_price: float, 
                                    timeframe_analysis: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate buy signal on pullback in uptrend"""
        
        # Check if price is near support in uptrend
        support_levels = pattern_analysis.get('support_levels', [])
        
        for support in support_levels:
            distance_to_support = abs(current_price - support) / current_price
            
            if distance_to_support < 0.005:  # Within 0.5% of support
                # Check if RSI is oversold on lower timeframe
                tf_5m = timeframe_analysis['timeframe_results'].get('5m', {})
                rsi_5m = tf_5m.get('rsi', 50)
                
                if rsi_5m < 40:  # Oversold condition
                    return {
                        'symbol': symbol,
                        'action': SignalAction.BUY,
                        'entry_price': current_price,
                        'signal_type': 'pullback_buy',
                        'confidence': 0.75,
                        'reasoning': f"Pullback to support at {support:.6f}, RSI oversold: {rsi_5m:.1f}",
                        'support_level': support,
                        'profit_target': 'moderate'
                    }
        
        return None
    
    def _generate_pullback_sell_signal(self, symbol: str, current_price: float,
                                     timeframe_analysis: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate sell signal on pullback in downtrend"""
        
        resistance_levels = pattern_analysis.get('resistance_levels', [])
        
        for resistance in resistance_levels:
            distance_to_resistance = abs(current_price - resistance) / current_price
            
            if distance_to_resistance < 0.005:  # Within 0.5% of resistance
                tf_5m = timeframe_analysis['timeframe_results'].get('5m', {})
                rsi_5m = tf_5m.get('rsi', 50)
                
                if rsi_5m > 60:  # Overbought condition
                    return {
                        'symbol': symbol,
                        'action': SignalAction.SELL,
                        'entry_price': current_price,
                        'signal_type': 'pullback_sell',
                        'confidence': 0.75,
                        'reasoning': f"Pullback to resistance at {resistance:.6f}, RSI overbought: {rsi_5m:.1f}",
                        'resistance_level': resistance,
                        'profit_target': 'moderate'
                    }
        
        return None
    
    def _generate_breakout_signals(self, symbol: str, current_price: float,
                                 pattern_analysis: Dict[str, Any], timeframe_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate breakout signals"""
        
        signals = []
        breakout_analysis = pattern_analysis.get('breakout_analysis', {})
        
        if breakout_analysis.get('bullish_breakout'):
            signals.append({
                'symbol': symbol,
                'action': SignalAction.BUY,
                'entry_price': current_price,
                'signal_type': 'bullish_breakout',
                'confidence': 0.8,
                'reasoning': "Bullish breakout detected",
                'profit_target': 'aggressive'
            })
        
        if breakout_analysis.get('bearish_breakout'):
            signals.append({
                'symbol': symbol,
                'action': SignalAction.SELL,
                'entry_price': current_price,
                'signal_type': 'bearish_breakout',
                'confidence': 0.8,
                'reasoning': "Bearish breakout detected",
                'profit_target': 'aggressive'
            })
        
        return signals
    
    async def _validate_and_enhance_with_ai(self, signal: Dict[str, Any], data: MarketData,
                                          timeframe_analysis: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance signal with AI analysis"""
        
        try:
            # Get AI analysis
            ai_analysis = await self.ai_analyzer.analyze_market_sentiment(signal['symbol'], data)
            
            # Check AI validation criteria
            ai_agrees = (
                ai_analysis.recommended_action in [signal['action'].value, 'HOLD'] and
                ai_analysis.confidence_level >= self.min_ai_confidence
            )
            
            # Calculate combined confidence
            technical_confidence = signal['confidence'] * self.technical_weight
            ai_confidence = ai_analysis.confidence_level * self.ai_sentiment_weight
            
            # Check pattern confirmation
            ai_patterns = pattern_analysis.get('ai_patterns', {})
            pattern_confidence = 0.0
            
            if ai_patterns.get('patterns_detected'):
                pattern_reliability = ai_patterns.get('pattern_reliability', 0.5)
                pattern_confidence = pattern_reliability * self.ai_pattern_weight
                self.ai_pattern_matches += 1
            
            final_confidence = min(1.0, technical_confidence + ai_confidence + pattern_confidence)
            
            # Enhanced reasoning
            enhanced_reasoning = signal['reasoning'] + f" | AI: {ai_analysis.reasoning[:100]}"
            
            # Risk assessment
            risk_level = RiskLevel.MEDIUM
            if ai_analysis.risk_assessment == 'LOW' and final_confidence > 0.8:
                risk_level = RiskLevel.LOW
            elif ai_analysis.risk_assessment == 'HIGH' or final_confidence < 0.6:
                risk_level = RiskLevel.HIGH
            
            approval = (
                ai_agrees and
                final_confidence >= 0.6 and
                ai_analysis.risk_assessment != 'HIGH'
            )
            
            if approval:
                self.multi_timeframe_confirmations += 1
            
            return {
                'approved': approval,
                'final_confidence': final_confidence,
                'ai_analysis': ai_analysis,
                'enhanced_reasoning': enhanced_reasoning,
                'risk_level': risk_level,
                'ai_patterns': ai_patterns
            }
            
        except Exception as e:
            self.logger.error(f"AI validation failed: {e}")
            return {
                'approved': signal['confidence'] > 0.7,
                'final_confidence': signal['confidence'] * 0.8,
                'enhanced_reasoning': signal['reasoning'] + " | AI validation failed",
                'risk_level': RiskLevel.MEDIUM
            }
    
    async def _create_day_trading_signal(self, preliminary_signal: Dict[str, Any],
                                       ai_validation: Dict[str, Any], market_regime: MarketRegime) -> TradingSignal:
        """Create final day trading signal"""
        
        signal_id = f"daytrading_{preliminary_signal['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Determine profit target based on signal type and market regime
        profit_target_type = preliminary_signal.get('profit_target', 'moderate')
        profit_target = self.profit_targets[profit_target_type]
        
        # Adjust for market regime
        if market_regime == MarketRegime.VOLATILE:
            profit_target *= Decimal('1.5')  # Higher targets in volatile markets
        elif market_regime == MarketRegime.RANGING:
            profit_target *= Decimal('0.8')  # Lower targets in ranging markets
        
        # Calculate stop loss and take profit
        entry_price = preliminary_signal['entry_price']
        stop_loss_distance = float(self.stop_loss_percentage)
        profit_distance = float(profit_target)
        
        if preliminary_signal['action'] == SignalAction.BUY:
            stop_loss = entry_price * (1 - stop_loss_distance)
            take_profit = entry_price * (1 + profit_distance)
        else:  # SELL
            stop_loss = entry_price * (1 + stop_loss_distance)
            take_profit = entry_price * (1 - profit_distance)
        
        return TradingSignal(
            signal_id=signal_id,
            timestamp=datetime.now(),
            strategy_name=self.strategy_type,
            symbol=preliminary_signal['symbol'],
            action=preliminary_signal['action'],
            confidence=ai_validation['final_confidence'],
            expected_profit=float(profit_target),
            risk_level=ai_validation['risk_level'],
            timeframe="15m",
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            ai_analysis={
                'ai_sentiment': ai_validation['ai_analysis'].sentiment_score if 'ai_analysis' in ai_validation else None,
                'ai_confidence': ai_validation['ai_analysis'].confidence_level if 'ai_analysis' in ai_validation else None,
                'ai_reasoning': ai_validation['enhanced_reasoning'],
                'signal_type': preliminary_signal['signal_type'],
                'market_regime': market_regime.value,
                'ai_patterns': ai_validation.get('ai_patterns', {})
            },
            market_conditions={
                'market_regime': market_regime.value,
                'profit_target_type': profit_target_type,
                'signal_type': preliminary_signal['signal_type']
            }
        )
    
    def get_risk_parameters(self) -> Dict[str, float]:
        """Get day trading risk parameters"""
        return {
            'max_position_size': 0.15,  # 15% of capital per position
            'stop_loss_percentage': float(self.stop_loss_percentage),
            'max_daily_loss': 0.08,     # 8% maximum daily loss
            'max_concurrent_positions': 3,
            'min_profit_target': float(self.profit_targets['conservative']),
            'max_profit_target': float(self.profit_targets['aggressive']),
            'risk_reward_ratio': float(self.risk_reward_ratio),
            'max_hold_time_hours': 8    # Close all positions before market close
        }
    
    # Helper methods for technical analysis
    
    def _prepare_price_dataframe(self, price_history: List[PriceData]) -> pd.DataFrame:
        """Convert price history to pandas DataFrame"""
        return pd.DataFrame([
            {
                'timestamp': p.timestamp,
                'open': float(p.open),
                'high': float(p.high),
                'low': float(p.low),
                'close': float(p.close),
                'volume': float(p.volume)
            }
            for p in price_history
        ])
    
    def _resample_for_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample data for specific timeframe (simplified implementation)"""
        # In production, would properly resample based on timeframe
        # For now, return the data as-is
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _determine_trend_consensus(self, trends: List[TrendDirection]) -> TrendDirection:
        """Determine consensus from multiple timeframe trends"""
        trend_counts = {trend: trends.count(trend) for trend in set(trends)}
        return max(trend_counts, key=trend_counts.get)
    
    def _calculate_price_position_in_range(self, prices: pd.Series) -> float:
        """Calculate where current price sits in recent range (0-1)"""
        high = prices.max()
        low = prices.min()
        current = prices.iloc[-1]
        
        if high == low:
            return 0.5
        
        return (current - low) / (high - low)
    
    def _find_support_levels(self, df: pd.DataFrame, lookback: int) -> List[float]:
        """Find support levels using pivot lows"""
        lows = df['low'].rolling(window=5, center=True).min()
        support_levels = []
        
        for i in range(2, len(lows) - 2):
            if (lows.iloc[i] == df['low'].iloc[i] and
                lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]):
                support_levels.append(lows.iloc[i])
        
        return sorted(support_levels[-5:])  # Return last 5 support levels
    
    def _find_resistance_levels(self, df: pd.DataFrame, lookback: int) -> List[float]:
        """Find resistance levels using pivot highs"""
        highs = df['high'].rolling(window=5, center=True).max()
        resistance_levels = []
        
        for i in range(2, len(highs) - 2):
            if (highs.iloc[i] == df['high'].iloc[i] and
                highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]):
                resistance_levels.append(highs.iloc[i])
        
        return sorted(resistance_levels[-5:])  # Return last 5 resistance levels
    
    def _analyze_breakout_patterns(self, df: pd.DataFrame, support_levels: List[float], 
                                 resistance_levels: List[float]) -> Dict[str, bool]:
        """Analyze for breakout patterns"""
        current_price = df['close'].iloc[-1]
        volume_spike = self._detect_volume_spike(df)
        
        bullish_breakout = False
        bearish_breakout = False
        
        # Check for bullish breakout above resistance
        for resistance in resistance_levels:
            if (current_price > resistance * 1.002 and  # 0.2% above resistance
                volume_spike):
                bullish_breakout = True
                break
        
        # Check for bearish breakout below support
        for support in support_levels:
            if (current_price < support * 0.998 and  # 0.2% below support
                volume_spike):
                bearish_breakout = True
                break
        
        return {
            'bullish_breakout': bullish_breakout,
            'bearish_breakout': bearish_breakout,
            'volume_spike': volume_spike
        }
    
    def _detect_volume_spike(self, df: pd.DataFrame) -> bool:
        """Detect volume spike"""
        if len(df) < 20:
            return False
        
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(20).mean()
        
        return current_volume > avg_volume * self.volume_spike_threshold
    
    def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns"""
        if len(df) < 20:
            return {'volume_trend': 'insufficient_data'}
        
        volume_sma = df['volume'].rolling(window=20).mean()
        current_volume = df['volume'].iloc[-1]
        avg_volume = volume_sma.iloc[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        return {
            'volume_ratio': volume_ratio,
            'volume_trend': 'increasing' if volume_ratio > 1.2 else 'normal',
            'avg_volume': avg_volume,
            'current_volume': current_volume
        }
    
    def _generate_range_trading_signals(self, symbol: str, current_price: float,
                                      pattern_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate signals for range-bound markets"""
        signals = []
        
        support_levels = pattern_analysis.get('support_levels', [])
        resistance_levels = pattern_analysis.get('resistance_levels', [])
        
        # Buy near support
        for support in support_levels:
            if abs(current_price - support) / current_price < 0.01:  # Within 1% of support
                signals.append({
                    'symbol': symbol,
                    'action': SignalAction.BUY,
                    'entry_price': current_price,
                    'signal_type': 'range_support_buy',
                    'confidence': 0.65,
                    'reasoning': f"Range trading: buy near support at {support:.6f}",
                    'profit_target': 'conservative'
                })
        
        # Sell near resistance
        for resistance in resistance_levels:
            if abs(current_price - resistance) / current_price < 0.01:  # Within 1% of resistance
                signals.append({
                    'symbol': symbol,
                    'action': SignalAction.SELL,
                    'entry_price': current_price,
                    'signal_type': 'range_resistance_sell',
                    'confidence': 0.65,
                    'reasoning': f"Range trading: sell near resistance at {resistance:.6f}",
                    'profit_target': 'conservative'
                })
        
        return signals
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics"""
        return {
            'strategy_name': self.strategy_type.value,
            'signals_generated': self.signals_generated,
            'multi_timeframe_confirmations': self.multi_timeframe_confirmations,
            'ai_pattern_matches': self.ai_pattern_matches,
            'confirmation_rate': self.multi_timeframe_confirmations / max(self.signals_generated, 1),
            'pattern_match_rate': self.ai_pattern_matches / max(self.signals_generated, 1),
            'profit_targets': {k: float(v) for k, v in self.profit_targets.items()},
            'risk_reward_ratio': float(self.risk_reward_ratio)
        }
