"""
Concrete implementation of IOpportunityRepository using Supabase.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from ...domain.repositories.opportunity_repository import IOpportunityRepository
from ...domain.entities.opportunity import Opportunity, OpportunityStatus
from ...domain.value_objects.currency import Currency
from ...domain.value_objects.price import Price
from ...domain.value_objects.profit_percentage import ProfitPercentage
from ..external_apis.supabase_client import SupabaseClient
from ...utils.logger import get_logger


class RepositoryError(Exception):
    """Exception raised for repository operations."""
    pass


class NotFoundError(RepositoryError):
    """Exception raised when entity is not found."""
    pass


class OpportunityRepositoryImpl(IOpportunityRepository):
    """
    Concrete implementation of opportunity repository using Supabase.
    
    Implements the IOpportunityRepository interface defined in the domain layer.
    This follows the Dependency Inversion Principle.
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self._supabase = supabase_client
        self._logger = get_logger(self.__class__.__name__)
        self._table_name = "arbitraje_oportunidades"
    
    async def save(self, opportunity: Opportunity) -> None:
        """Save an opportunity to Supabase."""
        try:
            data = self._serialize_opportunity(opportunity)
            
            # Check if opportunity already exists
            existing = await self.get_by_id(opportunity.opportunity_id)
            
            if existing:
                # Update existing opportunity
                response = self._supabase.client.table(self._table_name)\
                    .update(data)\
                    .eq("opportunity_id", opportunity.opportunity_id)\
                    .execute()
            else:
                # Insert new opportunity
                response = self._supabase.client.table(self._table_name)\
                    .insert(data)\
                    .execute()
            
            if not response.data:
                raise RepositoryError("Failed to save opportunity")
                
            self._logger.info(f"Saved opportunity {opportunity.opportunity_id}")
            
        except Exception as e:
            self._logger.error(f"Error saving opportunity {opportunity.opportunity_id}: {e}")
            raise RepositoryError(f"Failed to save opportunity: {e}")
    
    async def get_by_id(self, opportunity_id: str) -> Optional[Opportunity]:
        """Retrieve an opportunity by its ID."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .select("*")\
                .eq("opportunity_id", opportunity_id)\
                .limit(1)\
                .execute()
            
            if not response.data:
                return None
            
            return self._deserialize_opportunity(response.data[0])
            
        except Exception as e:
            self._logger.error(f"Error retrieving opportunity {opportunity_id}: {e}")
            raise RepositoryError(f"Failed to retrieve opportunity: {e}")
    
    async def get_by_status(self, status: OpportunityStatus) -> List[Opportunity]:
        """Retrieve opportunities by their status."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .select("*")\
                .eq("status", status.value)\
                .execute()
            
            return [self._deserialize_opportunity(data) for data in response.data]
            
        except Exception as e:
            self._logger.error(f"Error retrieving opportunities by status {status}: {e}")
            raise RepositoryError(f"Failed to retrieve opportunities by status: {e}")
    
    async def get_pending_confirmation(self) -> List[Opportunity]:
        """Retrieve opportunities pending user confirmation."""
        return await self.get_by_status(OpportunityStatus.PENDING_CONFIRMATION)
    
    async def get_executable(self) -> List[Opportunity]:
        """Retrieve opportunities that are ready for execution."""
        return await self.get_by_status(OpportunityStatus.APPROVED)
    
    async def get_recent(self, hours: int = 24) -> List[Opportunity]:
        """Retrieve opportunities detected in the last N hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            response = self._supabase.client.table(self._table_name)\
                .select("*")\
                .gte("detection_timestamp", cutoff_time.isoformat())\
                .order("detection_timestamp", desc=True)\
                .execute()
            
            return [self._deserialize_opportunity(data) for data in response.data]
            
        except Exception as e:
            self._logger.error(f"Error retrieving recent opportunities: {e}")
            raise RepositoryError(f"Failed to retrieve recent opportunities: {e}")
    
    async def update_status(self, opportunity_id: str, new_status: OpportunityStatus) -> None:
        """Update the status of an opportunity."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .update({"status": new_status.value})\
                .eq("opportunity_id", opportunity_id)\
                .execute()
            
            if not response.data:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
                
            self._logger.info(f"Updated opportunity {opportunity_id} status to {new_status.value}")
            
        except Exception as e:
            self._logger.error(f"Error updating opportunity status: {e}")
            if "not found" in str(e).lower():
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            raise RepositoryError(f"Failed to update opportunity status: {e}")
    
    async def delete(self, opportunity_id: str) -> None:
        """Delete an opportunity from storage."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .delete()\
                .eq("opportunity_id", opportunity_id)\
                .execute()
            
            if not response.data:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
                
            self._logger.info(f"Deleted opportunity {opportunity_id}")
            
        except Exception as e:
            self._logger.error(f"Error deleting opportunity: {e}")
            if "not found" in str(e).lower():
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            raise RepositoryError(f"Failed to delete opportunity: {e}")
    
    async def get_by_currency_pair(
        self, 
        base_currency: str, 
        intermediate_currency: str, 
        quote_currency: str
    ) -> List[Opportunity]:
        """Retrieve opportunities for a specific currency triplet."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .select("*")\
                .eq("base_currency", base_currency)\
                .eq("intermediate_currency", intermediate_currency)\
                .eq("quote_currency", quote_currency)\
                .execute()
            
            return [self._deserialize_opportunity(data) for data in response.data]
            
        except Exception as e:
            self._logger.error(f"Error retrieving opportunities by currency pair: {e}")
            raise RepositoryError(f"Failed to retrieve opportunities by currency pair: {e}")
    
    async def get_performance_metrics(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get performance metrics for opportunities in a date range."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .select("*")\
                .gte("detection_timestamp", start_date.isoformat())\
                .lte("detection_timestamp", end_date.isoformat())\
                .execute()
            
            opportunities = response.data
            total_count = len(opportunities)
            
            if total_count == 0:
                return {
                    "total_opportunities": 0,
                    "average_profit_percentage": 0,
                    "max_profit_percentage": 0,
                    "min_profit_percentage": 0,
                    "status_distribution": {}
                }
            
            profit_percentages = [float(opp.get("estimated_profit_percentage", 0)) for opp in opportunities]
            status_counts = {}
            
            for opp in opportunities:
                status = opp.get("status", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_opportunities": total_count,
                "average_profit_percentage": sum(profit_percentages) / len(profit_percentages),
                "max_profit_percentage": max(profit_percentages),
                "min_profit_percentage": min(profit_percentages),
                "status_distribution": status_counts,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
        except Exception as e:
            self._logger.error(f"Error calculating performance metrics: {e}")
            raise RepositoryError(f"Failed to calculate performance metrics: {e}")
    
    async def cleanup_expired(self) -> int:
        """Remove expired opportunities from storage."""
        try:
            current_time = datetime.utcnow()
            
            # Get expired opportunities
            response = self._supabase.client.table(self._table_name)\
                .select("opportunity_id")\
                .lt("expiry_timestamp", current_time.isoformat())\
                .execute()
            
            expired_ids = [opp["opportunity_id"] for opp in response.data]
            
            if not expired_ids:
                return 0
            
            # Delete expired opportunities
            delete_response = self._supabase.client.table(self._table_name)\
                .delete()\
                .in_("opportunity_id", expired_ids)\
                .execute()
            
            deleted_count = len(delete_response.data) if delete_response.data else 0
            self._logger.info(f"Cleaned up {deleted_count} expired opportunities")
            
            return deleted_count
            
        except Exception as e:
            self._logger.error(f"Error cleaning up expired opportunities: {e}")
            raise RepositoryError(f"Failed to cleanup expired opportunities: {e}")
    
    async def get_top_profitable(self, limit: int = 10) -> List[Opportunity]:
        """Get the most profitable opportunities."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .select("*")\
                .order("estimated_profit_percentage", desc=True)\
                .limit(limit)\
                .execute()
            
            return [self._deserialize_opportunity(data) for data in response.data]
            
        except Exception as e:
            self._logger.error(f"Error retrieving top profitable opportunities: {e}")
            raise RepositoryError(f"Failed to retrieve top profitable opportunities: {e}")
    
    async def count_by_status(self) -> Dict[OpportunityStatus, int]:
        """Count opportunities by their status."""
        try:
            response = self._supabase.client.table(self._table_name)\
                .select("status")\
                .execute()
            
            status_counts = {}
            for row in response.data:
                status_str = row.get("status", "UNKNOWN")
                try:
                    status = OpportunityStatus(status_str)
                    status_counts[status] = status_counts.get(status, 0) + 1
                except ValueError:
                    # Handle unknown status values
                    self._logger.warning(f"Unknown status found: {status_str}")
            
            return status_counts
            
        except Exception as e:
            self._logger.error(f"Error counting opportunities by status: {e}")
            raise RepositoryError(f"Failed to count opportunities by status: {e}")
    
    async def search(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Opportunity]:
        """Search opportunities with filters."""
        try:
            query = self._supabase.client.table(self._table_name).select("*")
            
            # Apply filters
            for key, value in filters.items():
                if key == "min_profit_percentage":
                    query = query.gte("estimated_profit_percentage", value)
                elif key == "max_profit_percentage":
                    query = query.lte("estimated_profit_percentage", value)
                elif key == "status":
                    query = query.eq("status", value)
                elif key == "base_currency":
                    query = query.eq("base_currency", value)
                elif key == "quote_currency":
                    query = query.eq("quote_currency", value)
                elif key == "after_date":
                    query = query.gte("detection_timestamp", value)
                elif key == "before_date":
                    query = query.lte("detection_timestamp", value)
            
            # Apply pagination
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            response = query.execute()
            return [self._deserialize_opportunity(data) for data in response.data]
            
        except Exception as e:
            self._logger.error(f"Error searching opportunities: {e}")
            raise RepositoryError(f"Failed to search opportunities: {e}")
    
    def _serialize_opportunity(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Convert Opportunity entity to database format."""
        return {
            "opportunity_id": opportunity.opportunity_id,
            "base_currency": opportunity.base_currency.symbol,
            "intermediate_currency": opportunity.intermediate_currency.symbol,
            "quote_currency": opportunity.quote_currency.symbol,
            "estimated_profit_percentage": float(opportunity.estimated_profit_percentage.value),
            "required_capital": float(opportunity.required_capital),
            "expected_profit": float(opportunity.expected_profit),
            "first_pair_price": float(opportunity.first_pair_price.amount),
            "second_pair_price": float(opportunity.second_pair_price.amount),
            "third_pair_price": float(opportunity.third_pair_price.amount),
            "detection_timestamp": opportunity.detection_timestamp.isoformat(),
            "status": opportunity.status.value,
            "expiry_timestamp": opportunity.expiry_timestamp.isoformat() if opportunity.expiry_timestamp else None,
            "confidence_score": opportunity.confidence_score,
            "risk_score": opportunity.risk_score
        }
    
    def _deserialize_opportunity(self, data: Dict[str, Any]) -> Opportunity:
        """Convert database format to Opportunity entity."""
        base_currency = Currency(data["base_currency"])
        intermediate_currency = Currency(data["intermediate_currency"])
        quote_currency = Currency(data["quote_currency"])
        
        # Create price objects (assuming same currency for simplicity)
        price_currency = base_currency  # This might need adjustment based on actual pair structure
        
        return Opportunity(
            opportunity_id=data["opportunity_id"],
            base_currency=base_currency,
            intermediate_currency=intermediate_currency,
            quote_currency=quote_currency,
            estimated_profit_percentage=ProfitPercentage(float(data["estimated_profit_percentage"])),
            required_capital=data["required_capital"],
            expected_profit=data["expected_profit"],
            first_pair_price=Price(data["first_pair_price"], price_currency),
            second_pair_price=Price(data["second_pair_price"], price_currency),
            third_pair_price=Price(data["third_pair_price"], price_currency),
            detection_timestamp=datetime.fromisoformat(data["detection_timestamp"]),
            status=OpportunityStatus(data["status"]),
            expiry_timestamp=datetime.fromisoformat(data["expiry_timestamp"]) if data.get("expiry_timestamp") else None,
            confidence_score=data.get("confidence_score"),
            risk_score=data.get("risk_score")
        )
