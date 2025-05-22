"""
Scalping Strategy Implementation
High-frequency trading strategy for small, quick profits
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd

from ...domain.trading_signals.trading_signal import TradingSignal, SignalAction, RiskLevel, StrategyType
from ...domain.entities.market_data import MarketData
from ...infrastructure.ai_analysis.gemini_analyzer import GeminiMarketAnalyzer, AIAnalysisResult
from .base_strategy import TradingStrategy


class ScalpingStrategy(TradingStrategy):
    """
    Scalping strategy for capturing small price movements (0.01%-0.1%)
    
    Characteristics:
    - Very short holding periods (5 seconds - 5 minutes)
    - High frequency (50-200 trades per day)
    - Small profit targets with tight stop losses
    - AI-enhanced signal validation
    """
    
    def __init__(self, ai_analyzer: GeminiMarketAnalyzer):
        self.strategy_type = StrategyType.SCALPING
        self.ai_analyzer = ai_analyzer
        self.logger = logging.getLogger("strategy.scalping")
        
        # Scalping parameters
        self.min_profit_threshold = Decimal('0.0001')  # 0.01% minimum profit
        self.max_profit_target = Decimal('0.001')      # 0.1% maximum profit target
        self.stop_loss_percentage = Decimal('0.0005')  # 0.05% stop loss
        self.max_hold_time = timedelta(minutes=5)      # Maximum 5 minutes hold
        
        # Market condition requirements
        self.min_volume_24h = Decimal('1000000')       # $1M minimum 24h volume
        self.max_spread_percentage = Decimal('0.05')   # 0.05% maximum spread
        self.min_liquidity_score = Decimal('500')      # Minimum liquidity
        
        # Technical indicator settings
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2
        
        # AI validation settings
        self.min_ai_confidence = 0.65              # Minimum AI confidence for signals
        self.ai_sentiment_threshold = 60           # Sentiment score threshold
        
        # Performance tracking
        self.signals_generated = 0
        self.ai_validations_passed = 0
        
    async def analyze_market(self, market_data: Dict[str, MarketData]) -> List[TradingSignal]:
        """
        Analyze market data and generate scalping signals
        
        Returns:
            List of high-confidence scalping signals
        """
        signals = []
        
        for symbol, data in market_data.items():
            try:
                # Pre-filter: Check basic market conditions
                if not self._meets_basic_requirements(symbol, data):
                    continue
                
                # Calculate technical indicators
                technical_analysis = await self._calculate_technical_indicators(symbol, data)
                
                if not technical_analysis:
                    continue
                
                # Generate preliminary signal based on technical analysis
                preliminary_signal = await self._generate_technical_signal(symbol, data, technical_analysis)
                
                if not preliminary_signal:
                    continue
                
                # Validate signal with AI
                ai_validation = await self._validate_with_ai(preliminary_signal, data, technical_analysis)
                
                if ai_validation['is_valid']:
                    # Create final signal with AI insights
                    final_signal = await self._create_final_signal(
                        preliminary_signal, 
                        ai_validation, 
                        technical_analysis
                    )
                    
                    signals.append(final_signal)
                    self.signals_generated += 1
                    self.ai_validations_passed += 1
                    
                    self.logger.info(f"Scalping signal generated for {symbol}: {final_signal.action.value}")
                
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol} for scalping: {e}")
                continue
        
        # Sort signals by confidence and expected profit
        signals.sort(key=lambda s: (s.confidence, s.expected_profit), reverse=True)
        
        # Return top signals (limit to prevent overtrading)
        return signals[:5]  # Maximum 5 simultaneous scalping positions
    
    def _meets_basic_requirements(self, symbol: str, data: MarketData) -> bool:
        """Check if symbol meets basic scalping requirements"""
        
        # Volume requirement
        if data.volume_24h and data.volume_24h < self.min_volume_24h:
            return False
        
        # Liquidity requirement
        if not data.is_liquid:
            return False
        
        # Spread requirement
        if not data.has_tight_spread:
            return False
        
        # Order book depth requirement
        if data.order_book and data.order_book.liquidity_score < self.min_liquidity_score:
            return False
        
        return True
    
    async def _calculate_technical_indicators(self, symbol: str, data: MarketData) -> Optional[Dict[str, Any]]:
        """Calculate technical indicators for scalping analysis"""
        
        if not data.price_history or len(data.price_history) < 50:
            self.logger.warning(f"Insufficient price history for {symbol}")
            return None
        
        try:
            # Convert price history to pandas DataFrame
            prices_df = pd.DataFrame([
                {
                    'timestamp': p.timestamp,
                    'open': float(p.open),
                    'high': float(p.high),
                    'low': float(p.low),
                    'close': float(p.close),
                    'volume': float(p.volume)
                }
                for p in data.price_history[-100:]  # Last 100 data points
            ])
            
            if prices_df.empty:
                return None
            
            # Calculate RSI
            rsi = self._calculate_rsi(prices_df['close'], self.rsi_period)
            
            # Calculate MACD
            macd_line, macd_signal, macd_histogram = self._calculate_macd(
                prices_df['close'], self.macd_fast, self.macd_slow, self.macd_signal
            )
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                prices_df['close'], self.bb_period, self.bb_std
            )
            
            # Calculate volume analysis
            volume_sma = prices_df['volume'].rolling(window=20).mean()
            volume_ratio = prices_df['volume'].iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1
            
            # Calculate price momentum
            price_momentum = self._calculate_momentum(prices_df['close'], period=5)
            
            return {
                'rsi': rsi.iloc[-1] if not rsi.empty else 50,
                'rsi_previous': rsi.iloc[-2] if len(rsi) > 1 else 50,
                'macd_line': macd_line.iloc[-1] if not macd_line.empty else 0,
                'macd_signal': macd_signal.iloc[-1] if not macd_signal.empty else 0,
                'macd_histogram': macd_histogram.iloc[-1] if not macd_histogram.empty else 0,
                'bb_upper': bb_upper.iloc[-1] if not bb_upper.empty else float(data.current_price),
                'bb_middle': bb_middle.iloc[-1] if not bb_middle.empty else float(data.current_price),
                'bb_lower': bb_lower.iloc[-1] if not bb_lower.empty else float(data.current_price),
                'volume_ratio': volume_ratio,
                'price_momentum': price_momentum.iloc[-1] if not price_momentum.empty else 0,
                'current_price': float(data.current_price),
                'price_position_in_bb': self._get_bb_position(float(data.current_price), bb_upper.iloc[-1], bb_lower.iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return None
    
    async def _generate_technical_signal(self, symbol: str, data: MarketData, tech_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate preliminary signal based on technical analysis"""
        
        current_price = tech_analysis['current_price']
        rsi = tech_analysis['rsi']
        rsi_prev = tech_analysis['rsi_previous']
        macd_line = tech_analysis['macd_line']
        macd_signal = tech_analysis['macd_signal']
        macd_histogram = tech_analysis['macd_histogram']
        bb_position = tech_analysis['price_position_in_bb']
        volume_ratio = tech_analysis['volume_ratio']
        momentum = tech_analysis['price_momentum']
        
        signal = None
        action = None
        confidence = 0.0
        reasoning = []
        
        # Scalping Signal Logic
        
        # BUY Conditions
        buy_conditions = []
        
        # RSI oversold bounce
        if rsi < self.rsi_oversold and rsi > rsi_prev:
            buy_conditions.append("RSI oversold bounce")
            confidence += 0.2
        
        # MACD bullish signal
        if macd_line > macd_signal and macd_histogram > 0:
            buy_conditions.append("MACD bullish")
            confidence += 0.15
        
        # Price near lower Bollinger Band
        if bb_position < 0.2:  # In lower 20% of BB range
            buy_conditions.append("Price near BB lower band")
            confidence += 0.15
        
        # Volume confirmation
        if volume_ratio > 1.2:  # 20% above average volume
            buy_conditions.append("Volume confirmation")
            confidence += 0.1
        
        # Positive momentum
        if momentum > 0:
            buy_conditions.append("Positive momentum")
            confidence += 0.1
        
        # SELL Conditions
        sell_conditions = []
        
        # RSI overbought decline
        if rsi > self.rsi_overbought and rsi < rsi_prev:
            sell_conditions.append("RSI overbought decline")
            confidence += 0.2
        
        # MACD bearish signal
        if macd_line < macd_signal and macd_histogram < 0:
            sell_conditions.append("MACD bearish")
            confidence += 0.15
        
        # Price near upper Bollinger Band
        if bb_position > 0.8:  # In upper 20% of BB range
            sell_conditions.append("Price near BB upper band")
            confidence += 0.15
        
        # Volume confirmation for sell
        if volume_ratio > 1.2:
            sell_conditions.append("Volume confirmation")
            confidence += 0.1
        
        # Negative momentum
        if momentum < 0:
            sell_conditions.append("Negative momentum")
            confidence += 0.1
        
        # Determine signal
        min_conditions = 2  # Minimum conditions for signal
        
        if len(buy_conditions) >= min_conditions and len(sell_conditions) < min_conditions:
            action = SignalAction.BUY
            reasoning = buy_conditions
        elif len(sell_conditions) >= min_conditions and len(buy_conditions) < min_conditions:
            action = SignalAction.SELL
            reasoning = sell_conditions
        
        if action and confidence >= 0.4:  # Minimum technical confidence
            # Calculate profit target and stop loss
            profit_target = min(
                self.max_profit_target,
                max(self.min_profit_threshold, Decimal(str(abs(momentum) * 0.1)))
            )
            
            return {
                'symbol': symbol,
                'action': action,
                'confidence': min(confidence, 1.0),
                'profit_target': float(profit_target),
                'stop_loss': float(self.stop_loss_percentage),
                'reasoning': reasoning,
                'technical_analysis': tech_analysis,
                'entry_price': current_price
            }
        
        return None
    
    async def _validate_with_ai(self, signal: Dict[str, Any], data: MarketData, tech_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate signal using AI analysis"""
        
        try:
            # Get AI market sentiment analysis
            ai_analysis = await self.ai_analyzer.analyze_market_sentiment(signal['symbol'], data)
            
            # Check AI validation criteria
            is_valid = (
                ai_analysis.confidence_level >= self.min_ai_confidence / 100 and
                ai_analysis.sentiment_score >= self.ai_sentiment_threshold and
                ai_analysis.recommended_action in [signal['action'].value, 'HOLD'] and
                ai_analysis.risk_assessment in ['LOW', 'MEDIUM']
            )
            
            # Adjust confidence based on AI analysis
            ai_confidence_boost = ai_analysis.confidence_level * 0.3  # Up to 30% boost
            final_confidence = min(signal['confidence'] + ai_confidence_boost, 1.0)
            
            return {
                'is_valid': is_valid,
                'ai_analysis': ai_analysis,
                'final_confidence': final_confidence,
                'ai_reasoning': ai_analysis.reasoning,
                'risk_assessment': ai_analysis.risk_assessment
            }
            
        except Exception as e:
            self.logger.error(f"AI validation failed for {signal['symbol']}: {e}")
            # Fallback: accept signal with reduced confidence
            return {
                'is_valid': signal['confidence'] >= 0.6,  # Higher threshold without AI
                'ai_analysis': None,
                'final_confidence': signal['confidence'] * 0.8,  # Reduce confidence
                'ai_reasoning': f"AI validation failed: {e}",
                'risk_assessment': 'MEDIUM'
            }
    
    async def _create_final_signal(self, preliminary_signal: Dict[str, Any], ai_validation: Dict[str, Any], tech_analysis: Dict[str, Any]) -> TradingSignal:
        """Create final trading signal with all validations"""
        
        signal_id = f"scalping_{preliminary_signal['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Combine technical and AI reasoning
        combined_reasoning = preliminary_signal['reasoning'] + [ai_validation['ai_reasoning']]
        
        return TradingSignal(
            signal_id=signal_id,
            timestamp=datetime.now(),
            strategy_name=self.strategy_type,
            symbol=preliminary_signal['symbol'],
            action=preliminary_signal['action'],
            confidence=ai_validation['final_confidence'],
            expected_profit=preliminary_signal['profit_target'],
            risk_level=RiskLevel.LOW if ai_validation['risk_assessment'] == 'LOW' else RiskLevel.MEDIUM,
            timeframe="1m",
            entry_price=preliminary_signal['entry_price'],
            stop_loss=preliminary_signal['entry_price'] * (1 - preliminary_signal['stop_loss']) if preliminary_signal['action'] == SignalAction.BUY else preliminary_signal['entry_price'] * (1 + preliminary_signal['stop_loss']),
            take_profit=preliminary_signal['entry_price'] * (1 + preliminary_signal['profit_target']) if preliminary_signal['action'] == SignalAction.BUY else preliminary_signal['entry_price'] * (1 - preliminary_signal['profit_target']),
            ai_analysis={
                'ai_sentiment': ai_validation['ai_analysis'].sentiment_score if ai_validation['ai_analysis'] else None,
                'ai_confidence': ai_validation['ai_analysis'].confidence_level if ai_validation['ai_analysis'] else None,
                'ai_reasoning': ai_validation['ai_reasoning'],
                'technical_reasoning': combined_reasoning,
                'risk_assessment': ai_validation['risk_assessment']
            },
            exchange=data.exchange if 'data' in locals() else None,
            market_conditions={
                'volume_ratio': tech_analysis['volume_ratio'],
                'rsi': tech_analysis['rsi'],
                'macd_signal': tech_analysis['macd_line'] - tech_analysis['macd_signal'],
                'bb_position': tech_analysis['price_position_in_bb']
            }
        )
    
    def get_risk_parameters(self) -> Dict[str, float]:
        """Get risk parameters specific to scalping"""
        return {
            'max_position_size': 0.02,  # 2% of capital per position
            'stop_loss_percentage': float(self.stop_loss_percentage),
            'max_daily_loss': 0.05,     # 5% maximum daily loss
            'max_concurrent_positions': 5,
            'min_profit_target': float(self.min_profit_threshold),
            'max_hold_time_minutes': self.max_hold_time.total_seconds() / 60
        }
    
    # Technical Indicator Calculation Methods
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal).mean()
        macd_histogram = macd_line - macd_signal
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def _calculate_momentum(self, prices: pd.Series, period: int = 5) -> pd.Series:
        """Calculate price momentum"""
        return prices.pct_change(periods=period)
    
    def _get_bb_position(self, current_price: float, bb_upper: float, bb_lower: float) -> float:
        """Get position within Bollinger Bands (0 = lower band, 1 = upper band)"""
        if bb_upper == bb_lower:
            return 0.5
        return (current_price - bb_lower) / (bb_upper - bb_lower)
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics"""
        return {
            'strategy_name': self.strategy_type.value,
            'signals_generated': self.signals_generated,
            'ai_validations_passed': self.ai_validations_passed,
            'ai_validation_rate': self.ai_validations_passed / max(self.signals_generated, 1),
            'min_profit_threshold': float(self.min_profit_threshold),
            'max_profit_target': float(self.max_profit_target),
            'stop_loss_percentage': float(self.stop_loss_percentage),
            'max_hold_time_minutes': self.max_hold_time.total_seconds() / 60
        }
