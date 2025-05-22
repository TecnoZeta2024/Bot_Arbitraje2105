"""
Trading Signal Entity - Core domain entity for trading decisions
Implements SRP and represents a pure domain concept
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class SignalAction(Enum):
    """Enumeration of possible trading actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    EXECUTE_ARBITRAGE = "EXECUTE_ARBITRAGE"


class RiskLevel(Enum):
    """Risk level classification"""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StrategyType(Enum):
    """Trading strategy types"""
    SCALPING = "scalping"
    DAY_TRADING = "day_trading"
    TRIANGULAR_ARBITRAGE = "triangular_arbitrage"
    SIMPLE_ARBITRAGE = "simple_arbitrage"


@dataclass(frozen=True)
class TradingSignal:
    """
    Core trading signal entity that represents a trading opportunity
    
    This is a pure domain entity following SRP - it only represents
    the concept of a trading signal without any business logic
    """
    # Identity
    signal_id: str
    timestamp: datetime
    
    # Trading Details
    strategy_name: StrategyType
    symbol: str
    action: SignalAction
    
    # Confidence and Risk
    confidence: float  # 0.0 - 1.0
    expected_profit: float  # Expected profit percentage
    risk_level: RiskLevel
    
    # Technical Details
    timeframe: str  # '1m', '5m', '15m', '1h', etc.
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # AI Analysis
    ai_analysis: Optional[Dict[str, Any]] = None
    
    # Metadata
    exchange: Optional[str] = None
    market_conditions: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate signal data integrity"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if self.expected_profit < 0:
            raise ValueError("Expected profit cannot be negative")
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if signal has high confidence (>= 0.7)"""
        return self.confidence >= 0.7
    
    @property
    def is_low_risk(self) -> bool:
        """Check if signal is low risk"""
        return self.risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]
    
    @property
    def is_scalping_signal(self) -> bool:
        """Check if this is a scalping signal"""
        return self.strategy_name == StrategyType.SCALPING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary for serialization"""
        return {
            'signal_id': self.signal_id,
            'timestamp': self.timestamp.isoformat(),
            'strategy_name': self.strategy_name.value,
            'symbol': self.symbol,
            'action': self.action.value,
            'confidence': self.confidence,
            'expected_profit': self.expected_profit,
            'risk_level': self.risk_level.value,
            'timeframe': self.timeframe,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'ai_analysis': self.ai_analysis,
            'exchange': self.exchange,
            'market_conditions': self.market_conditions
        }
