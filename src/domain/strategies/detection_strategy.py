"""
Detection Strategy Interface - Open/Closed Principle implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..entities.opportunity import Opportunity
from ..entities.market_data import MarketData


class DetectionType(Enum):
    """Type of detection strategy."""
    TRIANGULAR_ARBITRAGE = "TRIANGULAR_ARBITRAGE"
    SIMPLE_ARBITRAGE = "SIMPLE_ARBITRAGE" 
    SCALPING = "SCALPING"
    CROSS_EXCHANGE = "CROSS_EXCHANGE"
    STATISTICAL_ARBITRAGE = "STATISTICAL_ARBITRAGE"


@dataclass
class DetectionResult:
    """
    Result of a detection strategy.
    
    Encapsulates all opportunities found and detection metadata.
    """
    
    # Core results
    opportunities: List[Opportunity]
    detection_type: DetectionType
    
    # Detection metrics
    total_combinations_checked: int = 0
    valid_combinations: int = 0
    opportunities_above_threshold: int = 0
    detection_time_seconds: float = 0.0
    
    # Market data info
    symbols_analyzed: int = 0
    tickers_processed: int = 0
    market_data_age_seconds: Optional[float] = None
    
    # Strategy info
    strategy_name: str = ""
    strategy_parameters: Dict[str, Any] = None
    
    # Quality metrics
    confidence_score: float = 0.8
    data_quality_score: float = 0.9
    
    # Metadata
    detection_timestamp: datetime = None
    
    def __post_init__(self):
        if self.detection_timestamp is None:
            self.detection_timestamp = datetime.utcnow()
        if self.strategy_parameters is None:
            self.strategy_parameters = {}
    
    def get_detection_rate(self) -> float:
        """Get the rate of opportunities per combination checked."""
        if self.total_combinations_checked == 0:
            return 0.0
        return len(self.opportunities) / self.total_combinations_checked
    
    def get_efficiency_score(self) -> float:
        """Get detection efficiency score (0-1)."""
        if self.detection_time_seconds == 0:
            return 0.0
        
        # Opportunities per second
        ops_per_second = len(self.opportunities) / self.detection_time_seconds
        
        # Normalize to 0-1 scale (assuming max 1 opportunity per second is excellent)
        return min(ops_per_second, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "opportunities_count": len(self.opportunities),
            "detection_type": self.detection_type.value,
            "strategy_name": self.strategy_name,
            "total_combinations_checked": self.total_combinations_checked,
            "valid_combinations": self.valid_combinations,
            "opportunities_above_threshold": self.opportunities_above_threshold,
            "detection_time_seconds": self.detection_time_seconds,
            "symbols_analyzed": self.symbols_analyzed,
            "tickers_processed": self.tickers_processed,
            "market_data_age_seconds": self.market_data_age_seconds,
            "confidence_score": self.confidence_score,
            "data_quality_score": self.data_quality_score,
            "detection_rate": self.get_detection_rate(),
            "efficiency_score": self.get_efficiency_score(),
            "detection_timestamp": self.detection_timestamp.isoformat(),
            "strategy_parameters": self.strategy_parameters
        }


class IDetectionStrategy(ABC):
    """
    Interface for detection strategies.
    
    Applies Open/Closed Principle - new detection strategies can be added
    without modifying existing code. Each strategy encapsulates a different
    approach to finding arbitrage opportunities.
    """
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of the detection strategy."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the detection strategy."""
        pass
    
    @property
    @abstractmethod
    def detection_type(self) -> DetectionType:
        """Type of detection this strategy performs."""
        pass
    
    @abstractmethod
    async def detect_opportunities(
        self, 
        market_data: List[MarketData],
        parameters: Optional[Dict[str, Any]] = None
    ) -> DetectionResult:
        """
        Detect arbitrage opportunities in the provided market data.
        
        Args:
            market_data: List of market data to analyze
            parameters: Optional parameters to override defaults
            
        Returns:
            Detection result with found opportunities
        """
        pass
    
    @abstractmethod
    def validate_market_data(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """
        Validate that market data is suitable for this detection strategy.
        
        Args:
            market_data: Market data to validate
            
        Returns:
            Validation result with is_valid boolean and details
        """
        pass
    
    @abstractmethod
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """
        Get the parameters and configuration of this strategy.
        
        Returns:
            Strategy parameters
        """
        pass
    
    @abstractmethod
    def update_strategy_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update strategy parameters.
        
        Args:
            parameters: New parameters to set
            
        Returns:
            Updated parameters
        """
        pass
    
    @abstractmethod
    def get_min_market_data_requirements(self) -> Dict[str, Any]:
        """
        Get minimum market data requirements for this strategy.
        
        Returns:
            Requirements dictionary
        """
        pass
    
    def supports_real_time(self) -> bool:
        """
        Check if this strategy supports real-time detection.
        
        Returns:
            True if real-time capable, False otherwise
        """
        # Default implementation - can be overridden
        return True
    
    def get_expected_performance(self) -> Dict[str, Any]:
        """
        Get expected performance characteristics of this strategy.
        
        Returns:
            Performance characteristics
        """
        # Default implementation - can be overridden
        return {
            "avg_opportunities_per_scan": 5,
            "avg_detection_time_seconds": 10,
            "typical_profit_range": [0.1, 2.0],  # percentage
            "data_freshness_requirement_seconds": 30
        }


class BaseDetectionStrategy(IDetectionStrategy):
    """
    Base implementation of detection strategy with common functionality.
    
    Provides default implementations and utility methods that can be
    shared across different concrete strategies.
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        detection_type: DetectionType
    ):
        self._name = name
        self._description = description
        self._detection_type = detection_type
        self._parameters = self._get_default_parameters()
    
    @property
    def strategy_name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def detection_type(self) -> DetectionType:
        return self._detection_type
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        return self._parameters.copy()
    
    def update_strategy_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update strategy parameters with validation."""
        # Basic validation - can be overridden in concrete strategies
        for key, value in parameters.items():
            if key in self._parameters:
                # Basic type checking
                expected_type = type(self._parameters[key])
                if isinstance(value, expected_type):
                    self._parameters[key] = value
        
        return self.get_strategy_parameters()
    
    def validate_market_data(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Basic market data validation."""
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        
        if not market_data:
            validation["is_valid"] = False
            validation["errors"].append("No market data provided")
            return validation
        
        # Check data freshness
        max_age = self._parameters.get("max_data_age_seconds", 300)
        stale_data_count = sum(1 for md in market_data if md.is_stale(max_age))
        
        if stale_data_count > 0:
            stale_percentage = (stale_data_count / len(market_data)) * 100
            if stale_percentage > 50:
                validation["is_valid"] = False
                validation["errors"].append(f"{stale_percentage:.1f}% of market data is stale")
            else:
                validation["warnings"].append(f"{stale_percentage:.1f}% of market data is stale")
        
        # Check minimum data requirements
        min_requirements = self.get_min_market_data_requirements()
        if len(market_data) < min_requirements.get("min_symbols", 10):
            validation["is_valid"] = False
            validation["errors"].append(
                f"Insufficient market data: {len(market_data)} symbols "
                f"(minimum: {min_requirements.get('min_symbols', 10)})"
            )
        
        return validation
    
    def get_min_market_data_requirements(self) -> Dict[str, Any]:
        """Default minimum requirements."""
        return {
            "min_symbols": 10,
            "min_liquidity_usd": 100000,
            "max_spread_percentage": 1.0,
            "max_data_age_seconds": 300
        }
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for this strategy - to be overridden."""
        return {
            "profit_threshold_percentage": 0.1,
            "max_capital_per_opportunity": 1000.0,
            "max_data_age_seconds": 300,
            "min_liquidity_usd": 100000.0
        }
    
    def _create_detection_result(
        self, 
        opportunities: List[Opportunity],
        **kwargs
    ) -> DetectionResult:
        """Helper method to create detection results."""
        return DetectionResult(
            opportunities=opportunities,
            detection_type=self.detection_type,
            strategy_name=self.strategy_name,
            strategy_parameters=self.get_strategy_parameters(),
            **kwargs
        )
    
    def _filter_opportunities_by_threshold(
        self, 
        opportunities: List[Opportunity]
    ) -> List[Opportunity]:
        """Filter opportunities by profit threshold."""
        threshold = self._parameters.get("profit_threshold_percentage", 0.1)
        return [
            opp for opp in opportunities 
            if opp.estimated_profit_percentage.value >= threshold
        ]
    
    def _assess_market_data_quality(self, market_data: List[MarketData]) -> float:
        """Assess overall quality of market data (0-1 score)."""
        if not market_data:
            return 0.0
        
        quality_scores = []
        
        for md in market_data:
            score = 1.0
            
            # Penalize stale data
            if md.is_stale(60):  # 1 minute
                score -= 0.3
            elif md.is_stale(300):  # 5 minutes
                score -= 0.1
            
            # Reward tight spreads
            if md.spread_percentage and md.spread_percentage < 0.1:
                score += 0.1
            elif md.spread_percentage and md.spread_percentage > 1.0:
                score -= 0.2
            
            # Reward high liquidity
            if md.volume_24h and md.volume_24h > 1000000:  # > 1M
                score += 0.1
            elif md.volume_24h and md.volume_24h < 100000:  # < 100K
                score -= 0.2
            
            quality_scores.append(max(0.0, min(1.0, score)))
        
        return sum(quality_scores) / len(quality_scores)
