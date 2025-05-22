"""
Data Transfer Objects for Opportunity entities.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid

from ...domain.entities.opportunity import Opportunity, OpportunityStatus
from ...domain.value_objects.currency import Currency
from ...domain.value_objects.price import Price
from ...domain.value_objects.profit_percentage import ProfitPercentage


@dataclass
class OpportunityDTO:
    """
    Data Transfer Object for Opportunity entity.
    
    Used for transferring opportunity data across application boundaries
    without exposing domain entities directly.
    """
    
    opportunity_id: str
    base_currency: str
    intermediate_currency: str
    quote_currency: str
    estimated_profit_percentage: float
    required_capital: float
    expected_profit: float
    first_pair_price: float
    second_pair_price: float
    third_pair_price: float
    detection_timestamp: str  # ISO format
    status: str
    expiry_timestamp: Optional[str] = None  # ISO format
    confidence_score: Optional[float] = None
    risk_score: Optional[float] = None
    
    # Computed fields
    trading_path: Optional[List[str]] = None
    required_pairs: Optional[List[str]] = None
    is_expired: Optional[bool] = None
    is_executable: Optional[bool] = None
    
    @classmethod
    def from_domain_entity(cls, opportunity: Opportunity) -> 'OpportunityDTO':
        """
        Create DTO from domain entity.
        
        Args:
            opportunity: Domain entity
            
        Returns:
            DTO representation
        """
        return cls(
            opportunity_id=opportunity.opportunity_id,
            base_currency=opportunity.base_currency.symbol,
            intermediate_currency=opportunity.intermediate_currency.symbol,
            quote_currency=opportunity.quote_currency.symbol,
            estimated_profit_percentage=opportunity.estimated_profit_percentage.value,
            required_capital=float(opportunity.required_capital),
            expected_profit=float(opportunity.expected_profit),
            first_pair_price=float(opportunity.first_pair_price.amount),
            second_pair_price=float(opportunity.second_pair_price.amount),
            third_pair_price=float(opportunity.third_pair_price.amount),
            detection_timestamp=opportunity.detection_timestamp.isoformat(),
            status=opportunity.status.value,
            expiry_timestamp=opportunity.expiry_timestamp.isoformat() if opportunity.expiry_timestamp else None,
            confidence_score=opportunity.confidence_score,
            risk_score=opportunity.risk_score,
            trading_path=opportunity.get_trading_path(),
            required_pairs=opportunity.get_required_pairs(),
            is_expired=opportunity.is_expired(),
            is_executable=opportunity.is_executable()
        )
    
    def to_domain_entity(self) -> Opportunity:
        """
        Convert DTO to domain entity.
        
        Returns:
            Domain entity
        """
        base_currency = Currency(self.base_currency)
        intermediate_currency = Currency(self.intermediate_currency)
        quote_currency = Currency(self.quote_currency)
        
        # For price currency, we'll use base currency as default
        # In a real implementation, this might need more sophisticated logic
        price_currency = base_currency
        
        return Opportunity(
            opportunity_id=self.opportunity_id,
            base_currency=base_currency,
            intermediate_currency=intermediate_currency,
            quote_currency=quote_currency,
            estimated_profit_percentage=ProfitPercentage(self.estimated_profit_percentage),
            required_capital=Decimal(str(self.required_capital)),
            expected_profit=Decimal(str(self.expected_profit)),
            first_pair_price=Price(Decimal(str(self.first_pair_price)), price_currency),
            second_pair_price=Price(Decimal(str(self.second_pair_price)), price_currency),
            third_pair_price=Price(Decimal(str(self.third_pair_price)), price_currency),
            detection_timestamp=datetime.fromisoformat(self.detection_timestamp),
            status=OpportunityStatus(self.status),
            expiry_timestamp=datetime.fromisoformat(self.expiry_timestamp) if self.expiry_timestamp else None,
            confidence_score=self.confidence_score,
            risk_score=self.risk_score
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary for serialization."""
        return {
            "opportunity_id": self.opportunity_id,
            "base_currency": self.base_currency,
            "intermediate_currency": self.intermediate_currency,
            "quote_currency": self.quote_currency,
            "estimated_profit_percentage": self.estimated_profit_percentage,
            "required_capital": self.required_capital,
            "expected_profit": self.expected_profit,
            "first_pair_price": self.first_pair_price,
            "second_pair_price": self.second_pair_price,
            "third_pair_price": self.third_pair_price,
            "detection_timestamp": self.detection_timestamp,
            "status": self.status,
            "expiry_timestamp": self.expiry_timestamp,
            "confidence_score": self.confidence_score,
            "risk_score": self.risk_score,
            "trading_path": self.trading_path,
            "required_pairs": self.required_pairs,
            "is_expired": self.is_expired,
            "is_executable": self.is_executable
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpportunityDTO':
        """Create DTO from dictionary."""
        return cls(**data)


@dataclass
class CreateOpportunityDTO:
    """
    Data Transfer Object for creating opportunities.
    
    Contains only the required fields for opportunity creation.
    """
    
    base_currency: str
    intermediate_currency: str
    quote_currency: str
    estimated_profit_percentage: float
    required_capital: float
    expected_profit: float
    first_pair_price: float
    second_pair_price: float
    third_pair_price: float
    confidence_score: Optional[float] = None
    risk_score: Optional[float] = None
    expiry_hours: Optional[int] = 1  # Hours until expiry
    
    def to_domain_entity(self) -> Opportunity:
        """
        Create domain entity from creation DTO.
        
        Returns:
            New opportunity domain entity
        """
        base_currency = Currency(self.base_currency)
        intermediate_currency = Currency(self.intermediate_currency)
        quote_currency = Currency(self.quote_currency)
        
        # Generate unique ID
        opportunity_id = str(uuid.uuid4())
        
        # Set expiry timestamp
        expiry_timestamp = None
        if self.expiry_hours:
            expiry_timestamp = datetime.utcnow() + timedelta(hours=self.expiry_hours)
        
        # Use base currency for prices (this might need refinement)
        price_currency = base_currency
        
        return Opportunity(
            opportunity_id=opportunity_id,
            base_currency=base_currency,
            intermediate_currency=intermediate_currency,
            quote_currency=quote_currency,
            estimated_profit_percentage=ProfitPercentage(self.estimated_profit_percentage),
            required_capital=Decimal(str(self.required_capital)),
            expected_profit=Decimal(str(self.expected_profit)),
            first_pair_price=Price(Decimal(str(self.first_pair_price)), price_currency),
            second_pair_price=Price(Decimal(str(self.second_pair_price)), price_currency),
            third_pair_price=Price(Decimal(str(self.third_pair_price)), price_currency),
            detection_timestamp=datetime.utcnow(),
            status=OpportunityStatus.DETECTED,
            expiry_timestamp=expiry_timestamp,
            confidence_score=self.confidence_score,
            risk_score=self.risk_score
        )
    
    def validate(self) -> List[str]:
        """
        Validate the creation DTO.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate currencies
        if not self.base_currency or len(self.base_currency) < 2:
            errors.append("Base currency is required and must be at least 2 characters")
        
        if not self.intermediate_currency or len(self.intermediate_currency) < 2:
            errors.append("Intermediate currency is required and must be at least 2 characters")
        
        if not self.quote_currency or len(self.quote_currency) < 2:
            errors.append("Quote currency is required and must be at least 2 characters")
        
        # Validate currencies are different
        currencies = {self.base_currency, self.intermediate_currency, self.quote_currency}
        if len(currencies) != 3:
            errors.append("All three currencies must be different")
        
        # Validate profit percentage
        if self.estimated_profit_percentage <= 0:
            errors.append("Estimated profit percentage must be positive")
        
        if self.estimated_profit_percentage > 100:  # 100% profit seems unrealistic
            errors.append("Estimated profit percentage seems unrealistically high")
        
        # Validate capital
        if self.required_capital <= 0:
            errors.append("Required capital must be positive")
        
        if self.required_capital < 10:  # Minimum viable capital
            errors.append("Required capital must be at least 10")
        
        # Validate expected profit
        if self.expected_profit <= 0:
            errors.append("Expected profit must be positive")
        
        # Validate prices
        if self.first_pair_price <= 0:
            errors.append("First pair price must be positive")
        
        if self.second_pair_price <= 0:
            errors.append("Second pair price must be positive")
        
        if self.third_pair_price <= 0:
            errors.append("Third pair price must be positive")
        
        # Validate optional scores
        if self.confidence_score is not None:
            if not (0 <= self.confidence_score <= 1):
                errors.append("Confidence score must be between 0 and 1")
        
        if self.risk_score is not None:
            if not (0 <= self.risk_score <= 1):
                errors.append("Risk score must be between 0 and 1")
        
        # Validate expiry hours
        if self.expiry_hours is not None:
            if self.expiry_hours <= 0 or self.expiry_hours > 24:
                errors.append("Expiry hours must be between 1 and 24")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary for serialization."""
        return {
            "base_currency": self.base_currency,
            "intermediate_currency": self.intermediate_currency,
            "quote_currency": self.quote_currency,
            "estimated_profit_percentage": self.estimated_profit_percentage,
            "required_capital": self.required_capital,
            "expected_profit": self.expected_profit,
            "first_pair_price": self.first_pair_price,
            "second_pair_price": self.second_pair_price,
            "third_pair_price": self.third_pair_price,
            "confidence_score": self.confidence_score,
            "risk_score": self.risk_score,
            "expiry_hours": self.expiry_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateOpportunityDTO':
        """Create DTO from dictionary."""
        return cls(**data)


# Import required modules
from datetime import datetime, timedelta
