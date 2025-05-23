"""
RiskManager - Single responsibility for risk management and validation.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ...domain.entities.arbitrage_operation import ArbitrageOperation
from ...domain.entities.execution_step import ExecutionStep
from ...domain.entities.opportunity import Opportunity
from ...utils.logger import get_logger


class RiskManager:
    """
    Responsible ONLY for risk assessment and management.
    
    Applies Single Responsibility Principle - this class has only one reason to change:
    when risk management rules change.
    """
    
    def __init__(self):
        self._logger = get_logger(self.__class__.__name__)
        
        # Risk configuration
        self._max_daily_operations = 50
        self._max_capital_per_operation = Decimal("1000")
        self._max_total_capital_at_risk = Decimal("5000")
        self._min_profit_threshold = 0.1  # 0.1%
        self._max_slippage_tolerance = 2.0  # 2%
        self._max_execution_time_seconds = 300  # 5 minutes
    
    def assess_opportunity_risk(self, opportunity: Opportunity) -> Dict[str, Any]:
        """
        Assess the risk level of an arbitrage opportunity.
        
        Args:
            opportunity: The opportunity to assess
            
        Returns:
            Risk assessment result
        """
        self._logger.info(f"Assessing opportunity risk: {opportunity.opportunity_id}")
        
        risk_assessment = {
            "opportunity_id": opportunity.opportunity_id,
            "overall_risk_level": "LOW",
            "risk_score": 0.0,
            "risk_factors": [],
            "recommendations": [],
            "is_approved": True,
            "max_recommended_capital": float(opportunity.required_capital)
        }
        
        risk_score = 0.0
        
        # 1. Profit margin risk
        profit_risk = self._assess_profit_margin_risk(opportunity)
        risk_score += profit_risk["score"]
        if profit_risk["factors"]:
            risk_assessment["risk_factors"].extend(profit_risk["factors"])
        
        # 2. Capital requirement risk
        capital_risk = self._assess_capital_risk(opportunity)
        risk_score += capital_risk["score"]
        if capital_risk["factors"]:
            risk_assessment["risk_factors"].extend(capital_risk["factors"])
        
        # 3. Market volatility risk
        volatility_risk = self._assess_volatility_risk(opportunity)
        risk_score += volatility_risk["score"]
        if volatility_risk["factors"]:
            risk_assessment["risk_factors"].extend(volatility_risk["factors"])
        
        # 4. Execution complexity risk
        complexity_risk = self._assess_execution_complexity_risk(opportunity)
        risk_score += complexity_risk["score"]
        if complexity_risk["factors"]:
            risk_assessment["risk_factors"].extend(complexity_risk["factors"])
        
        # 5. Time-based risk (opportunity age)
        time_risk = self._assess_time_risk(opportunity)
        risk_score += time_risk["score"]
        if time_risk["factors"]:
            risk_assessment["risk_factors"].extend(time_risk["factors"])
        
        # Calculate overall risk level and approval
        risk_assessment["risk_score"] = risk_score
        
        if risk_score <= 2.0:
            risk_assessment["overall_risk_level"] = "LOW"
        elif risk_score <= 4.0:
            risk_assessment["overall_risk_level"] = "MEDIUM"
        else:
            risk_assessment["overall_risk_level"] = "HIGH"
        
        # Approval decision
        if risk_score > 6.0:
            risk_assessment["is_approved"] = False
            risk_assessment["recommendations"].append("Opportunity rejected due to high risk")
        elif risk_score > 4.0:
            risk_assessment["is_approved"] = True
            risk_assessment["max_recommended_capital"] = float(opportunity.required_capital) * 0.5
            risk_assessment["recommendations"].append("Reduce capital by 50% due to medium-high risk")
        
        return risk_assessment
    
    def _assess_profit_margin_risk(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Assess risk based on profit margin."""
        profit_percentage = opportunity.estimated_profit_percentage.value
        
        if profit_percentage < self._min_profit_threshold:
            return {
                "score": 3.0,
                "factors": [f"Low profit margin: {profit_percentage:.4f}%"]
            }
        elif profit_percentage > 10.0:  # Suspiciously high
            return {
                "score": 2.0,
                "factors": [f"Unusually high profit margin: {profit_percentage:.4f}% - verify data"]
            }
        
        return {"score": 0.0, "factors": []}
    
    def _assess_capital_risk(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Assess risk based on capital requirements."""
        capital = opportunity.required_capital
        
        if capital > self._max_capital_per_operation:
            return {
                "score": 2.5,
                "factors": [f"High capital requirement: {capital} exceeds limit {self._max_capital_per_operation}"]
            }
        elif capital < Decimal("10"):
            return {
                "score": 1.0,
                "factors": [f"Very low capital: {capital} may not be worth transaction costs"]
            }
        
        return {"score": 0.0, "factors": []}
    
    def _assess_volatility_risk(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Assess market volatility risk."""
        # Simple heuristic based on currency types
        currencies = [
            opportunity.base_currency.symbol,
            opportunity.intermediate_currency.symbol,
            opportunity.quote_currency.symbol
        ]
        
        volatile_currencies = ["DOGE", "SHIB", "MEME", "PEPE"]  # Example volatile coins
        stable_currencies = ["USDT", "USDC", "BUSD", "DAI"]
        major_currencies = ["BTC", "ETH", "BNB"]
        
        volatility_score = 0.0
        factors = []
        
        volatile_count = sum(1 for c in currencies if c in volatile_currencies)
        stable_count = sum(1 for c in currencies if c in stable_currencies)
        major_count = sum(1 for c in currencies if c in major_currencies)
        
        if volatile_count >= 2:
            volatility_score += 2.0
            factors.append(f"Multiple volatile currencies: {volatile_count}")
        elif volatile_count == 1:
            volatility_score += 1.0
            factors.append("Contains volatile currency")
        
        if stable_count == 0:
            volatility_score += 1.0
            factors.append("No stable currency anchor")
        
        return {"score": volatility_score, "factors": factors}
    
    def _assess_execution_complexity_risk(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Assess execution complexity risk."""
        required_pairs = opportunity.get_required_pairs()
        
        complexity_score = 0.0
        factors = []
        
        # More pairs = more complexity
        if len(required_pairs) > 3:
            complexity_score += 1.5
            factors.append(f"High complexity: {len(required_pairs)} trading pairs required")
        
        # Check for obscure trading pairs (simple heuristic)
        obscure_pairs = []
        for pair in required_pairs:
            if len(pair) > 8:  # Long pair names might indicate less common pairs
                obscure_pairs.append(pair)
        
        if obscure_pairs:
            complexity_score += 1.0
            factors.append(f"Potentially obscure pairs: {obscure_pairs}")
        
        return {"score": complexity_score, "factors": factors}
    
    def _assess_time_risk(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Assess time-based risks."""
        now = datetime.utcnow()
        age_seconds = (now - opportunity.detection_timestamp).total_seconds()
        
        time_score = 0.0
        factors = []
        
        # Stale opportunities are riskier
        if age_seconds > 300:  # 5 minutes
            time_score += 2.0
            factors.append(f"Stale opportunity: {age_seconds:.0f} seconds old")
        elif age_seconds > 60:  # 1 minute
            time_score += 1.0
            factors.append(f"Aging opportunity: {age_seconds:.0f} seconds old")
        
        # Check expiry
        if opportunity.expiry_timestamp:
            time_to_expiry = (opportunity.expiry_timestamp - now).total_seconds()
            if time_to_expiry < 60:  # Less than 1 minute to execute
                time_score += 2.5
                factors.append(f"Expires soon: {time_to_expiry:.0f} seconds remaining")
        
        return {"score": time_score, "factors": factors}
    
    def validate_operation_execution(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """
        Validate that an operation is safe to execute.
        
        Args:
            operation: The operation to validate
            
        Returns:
            Validation result
        """
        self._logger.info(f"Validating operation execution: {operation.operation_id}")
        
        validation = {
            "operation_id": operation.operation_id,
            "is_approved": True,
            "warnings": [],
            "errors": [],
            "risk_level": "LOW"
        }
        
        # Check operation status
        if operation.status.value != "PENDING":
            validation["is_approved"] = False
            validation["errors"].append(f"Operation not in PENDING status: {operation.status.value}")
        
        # Check execution steps
        if not operation.execution_steps:
            validation["is_approved"] = False
            validation["errors"].append("No execution steps defined")
        
        # Check capital limits
        if operation.initial_capital > self._max_capital_per_operation:
            validation["is_approved"] = False
            validation["errors"].append(
                f"Capital {operation.initial_capital} exceeds limit {self._max_capital_per_operation}"
            )
        
        # Check for duplicate operations
        # (This would require access to operation repository - simplified for now)
        
        return validation
    
    def monitor_execution_risks(self, operation: ArbitrageOperation) -> Dict[str, Any]:
        """
        Monitor risks during operation execution.
        
        Args:
            operation: The executing operation
            
        Returns:
            Risk monitoring result
        """
        monitoring = {
            "operation_id": operation.operation_id,
            "execution_time_seconds": 0,
            "current_risk_level": "LOW",
            "alerts": [],
            "should_abort": False
        }
        
        # Check execution time
        if operation.started_at:
            execution_time = (datetime.utcnow() - operation.started_at).total_seconds()
            monitoring["execution_time_seconds"] = execution_time
            
            if execution_time > self._max_execution_time_seconds:
                monitoring["current_risk_level"] = "HIGH"
                monitoring["alerts"].append(f"Execution time exceeded: {execution_time:.0f}s")
                monitoring["should_abort"] = True
        
        # Check step completion rate
        completed_steps = sum(1 for step in operation.execution_steps if step.is_successful())
        total_steps = len(operation.execution_steps)
        
        if total_steps > 0:
            completion_rate = completed_steps / total_steps
            if completion_rate < 0.5 and completed_steps > 0:
                monitoring["alerts"].append(f"Low completion rate: {completion_rate:.1%}")
        
        # Check accumulated slippage
        total_slippage = operation.total_slippage
        if total_slippage > self._max_slippage_tolerance:
            monitoring["current_risk_level"] = "HIGH"
            monitoring["alerts"].append(f"High slippage: {total_slippage:.2f}%")
        
        return monitoring
    
    def assess_daily_risk_exposure(self, operations: List[ArbitrageOperation]) -> Dict[str, Any]:
        """
        Assess total risk exposure for the day.
        
        Args:
            operations: List of operations for the day
            
        Returns:
            Daily risk assessment
        """
        today = datetime.utcnow().date()
        today_operations = [
            op for op in operations 
            if op.created_at.date() == today
        ]
        
        total_capital_at_risk = sum(op.initial_capital for op in today_operations)
        
        assessment = {
            "date": today.isoformat(),
            "total_operations": len(today_operations),
            "total_capital_at_risk": float(total_capital_at_risk),
            "risk_level": "LOW",
            "limits_exceeded": [],
            "recommendations": []
        }
        
        # Check daily operation limit
        if len(today_operations) > self._max_daily_operations:
            assessment["risk_level"] = "HIGH"
            assessment["limits_exceeded"].append(
                f"Daily operation limit exceeded: {len(today_operations)}/{self._max_daily_operations}"
            )
        
        # Check total capital at risk
        if total_capital_at_risk > self._max_total_capital_at_risk:
            assessment["risk_level"] = "HIGH"
            assessment["limits_exceeded"].append(
                f"Total capital at risk exceeded: {total_capital_at_risk}/{self._max_total_capital_at_risk}"
            )
        
        # Success rate analysis
        completed_operations = [op for op in today_operations if op.status.value == "COMPLETED"]
        if completed_operations:
            successful_operations = [op for op in completed_operations if op.is_profitable()]
            success_rate = len(successful_operations) / len(completed_operations)
            
            if success_rate < 0.5:
                assessment["risk_level"] = "MEDIUM"
                assessment["recommendations"].append(f"Low success rate today: {success_rate:.1%}")
        
        return assessment
    
    def get_risk_limits(self) -> Dict[str, Any]:
        """Get current risk management limits."""
        return {
            "max_daily_operations": self._max_daily_operations,
            "max_capital_per_operation": float(self._max_capital_per_operation),
            "max_total_capital_at_risk": float(self._max_total_capital_at_risk),
            "min_profit_threshold": self._min_profit_threshold,
            "max_slippage_tolerance": self._max_slippage_tolerance,
            "max_execution_time_seconds": self._max_execution_time_seconds
        }
    
    def update_risk_limits(self, new_limits: Dict[str, Any]) -> Dict[str, Any]:
        """Update risk management limits."""
        updated = {}
        
        if "max_daily_operations" in new_limits:
            self._max_daily_operations = int(new_limits["max_daily_operations"])
            updated["max_daily_operations"] = self._max_daily_operations
        
        if "max_capital_per_operation" in new_limits:
            self._max_capital_per_operation = Decimal(str(new_limits["max_capital_per_operation"]))
            updated["max_capital_per_operation"] = float(self._max_capital_per_operation)
        
        if "max_total_capital_at_risk" in new_limits:
            self._max_total_capital_at_risk = Decimal(str(new_limits["max_total_capital_at_risk"]))
            updated["max_total_capital_at_risk"] = float(self._max_total_capital_at_risk)
        
        if "min_profit_threshold" in new_limits:
            self._min_profit_threshold = float(new_limits["min_profit_threshold"])
            updated["min_profit_threshold"] = self._min_profit_threshold
        
        if "max_slippage_tolerance" in new_limits:
            self._max_slippage_tolerance = float(new_limits["max_slippage_tolerance"])
            updated["max_slippage_tolerance"] = self._max_slippage_tolerance
        
        if "max_execution_time_seconds" in new_limits:
            self._max_execution_time_seconds = int(new_limits["max_execution_time_seconds"])
            updated["max_execution_time_seconds"] = self._max_execution_time_seconds
        
        self._logger.info(f"Updated risk limits: {updated}")
        return updated
