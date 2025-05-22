"""
Operation Repository Interface - Defines contract for operation persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.arbitrage_operation import ArbitrageOperation, OperationStatus, OperationType


class IOperationRepository(ABC):
    """
    Interface for operation repository.
    
    Defines the contract for persisting and retrieving arbitrage operations.
    """
    
    @abstractmethod
    async def save(self, operation: ArbitrageOperation) -> None:
        """
        Save an operation to persistent storage.
        
        Args:
            operation: The operation to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, operation_id: str) -> Optional[ArbitrageOperation]:
        """
        Retrieve an operation by its ID.
        
        Args:
            operation_id: Unique identifier of the operation
            
        Returns:
            The operation if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_opportunity_id(self, opportunity_id: str) -> List[ArbitrageOperation]:
        """
        Retrieve operations related to a specific opportunity.
        
        Args:
            opportunity_id: ID of the related opportunity
            
        Returns:
            List of operations for the opportunity
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_status(self, status: OperationStatus) -> List[ArbitrageOperation]:
        """
        Retrieve operations by their status.
        
        Args:
            status: The status to filter by
            
        Returns:
            List of operations with the specified status
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_active_operations(self) -> List[ArbitrageOperation]:
        """
        Retrieve currently active operations (executing or pending).
        
        Returns:
            List of active operations
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_completed_operations(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ArbitrageOperation]:
        """
        Retrieve completed operations within a date range.
        
        Args:
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Returns:
            List of completed operations
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def update_status(self, operation_id: str, new_status: OperationStatus) -> None:
        """
        Update the status of an operation.
        
        Args:
            operation_id: ID of the operation to update
            new_status: New status to set
            
        Raises:
            RepositoryError: If update operation fails
            NotFoundError: If operation doesn't exist
        """
        pass
    
    @abstractmethod
    async def update_results(
        self, 
        operation_id: str, 
        results: Dict[str, Any]
    ) -> None:
        """
        Update the execution results of an operation.
        
        Args:
            operation_id: ID of the operation to update
            results: Dictionary containing execution results
            
        Raises:
            RepositoryError: If update operation fails
            NotFoundError: If operation doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_performance_summary(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get performance summary for operations in a date range.
        
        Args:
            start_date: Start date for the summary
            end_date: End date for the summary
            
        Returns:
            Dictionary containing performance summary
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def get_profit_loss_summary(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get profit/loss summary for operations in a date range.
        
        Args:
            start_date: Start date for the summary
            end_date: End date for the summary
            
        Returns:
            Dictionary containing P&L summary
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def get_by_operation_type(self, operation_type: OperationType) -> List[ArbitrageOperation]:
        """
        Retrieve operations by their type.
        
        Args:
            operation_type: The operation type to filter by
            
        Returns:
            List of operations with the specified type
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_most_profitable(self, limit: int = 10) -> List[ArbitrageOperation]:
        """
        Get the most profitable operations.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of most profitable operations
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def get_failed_operations_with_details(
        self, 
        start_date: Optional[datetime] = None
    ) -> List[ArbitrageOperation]:
        """
        Get failed operations with error details for analysis.
        
        Args:
            start_date: Optional start date filter
            
        Returns:
            List of failed operations with details
            
        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def count_by_status(self) -> Dict[OperationStatus, int]:
        """
        Count operations by their status.
        
        Returns:
            Dictionary mapping status to count
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def get_execution_statistics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get execution statistics for operations in a date range.
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary containing execution statistics
            
        Raises:
            RepositoryError: If operation fails
        """
        pass
    
    @abstractmethod
    async def cleanup_old_operations(self, days: int = 90) -> int:
        """
        Clean up old operations older than specified days.
        
        Args:
            days: Number of days to keep (default: 90)
            
        Returns:
            Number of operations removed
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ArbitrageOperation]:
        """
        Search operations with filters.
        
        Args:
            filters: Dictionary of search filters
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of matching operations
            
        Raises:
            RepositoryError: If search operation fails
        """
        pass
