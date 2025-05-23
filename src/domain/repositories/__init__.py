"""
Repository interfaces for the Triangular Arbitrage Bot Domain.
"""

from .market_data_repository import IMarketDataRepository
from .operation_repository import IOperationRepository
from .opportunity_repository import IOpportunityRepository
from .trading_pair_repository import ITradingPairRepository

__all__ = [
    "IOpportunityRepository",
    "IOperationRepository",
    "IMarketDataRepository", 
    "ITradingPairRepository"
]
