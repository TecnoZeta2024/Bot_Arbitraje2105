"""
Opportunity Repository Interface - Defines contract for opportunity persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.opportunity import Opportunity, OpportunityStatus


class IOpportunityRepository(ABC):
    """
    Interface for opportunity repository.
    
    Defines the contract for persisting and retrieving arbitrage opportunities.
    This follows the Dependency Inversion Principle - the domain layer defines
    the interface, and infrastructure layer implements it.
    """
    
    @abstractmethod
    async def save(self, opportunity: Opportunity) -> None:
        """
        Save an opportunity to persistent storage.
        
        Args:
            opportunity: The opportunity to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, opportunity_id: str) -> Optional[Opportunity]:
        """
        Retrieve an opportunity by its ID.
        
        Args:
            opportunity_id: Unique identifier of the opportunity
            
        Returns:
            The opportunity if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_status(self, status: OpportunityStatus) -> List[Opportunity]:
        """
        Retrieve opportunities by their status.
        
        Args:
            status: The status to filter by
            
        Returns:
            List of opportunities with the specified status
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_pending_confirmation(self) -> List[Opportunity]:
        """
        Retrieve opportunities pending user confirmation.
        
        Returns:
            List of opportunities pending confirmation
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_executable(self) -> List[Opportunity]:
        """
        Retrieve opportunities that are ready for execution.
        
        Returns:
            List of executable opportunities
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_recent(self, hours: int = 24) -> List[Opportunity]:
        """
        Retrieve opportunities detected in the last N hours.
        
        Args:
            hours: Number of hours to look back (default: 24)
            
        Returns:
            List of recent opportunities
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def update_status(self, opportunity_id: str, new_status: OpportunityStatus) -> None:
        """
        Update the status of an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity to update
            new_status: New status to set
            
        Raises:
            RepositoryError: If update operation fails
            NotFoundError: If opportunity doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete(self, opportunity_id: str) -> None:
        """
        Delete an opportunity from storage.
        
        Args:
            opportunity_id: ID of the opportunity to delete
            
        Raises:
            RepositoryError: If deletion operation fails
            NotFoundError: If opportunity doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_by_currency_pair(
        self, 
        base_currency: str, 
        intermediate_currency: str, 
        quote_currency: str
    ) -> List[Opportunity]:
        """
        Retrieve opportunities for a specific currency triplet.
        
        Args:
            base_currency: Base currency symbol
            intermediate_currency: Intermediate currency symbol
            quote_currency: Quote currency symbol
            
        Returns:
            List of opportunities for the currency triplet
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_performance_metrics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get performance metrics for opportunities in a date range.
        
        Args:
            start_date: Start date for the metrics
            end_date: End date for the metrics
            
        Returns:
            Dictionary containing performance metrics
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove expired opportunities from storage.
        
        Returns:
            Number of opportunities removed
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        pass
    
    @abstractmethod
    async def get_top_profitable(self, limit: int = 10) -> List[Opportunity]:
        """
        Get the most profitable opportunities.
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of top profitable opportunities
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def count_by_status(self) -> Dict[OpportunityStatus, int]:
        """
        Count opportunities by their status.
        
        Returns:
            Dictionary mapping status to count
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Opportunity]:
        """
        Search opportunities with filters.
        
        Args:
            filters: Dictionary of search filters
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of matching opportunities
            
        Raises:
            RepositoryError: If search operation fails
        """
        pass
