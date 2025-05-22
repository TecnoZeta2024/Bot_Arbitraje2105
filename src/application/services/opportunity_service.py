"""
OpportunityService - Application service for managing arbitrage opportunities.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dependency_injector.wiring import Provide, inject

from ..dto.opportunity_dto import OpportunityDTO, CreateOpportunityDTO
from ...domain.entities.opportunity import Opportunity, OpportunityStatus
from ...domain.repositories.opportunity_repository import IOpportunityRepository
from ...infrastructure.container.dependency_injection import Container
from ...utils.logger import get_logger


class OpportunityService:
    """
    Application service for managing arbitrage opportunities.
    
    Orchestrates business operations related to opportunities,
    coordinating between domain entities and infrastructure.
    This follows the Application Service pattern.
    """
    
    @inject
    def __init__(
        self,
        opportunity_repository: IOpportunityRepository = Provide[Container.opportunity_repository]
    ):
        self._opportunity_repository = opportunity_repository
        self._logger = get_logger(self.__class__.__name__)
    
    async def create_opportunity(self, create_dto: CreateOpportunityDTO) -> OpportunityDTO:
        """
        Create a new arbitrage opportunity.
        
        Args:
            create_dto: Data transfer object with opportunity creation data
            
        Returns:
            Created opportunity as DTO
            
        Raises:
            ServiceError: If creation fails
        """
        try:
            # Convert DTO to domain entity
            opportunity = create_dto.to_domain_entity()
            
            # Save through repository
            await self._opportunity_repository.save(opportunity)
            
            self._logger.info(f"Created opportunity {opportunity.opportunity_id}")
            
            # Return as DTO
            return OpportunityDTO.from_domain_entity(opportunity)
            
        except Exception as e:
            self._logger.error(f"Error creating opportunity: {e}")
            raise ServiceError(f"Failed to create opportunity: {e}")
    
    async def get_opportunity(self, opportunity_id: str) -> Optional[OpportunityDTO]:
        """
        Get an opportunity by ID.
        
        Args:
            opportunity_id: Unique identifier of the opportunity
            
        Returns:
            Opportunity as DTO if found, None otherwise
        """
        try:
            opportunity = await self._opportunity_repository.get_by_id(opportunity_id)
            
            if not opportunity:
                return None
            
            return OpportunityDTO.from_domain_entity(opportunity)
            
        except Exception as e:
            self._logger.error(f"Error retrieving opportunity {opportunity_id}: {e}")
            raise ServiceError(f"Failed to retrieve opportunity: {e}")
    
    async def get_pending_opportunities(self) -> List[OpportunityDTO]:
        """
        Get all opportunities pending user confirmation.
        
        Returns:
            List of pending opportunities as DTOs
        """
        try:
            opportunities = await self._opportunity_repository.get_pending_confirmation()
            return [OpportunityDTO.from_domain_entity(opp) for opp in opportunities]
            
        except Exception as e:
            self._logger.error(f"Error retrieving pending opportunities: {e}")
            raise ServiceError(f"Failed to retrieve pending opportunities: {e}")
    
    async def get_executable_opportunities(self) -> List[OpportunityDTO]:
        """
        Get all opportunities ready for execution.
        
        Returns:
            List of executable opportunities as DTOs
        """
        try:
            opportunities = await self._opportunity_repository.get_executable()
            return [OpportunityDTO.from_domain_entity(opp) for opp in opportunities]
            
        except Exception as e:
            self._logger.error(f"Error retrieving executable opportunities: {e}")
            raise ServiceError(f"Failed to retrieve executable opportunities: {e}")
    
    async def approve_opportunity(self, opportunity_id: str) -> OpportunityDTO:
        """
        Approve an opportunity for execution.
        
        Args:
            opportunity_id: ID of the opportunity to approve
            
        Returns:
            Updated opportunity as DTO
            
        Raises:
            ServiceError: If approval fails
            NotFoundError: If opportunity doesn't exist
        """
        try:
            # Get opportunity
            opportunity = await self._opportunity_repository.get_by_id(opportunity_id)
            if not opportunity:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            
            # Apply business rule through domain entity
            opportunity.approve()
            
            # Save changes
            await self._opportunity_repository.save(opportunity)
            
            self._logger.info(f"Approved opportunity {opportunity_id}")
            
            return OpportunityDTO.from_domain_entity(opportunity)
            
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f"Error approving opportunity {opportunity_id}: {e}")
            raise ServiceError(f"Failed to approve opportunity: {e}")
    
    async def reject_opportunity(self, opportunity_id: str) -> OpportunityDTO:
        """
        Reject an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity to reject
            
        Returns:
            Updated opportunity as DTO
        """
        try:
            # Get opportunity
            opportunity = await self._opportunity_repository.get_by_id(opportunity_id)
            if not opportunity:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            
            # Apply business rule through domain entity
            opportunity.reject()
            
            # Save changes
            await self._opportunity_repository.save(opportunity)
            
            self._logger.info(f"Rejected opportunity {opportunity_id}")
            
            return OpportunityDTO.from_domain_entity(opportunity)
            
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f"Error rejecting opportunity {opportunity_id}: {e}")
            raise ServiceError(f"Failed to reject opportunity: {e}")
    
    async def mark_opportunity_as_executing(self, opportunity_id: str) -> OpportunityDTO:
        """
        Mark an opportunity as being executed.
        
        Args:
            opportunity_id: ID of the opportunity being executed
            
        Returns:
            Updated opportunity as DTO
        """
        try:
            opportunity = await self._opportunity_repository.get_by_id(opportunity_id)
            if not opportunity:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            
            opportunity.mark_as_executing()
            await self._opportunity_repository.save(opportunity)
            
            self._logger.info(f"Marked opportunity {opportunity_id} as executing")
            
            return OpportunityDTO.from_domain_entity(opportunity)
            
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f"Error marking opportunity as executing: {e}")
            raise ServiceError(f"Failed to mark opportunity as executing: {e}")
    
    async def complete_opportunity(self, opportunity_id: str) -> OpportunityDTO:
        """
        Mark an opportunity as completed.
        
        Args:
            opportunity_id: ID of the opportunity to complete
            
        Returns:
            Updated opportunity as DTO
        """
        try:
            opportunity = await self._opportunity_repository.get_by_id(opportunity_id)
            if not opportunity:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            
            opportunity.mark_as_completed()
            await self._opportunity_repository.save(opportunity)
            
            self._logger.info(f"Completed opportunity {opportunity_id}")
            
            return OpportunityDTO.from_domain_entity(opportunity)
            
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f"Error completing opportunity: {e}")
            raise ServiceError(f"Failed to complete opportunity: {e}")
    
    async def fail_opportunity(self, opportunity_id: str) -> OpportunityDTO:
        """
        Mark an opportunity as failed.
        
        Args:
            opportunity_id: ID of the opportunity that failed
            
        Returns:
            Updated opportunity as DTO
        """
        try:
            opportunity = await self._opportunity_repository.get_by_id(opportunity_id)
            if not opportunity:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            
            opportunity.mark_as_failed()
            await self._opportunity_repository.save(opportunity)
            
            self._logger.info(f"Marked opportunity {opportunity_id} as failed")
            
            return OpportunityDTO.from_domain_entity(opportunity)
            
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f"Error marking opportunity as failed: {e}")
            raise ServiceError(f"Failed to mark opportunity as failed: {e}")
    
    async def get_opportunities_by_status(self, status: OpportunityStatus) -> List[OpportunityDTO]:
        """
        Get opportunities by their status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of opportunities with the specified status
        """
        try:
            opportunities = await self._opportunity_repository.get_by_status(status)
            return [OpportunityDTO.from_domain_entity(opp) for opp in opportunities]
            
        except Exception as e:
            self._logger.error(f"Error retrieving opportunities by status {status}: {e}")
            raise ServiceError(f"Failed to retrieve opportunities by status: {e}")
    
    async def get_recent_opportunities(self, hours: int = 24) -> List[OpportunityDTO]:
        """
        Get opportunities detected in the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent opportunities
        """
        try:
            opportunities = await self._opportunity_repository.get_recent(hours)
            return [OpportunityDTO.from_domain_entity(opp) for opp in opportunities]
            
        except Exception as e:
            self._logger.error(f"Error retrieving recent opportunities: {e}")
            raise ServiceError(f"Failed to retrieve recent opportunities: {e}")
    
    async def get_top_profitable_opportunities(self, limit: int = 10) -> List[OpportunityDTO]:
        """
        Get the most profitable opportunities.
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of top profitable opportunities
        """
        try:
            opportunities = await self._opportunity_repository.get_top_profitable(limit)
            return [OpportunityDTO.from_domain_entity(opp) for opp in opportunities]
            
        except Exception as e:
            self._logger.error(f"Error retrieving top profitable opportunities: {e}")
            raise ServiceError(f"Failed to retrieve top profitable opportunities: {e}")
    
    async def cleanup_expired_opportunities(self) -> int:
        """
        Clean up expired opportunities.
        
        Returns:
            Number of opportunities cleaned up
        """
        try:
            count = await self._opportunity_repository.cleanup_expired()
            self._logger.info(f"Cleaned up {count} expired opportunities")
            return count
            
        except Exception as e:
            self._logger.error(f"Error cleaning up expired opportunities: {e}")
            raise ServiceError(f"Failed to cleanup expired opportunities: {e}")
    
    async def get_opportunity_statistics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get opportunity statistics for a date range.
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary containing opportunity statistics
        """
        try:
            metrics = await self._opportunity_repository.get_performance_metrics(start_date, end_date)
            status_counts = await self._opportunity_repository.count_by_status()
            
            return {
                **metrics,
                "status_distribution": {status.value: count for status, count in status_counts.items()}
            }
            
        except Exception as e:
            self._logger.error(f"Error calculating opportunity statistics: {e}")
            raise ServiceError(f"Failed to calculate opportunity statistics: {e}")
    
    async def search_opportunities(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[OpportunityDTO]:
        """
        Search opportunities with filters.
        
        Args:
            filters: Search filters
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching opportunities
        """
        try:
            opportunities = await self._opportunity_repository.search(filters, limit, offset)
            return [OpportunityDTO.from_domain_entity(opp) for opp in opportunities]
            
        except Exception as e:
            self._logger.error(f"Error searching opportunities: {e}")
            raise ServiceError(f"Failed to search opportunities: {e}")


class ServiceError(Exception):
    """Exception raised for service layer errors."""
    pass


class NotFoundError(ServiceError):
    """Exception raised when entity is not found."""
    pass
