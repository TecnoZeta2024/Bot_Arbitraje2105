"""
Data Transfer Objects for the Application Layer.
"""

from .operation_dto import CreateOperationDTO, OperationDTO
from .opportunity_dto import CreateOpportunityDTO, OpportunityDTO

__all__ = [
    "OpportunityDTO",
    "CreateOpportunityDTO",
    "OperationDTO",
    "CreateOperationDTO"
]
