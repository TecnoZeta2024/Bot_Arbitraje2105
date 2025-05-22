"""
Base Trading Strategy Abstract Class
Defines the interface and common functionality for all trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from domain.trading_signals.trading_signal import TradingSignal
from domain.entities.market_data import MarketData


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    
    Implements Strategy Pattern allowing different trading algorithms
    to be used interchangeably while maintaining consistent interface
    """
    
    @abstractmethod
    async def analyze(self, market_data: MarketData) -> TradingSignal:
        """
        Analyze market data and generate trading signal
        
        Args:
            market_data: Market data for analysis
            
        Returns:
            Trading signal or None if no signal generated
        """
        pass
    
    @abstractmethod
    def get_risk_parameters(self) -> Dict[str, float]:
        """
        Get risk management parameters specific to this strategy
        
        Returns:
            Dictionary containing risk parameters like max_position_size,
            stop_loss_percentage, max_daily_loss, etc.
        """
        pass
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return self.__class__.__name__
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return getattr(self, '__doc__', 'No description available')
    
    async def validate_signal(self, signal: TradingSignal, market_data: MarketData) -> bool:
        """
        Validate a trading signal against current market conditions
        
        Can be overridden by specific strategies for custom validation
        """
        # Basic validation
        if signal.confidence < 0.5:
            return False
        
        if signal.expected_profit <= 0:
            return False
        
        return True
    
    def calculate_position_size(self, signal: TradingSignal, available_capital: float) -> float:
        """
        Calculate position size based on signal confidence and risk parameters
        
        Can be overridden by specific strategies
        """
        risk_params = self.get_risk_parameters()
        max_position_size = risk_params.get('max_position_size', 0.02)
        
        # Adjust position size based on confidence
        confidence_multiplier = signal.confidence
        position_size = max_position_size * confidence_multiplier
        
        return min(position_size, max_position_size)


# Alias for backward compatibility
TradingStrategy = BaseStrategy
