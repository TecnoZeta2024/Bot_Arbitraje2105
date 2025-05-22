"""
Data Transfer Objects for the Application Layer.
"""

from .opportunity_dto import OpportunityDTO, CreateOpportunityDTO
from .operation_dto import OperationDTO, CreateOperationDTO

__all__ = [
    "OpportunityDTO",
    "CreateOpportunityDTO",
    "OperationDTO",
    "CreateOperationDTO"
]
