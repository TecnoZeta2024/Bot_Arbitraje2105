"""
Google Gemini AI Market Analyzer
Advanced AI-powered market analysis using Google Gemini API
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import google.generativeai as genai
from dataclasses import dataclass

from domain.trading_signals.trading_signal import TradingSignal, StrategyType
from domain.entities.market_data import MarketData


@dataclass
class AIAnalysisResult:
    """Result of AI analysis"""
    symbol: str
    timestamp: datetime
    sentiment_score: float  # 0-100
    confidence_level: float  # 0-1
    price_prediction_short: Optional[float]  # 1-15 min prediction
    risk_assessment: str  # LOW/MEDIUM/HIGH
    recommended_action: str  # BUY/SELL/HOLD
    reasoning: str
    patterns_detected: List[str]
    support_levels: List[float]
    resistance_levels: List[float]
    breakout_probability: float
    trend_strength: float
    raw_response: Dict[str, Any]


class GeminiAnalyzer:
    """
    Advanced market analyzer using Google Gemini AI
    
    Provides intelligent analysis for:
    - Market sentiment
    - Pattern recognition
    - Risk assessment
    - Price predictions
    - Trading signals validation
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini analyzer with API key"""
        try:
            if api_key:
                genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger = logging.getLogger("ai.gemini_analyzer")
            self.analysis_cache = {}
            self.cache_duration = timedelta(minutes=2)  # Cache analysis for 2 minutes
            
            # Test connection if API key provided
            if api_key:
                self._test_connection()
            self.logger.info("Gemini AI analyzer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini AI: {e}")
            # Don't raise, allow to continue without AI
    
    def _test_connection(self):
        """Test Gemini API connection"""
        try:
            test_response = self.model.generate_content("Test connection")
            if not test_response:
                raise Exception("No response from Gemini API")
        except Exception as e:
            raise Exception(f"Gemini API connection test failed: {e}")
    
    async def analyze_market_sentiment(self, symbol: str, market_data: MarketData) -> AIAnalysisResult:
        """
        Analyze market sentiment for a specific symbol using AI
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            market_data: Current market data for the symbol
            
        Returns:
            AIAnalysisResult with comprehensive analysis
        """
        # Check cache first
        cache_key = f"sentiment_{symbol}_{market_data.timestamp.strftime('%Y%m%d_%H%M')}"
        if self._is_cached(cache_key):
            return self.analysis_cache[cache_key]
        
        try:
            # Prepare data for AI analysis
            analysis_data = self._prepare_market_data_for_ai(symbol, market_data)
            
            # Create comprehensive prompt for sentiment analysis
            prompt = self._create_sentiment_analysis_prompt(symbol, analysis_data)
            
            # Get AI response
            response = await self._generate_ai_response(prompt)
            
            # Parse and validate response
            ai_result = self._parse_sentiment_response(symbol, response)
            
            # Cache result
            self.analysis_cache[cache_key] = ai_result
            
            self.logger.info(f"AI sentiment analysis completed for {symbol}: {ai_result.recommended_action}")
            return ai_result
            
        except Exception as e:
            self.logger.error(f"AI sentiment analysis failed for {symbol}: {e}")
            # Return default analysis in case of failure
            return self._create_fallback_analysis(symbol, market_data)
    
    async def detect_price_patterns(self, symbol: str, price_history: List[float]) -> Dict[str, Any]:
        """
        Detect complex price patterns using AI
        
        Args:
            symbol: Trading symbol
            price_history: List of historical prices (latest 50-100 points)
            
        Returns:
            Dictionary with detected patterns and analysis
        """
        cache_key = f"patterns_{symbol}_{len(price_history)}"
        if self._is_cached(cache_key):
            return self.analysis_cache[cache_key]
        
        try:
            # Convert to float for AI processing
            prices = price_history[-50:] if len(price_history) > 50 else price_history
            
            prompt = self._create_pattern_detection_prompt(symbol, prices)
            response = await self._generate_ai_response(prompt)
            
            pattern_result = self._parse_pattern_response(response)
            
            # Cache result
            self.analysis_cache[cache_key] = pattern_result
            
            return pattern_result
            
        except Exception as e:
            self.logger.error(f"Pattern detection failed for {symbol}: {e}")
            return self._create_fallback_pattern_analysis()
    
    async def assess_trading_risk(self, signal: TradingSignal, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for a trading signal using AI
        
        Args:
            signal: Trading signal to evaluate
            market_context: Additional market context data
            
        Returns:
            Risk assessment with recommendations
        """
        try:
            prompt = self._create_risk_assessment_prompt(signal, market_context)
            response = await self._generate_ai_response(prompt)
            
            risk_result = self._parse_risk_response(response)
            
            self.logger.info(f"AI risk assessment for {signal.symbol}: {risk_result.get('risk_score', 'unknown')}")
            return risk_result
            
        except Exception as e:
            self.logger.error(f"Risk assessment failed for {signal.symbol}: {e}")
            return self._create_fallback_risk_assessment()
    
    def _prepare_market_data_for_ai(self, symbol: str, market_data: MarketData) -> Dict[str, Any]:
        """Prepare market data in format suitable for AI analysis"""
        return {
            "symbol": symbol,
            "current_price": float(market_data.price),
            "volume_24h": float(market_data.volume) if market_data.volume else None,
            "price_change_24h": float(market_data.price_change_24h) if market_data.price_change_24h else None,
            "high_24h": float(market_data.high_24h) if market_data.high_24h else None,
            "low_24h": float(market_data.low_24h) if market_data.low_24h else None,
            "timestamp": market_data.timestamp.isoformat()
        }
    
    def _create_sentiment_analysis_prompt(self, symbol: str, data: Dict[str, Any]) -> str:
        """Create comprehensive prompt for sentiment analysis"""
        return f"""
        Analyze the following cryptocurrency market data for {symbol} and provide a structured sentiment analysis:
        
        Current Market Data:
        - Price: ${data['current_price']:.6f}
        - 24h Change: {data.get('price_change_24h', 'N/A')}%
        - Volume 24h: {data.get('volume_24h', 'N/A')}
        - High 24h: ${data.get('high_24h', 'N/A')}
        - Low 24h: ${data.get('low_24h', 'N/A')}
        
        Please provide analysis in the following JSON format only (no additional text):
        {{
            "sentiment_score": 50,
            "confidence_level": 0.7,
            "price_prediction_short": {data['current_price']},
            "risk_assessment": "MEDIUM",
            "recommended_action": "HOLD",
            "reasoning": "Market analysis based on current data",
            "market_regime": "ranging",
            "momentum_strength": 0.5,
            "support_level": {data['current_price'] * 0.98},
            "resistance_level": {data['current_price'] * 1.02}
        }}
        
        Consider current market conditions and provide conservative analysis.
        """
    
    def _create_pattern_detection_prompt(self, symbol: str, prices: List[float]) -> str:
        """Create prompt for pattern detection"""
        return f"""
        Analyze the following price sequence for {symbol} to detect technical patterns:
        
        Price History: {prices[-10:]}  # Last 10 prices for brevity
        
        Provide analysis in JSON format only:
        {{
            "patterns_detected": ["consolidation"],
            "support_levels": [{min(prices)}],
            "resistance_levels": [{max(prices)}],
            "breakout_probability": 0.5,
            "trend_strength": 0.5,
            "pattern_reliability": 0.6,
            "next_move_direction": "SIDEWAYS",
            "pattern_completion_probability": 0.5
        }}
        """
    
    def _create_risk_assessment_prompt(self, signal: TradingSignal, market_context: Dict[str, Any]) -> str:
        """Create prompt for risk assessment"""
        return f"""
        Evaluate the risk of this trading signal:
        
        Trading Signal:
        - Symbol: {signal.symbol}
        - Action: {signal.action.value}
        - Confidence: {signal.confidence:.2f}
        
        Provide risk analysis in JSON format only:
        {{
            "risk_score": 0.5,
            "risk_factors": ["market_volatility"],
            "mitigation_strategies": ["conservative_position_sizing"],
            "max_position_size": 0.05,
            "recommended_stop_loss": 0.01,
            "hold_time_recommendation": "30",
            "market_timing_score": 0.6
        }}
        """
    
    async def _generate_ai_response(self, prompt: str) -> str:
        """Generate AI response with retry logic"""
        max_retries = 2
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(self.model.generate_content, prompt)
                
                if response and response.text:
                    return response.text.strip()
                else:
                    raise Exception("Empty response from Gemini API")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"AI request attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    raise Exception(f"AI request failed after {max_retries} attempts: {e}")
    
    def _parse_sentiment_response(self, symbol: str, response: str) -> AIAnalysisResult:
        """Parse sentiment analysis response from AI"""
        try:
            # Clean response and extract JSON
            json_str = self._extract_json_from_response(response)
            data = json.loads(json_str)
            
            return AIAnalysisResult(
                symbol=symbol,
                timestamp=datetime.now(),
                sentiment_score=data.get("sentiment_score", 50.0),
                confidence_level=data.get("confidence_level", 0.5),
                price_prediction_short=data.get("price_prediction_short"),
                risk_assessment=data.get("risk_assessment", "MEDIUM"),
                recommended_action=data.get("recommended_action", "HOLD"),
                reasoning=data.get("reasoning", "AI analysis completed"),
                patterns_detected=[],
                support_levels=[data.get("support_level")] if data.get("support_level") else [],
                resistance_levels=[data.get("resistance_level")] if data.get("resistance_level") else [],
                breakout_probability=0.5,
                trend_strength=data.get("momentum_strength", 0.5),
                raw_response=data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return self._create_fallback_analysis(symbol, None)
    
    def _parse_pattern_response(self, response: str) -> Dict[str, Any]:
        """Parse pattern detection response"""
        try:
            json_str = self._extract_json_from_response(response)
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse pattern response: {e}")
            return self._create_fallback_pattern_analysis()
    
    def _parse_risk_response(self, response: str) -> Dict[str, Any]:
        """Parse risk assessment response"""
        try:
            json_str = self._extract_json_from_response(response)
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse risk response: {e}")
            return self._create_fallback_risk_assessment()
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from AI response that might contain extra text"""
        # Find JSON content between { and }
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1:
            return response[start:end+1]
        
        raise ValueError("No valid JSON found in response")
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if analysis is cached and still valid"""
        if cache_key in self.analysis_cache:
            # Check if cache entry has a timestamp and is still valid
            cached_item = self.analysis_cache[cache_key]
            if hasattr(cached_item, 'timestamp'):
                return datetime.now() - cached_item.timestamp < self.cache_duration
            return True  # Keep non-timestamped cache for short duration
        return False
    
    def _create_fallback_analysis(self, symbol: str, market_data: Optional[MarketData]) -> AIAnalysisResult:
        """Create fallback analysis when AI fails"""
        return AIAnalysisResult(
            symbol=symbol,
            timestamp=datetime.now(),
            sentiment_score=50.0,  # Neutral
            confidence_level=0.3,  # Low confidence
            price_prediction_short=None,
            risk_assessment="MEDIUM",
            recommended_action="HOLD",
            reasoning="AI analysis unavailable, using fallback",
            patterns_detected=[],
            support_levels=[],
            resistance_levels=[],
            breakout_probability=0.5,
            trend_strength=0.5,
            raw_response={"status": "fallback"}
        )
    
    def _create_fallback_pattern_analysis(self) -> Dict[str, Any]:
        """Create fallback pattern analysis"""
        return {
            "patterns_detected": [],
            "support_levels": [],
            "resistance_levels": [],
            "breakout_probability": 0.5,
            "trend_strength": 0.5,
            "pattern_reliability": 0.3
        }
    
    def _create_fallback_risk_assessment(self) -> Dict[str, Any]:
        """Create fallback risk assessment"""
        return {
            "risk_score": 0.5,
            "risk_factors": ["AI_ANALYSIS_UNAVAILABLE"],
            "mitigation_strategies": ["USE_CONSERVATIVE_POSITION_SIZE"],
            "max_position_size": 0.02,  # Very conservative
            "recommended_stop_loss": 0.01,  # 1%
            "market_timing_score": 0.5
        }
    
    def clear_cache(self):
        """Clear analysis cache"""
        self.analysis_cache.clear()
        self.logger.info("AI analysis cache cleared")
