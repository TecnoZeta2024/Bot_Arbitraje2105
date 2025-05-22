"""
Repository interfaces for the Triangular Arbitrage Bot Domain.
"""

from .opportunity_repository import IOpportunityRepository
from .operation_repository import IOperationRepository
from .market_data_repository import IMarketDataRepository
from .trading_pair_repository import ITradingPairRepository

__all__ = [
    "IOpportunityRepository",
    "IOperationRepository",
    "IMarketDataRepository", 
    "ITradingPairRepository"
]
