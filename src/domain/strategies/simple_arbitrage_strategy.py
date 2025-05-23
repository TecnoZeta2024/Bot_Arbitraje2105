"""
Simple Arbitrage Detection Strategy - Concrete implementation.
"""

import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ...utils.logger import get_logger
from ..entities.market_data import MarketData
from ..entities.opportunity import Opportunity
from ..value_objects.currency import Currency
from ..value_objects.price import Price
from ..value_objects.profit_percentage import ProfitPercentage
from .detection_strategy import BaseDetectionStrategy, DetectionResult, DetectionType


class SimpleArbitrageStrategy(BaseDetectionStrategy):
    """
    Concrete implementation of simple arbitrage detection strategy.
    
    Detects opportunities where the same asset is priced differently
    across different trading pairs or markets (price discrepancies).
    """
    
    def __init__(self):
        super().__init__(
            name="Simple Arbitrage",
            description="Detects simple arbitrage opportunities between different trading pairs",
            detection_type=DetectionType.SIMPLE_ARBITRAGE
        )
        self._logger = get_logger(self.__class__.__name__)
    
    async def detect_opportunities(
        self, 
        market_data: List[MarketData],
        parameters: Optional[Dict[str, Any]] = None
    ) -> DetectionResult:
        """Detect simple arbitrage opportunities."""
        start_time = time.time()
        self._logger.info("Starting simple arbitrage detection")
        
        # Use provided parameters or defaults
        if parameters:
            self.update_strategy_parameters(parameters)
        
        # Validate market data
        validation = self.validate_market_data(market_data)
        if not validation["is_valid"]:
            self._logger.error(f"Invalid market data: {validation['errors']}")
            return self._create_detection_result(
                opportunities=[],
                detection_time_seconds=time.time() - start_time,
                confidence_score=0.0
            )
        
        # Group pairs by base currency to find price discrepancies
        currency_groups = self._group_by_base_currency(market_data)
        
        opportunities = []
        stats = {
            "pairs_analyzed": 0,
            "price_discrepancies_found": 0,
            "opportunities_above_threshold": 0
        }
        
        # Analyze each currency group for arbitrage opportunities
        for base_currency, pairs in currency_groups.items():
            if len(pairs) < 2:
                continue
                
            stats["pairs_analyzed"] += len(pairs)
            
            # Find arbitrage opportunities between different quote currencies
            group_opportunities = self._find_arbitrage_in_group(base_currency, pairs)
            
            for opp in group_opportunities:
                stats["price_discrepancies_found"] += 1
                if opp.estimated_profit_percentage.value >= self._parameters["profit_threshold_percentage"]:
                    opportunities.append(opp)
                    stats["opportunities_above_threshold"] += 1
        
        detection_time = time.time() - start_time
        self._logger.info(f"Simple arbitrage detection completed in {detection_time:.2f}s: {len(opportunities)} opportunities")
        
        return self._create_detection_result(
            opportunities=opportunities,
            total_combinations_checked=stats["pairs_analyzed"],
            valid_combinations=stats["price_discrepancies_found"],
            opportunities_above_threshold=stats["opportunities_above_threshold"],
            detection_time_seconds=detection_time,
            symbols_analyzed=len(market_data),
            tickers_processed=len(market_data),
            confidence_score=self._calculate_confidence_score(stats, market_data),
            data_quality_score=self._assess_market_data_quality(market_data)
        )
    
    def _group_by_base_currency(self, market_data: List[MarketData]) -> Dict[str, List[MarketData]]:
        """Group market data by base currency."""
        groups = {}
        
        for md in market_data:
            if not md.is_suitable_for_arbitrage():
                continue
                
            base_currency = md.base_currency.symbol
            if base_currency not in groups:
                groups[base_currency] = []
            groups[base_currency].append(md)
        
        # Only keep groups with multiple pairs
        return {k: v for k, v in groups.items() if len(v) >= 2}
    
    def _find_arbitrage_in_group(self, base_currency: str, pairs: List[MarketData]) -> List[Opportunity]:
        """Find arbitrage opportunities within a currency group."""
        opportunities = []
        
        # Compare all pairs within the group
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                md1 = pairs[i]
                md2 = pairs[j]
                
                # Skip if same quote currency
                if md1.quote_currency.symbol == md2.quote_currency.symbol:
                    continue
                
                # Calculate arbitrage opportunity
                opp = self._calculate_simple_arbitrage(md1, md2, base_currency)
                if opp:
                    opportunities.append(opp)
        
        return opportunities
    
    def _calculate_simple_arbitrage(
        self, 
        md1: MarketData, 
        md2: MarketData, 
        base_currency: str
    ) -> Optional[Opportunity]:
        """Calculate simple arbitrage between two market data points."""
        try:
            # Get effective prices (considering bid/ask if available)
            price1 = self._get_effective_price(md1, "sell")  # Sell on md1
            price2 = self._get_effective_price(md2, "buy")   # Buy on md2
            
            if not price1 or not price2:
                return None
            
            # Calculate arbitrage: sell high, buy low
            if price1.amount <= price2.amount:
                return None  # No arbitrage opportunity
            
            # Calculate profit percentage
            profit_decimal = (price1.amount - price2.amount) / price2.amount
            gross_profit_percentage = float(profit_decimal * 100)
            
            # Apply fees (simplified calculation)
            fee_percentage = self._parameters.get("fee_percentage", 0.1)
            net_profit_percentage = gross_profit_percentage - (2 * fee_percentage)  # Two trades
            
            if net_profit_percentage <= 0:
                return None
            
            # Create opportunity
            return self._create_simple_arbitrage_opportunity(
                md1, md2, base_currency, net_profit_percentage, price1, price2
            )
            
        except Exception as e:
            self._logger.debug(f"Error calculating simple arbitrage: {e}")
            return None
    
    def _get_effective_price(self, md: MarketData, side: str) -> Optional[Price]:
        """Get effective price for buying or selling."""
        if side == "buy":
            # When buying, use ask price (higher)
            return md.ask_price if md.ask_price else md.price
        else:
            # When selling, use bid price (lower)
            return md.bid_price if md.bid_price else md.price
    
    def _create_simple_arbitrage_opportunity(
        self,
        md1: MarketData,
        md2: MarketData,
        base_currency: str,
        profit_percentage: float,
        sell_price: Price,
        buy_price: Price
    ) -> Opportunity:
        """Create Opportunity entity for simple arbitrage."""
        import uuid
        from datetime import datetime, timedelta

        # Use market data currencies
        base_curr = Currency(base_currency)
        quote_curr1 = md1.quote_currency
        quote_curr2 = md2.quote_currency
        
        # Use quote_curr1 as intermediate (sell high in this pair)
        intermediate_currency = quote_curr1
        quote_currency = quote_curr2
        
        # Calculate capital and profit
        capital = Decimal(str(self._parameters.get("default_capital", 100.0)))
        expected_profit = capital * Decimal(str(profit_percentage)) / 100
        
        return Opportunity(
            opportunity_id=str(uuid.uuid4()),
            base_currency=base_curr,
            intermediate_currency=intermediate_currency,
            quote_currency=quote_currency,
            estimated_profit_percentage=ProfitPercentage(profit_percentage),
            required_capital=capital,
            expected_profit=expected_profit,
            first_pair_price=sell_price,
            second_pair_price=buy_price,
            third_pair_price=Price(Decimal("1.0"), base_curr),  # Placeholder
            detection_timestamp=datetime.utcnow(),
            status=OpportunityStatus.DETECTED,
            expiry_timestamp=datetime.utcnow() + timedelta(
                seconds=self._parameters.get("opportunity_ttl_seconds", 180)  # Shorter TTL
            ),
            confidence_score=0.9,  # Simple arbitrage is more straightforward
            risk_score=0.2
        )
    
    def _calculate_confidence_score(
        self, 
        stats: Dict[str, int], 
        market_data: List[MarketData]
    ) -> float:
        """Calculate confidence score for simple arbitrage detection."""
        base_score = 0.9  # Simple arbitrage is generally more reliable
        
        # Adjust based on data quality
        data_quality = self._assess_market_data_quality(market_data)
        
        # Adjust based on market coverage
        if stats["pairs_analyzed"] < 10:
            base_score -= 0.2  # Low market coverage
        
        # Adjust based on opportunity density
        if stats["pairs_analyzed"] > 0:
            opportunity_rate = stats["opportunities_above_threshold"] / stats["pairs_analyzed"]
            if opportunity_rate > 0.1:  # Very high opportunity rate might be suspicious
                base_score -= 0.1
        
        return max(0.0, min(1.0, base_score * data_quality))
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for simple arbitrage strategy."""
        return {
            "profit_threshold_percentage": 0.05,  # Lower threshold for simple arbitrage
            "max_capital_per_opportunity": 500.0,  # Lower capital for simple arbitrage
            "max_data_age_seconds": 30,  # Fresher data needed
            "min_liquidity_usd": 50000.0,  # Lower liquidity requirement
            "fee_percentage": 0.1,
            "default_capital": 100.0,
            "opportunity_ttl_seconds": 180  # Shorter TTL for simple arbitrage
        }
    
    def get_min_market_data_requirements(self) -> Dict[str, Any]:
        """Get minimum requirements for simple arbitrage."""
        return {
            "min_symbols": 10,  # Need multiple pairs per currency
            "min_liquidity_usd": 50000,
            "max_spread_percentage": 0.2,  # Tighter spread requirement
            "max_data_age_seconds": 30
        }
    
    def supports_real_time(self) -> bool:
        """Simple arbitrage benefits from real-time data."""
        return True
    
    def get_expected_performance(self) -> Dict[str, Any]:
        """Get expected performance for simple arbitrage."""
        return {
            "avg_opportunities_per_scan": 2,
            "avg_detection_time_seconds": 5,
            "typical_profit_range": [0.05, 1.0],  # Lower but more frequent profits
            "data_freshness_requirement_seconds": 30
        }


# Import required modules
from ..entities.opportunity import OpportunityStatus
