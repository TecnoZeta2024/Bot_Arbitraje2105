"""
Triangular Arbitrage Detection Strategy - Concrete implementation.
"""

import itertools
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ...utils.calculator import calcular_rentabilidad_triangular
from ...utils.logger import get_logger
from ..entities.market_data import MarketData
from ..entities.opportunity import Opportunity
from ..value_objects.currency import Currency
from ..value_objects.price import Price
from ..value_objects.profit_percentage import ProfitPercentage
from .detection_strategy import BaseDetectionStrategy, DetectionResult, DetectionType


class TriangularArbitrageStrategy(BaseDetectionStrategy):
    """
    Concrete implementation of triangular arbitrage detection strategy.
    
    Detects opportunities where three currencies form a profitable cycle:
    Currency A -> Currency B -> Currency C -> Currency A
    """
    
    def __init__(self):
        super().__init__(
            name="Triangular Arbitrage",
            description="Detects triangular arbitrage opportunities within a single exchange",
            detection_type=DetectionType.TRIANGULAR_ARBITRAGE
        )
        self._logger = get_logger(self.__class__.__name__)
    
    async def detect_opportunities(
        self, 
        market_data: List[MarketData],
        parameters: Optional[Dict[str, Any]] = None
    ) -> DetectionResult:
        """Detect triangular arbitrage opportunities."""
        start_time = time.time()
        self._logger.info("Starting triangular arbitrage detection")
        
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
        
        # Extract currencies and create pair lookup
        currencies = self._extract_unique_currencies(market_data)
        pair_lookup = self._create_pair_lookup(market_data)
        
        self._logger.info(f"Analyzing {len(currencies)} currencies, {len(pair_lookup)} pairs")
        
        # Find triangular opportunities
        opportunities = []
        stats = {
            "total_combinations": 0,
            "valid_triangles": 0,
            "opportunities_found": 0
        }
        
        for coin_a, coin_b, coin_c in itertools.combinations(currencies, 3):
            stats["total_combinations"] += 1
            
            # Find required pairs
            pair_ab = self._find_pair(coin_a, coin_b, pair_lookup)
            pair_bc = self._find_pair(coin_b, coin_c, pair_lookup)
            pair_ca = self._find_pair(coin_c, coin_a, pair_lookup)
            
            if not (pair_ab and pair_bc and pair_ca):
                continue
            
            stats["valid_triangles"] += 1
            
            # Calculate both possible cycles
            cycle_opportunities = self._calculate_triangular_cycles(
                coin_a, coin_b, coin_c,
                pair_ab, pair_bc, pair_ca,
                pair_lookup
            )
            
            for opp in cycle_opportunities:
                if opp.estimated_profit_percentage.value >= self._parameters["profit_threshold_percentage"]:
                    opportunities.append(opp)
                    stats["opportunities_found"] += 1
        
        detection_time = time.time() - start_time
        self._logger.info(f"Detection completed in {detection_time:.2f}s: {len(opportunities)} opportunities")
        
        return self._create_detection_result(
            opportunities=opportunities,
            total_combinations_checked=stats["total_combinations"],
            valid_combinations=stats["valid_triangles"],
            opportunities_above_threshold=stats["opportunities_found"],
            detection_time_seconds=detection_time,
            symbols_analyzed=len(currencies),
            tickers_processed=len(pair_lookup),
            confidence_score=self._calculate_confidence_score(stats, market_data),
            data_quality_score=self._assess_market_data_quality(market_data)
        )
    
    def _extract_unique_currencies(self, market_data: List[MarketData]) -> List[str]:
        """Extract unique currencies from market data."""
        currencies = set()
        
        for md in market_data:
            if md.is_suitable_for_arbitrage():
                currencies.add(md.base_currency.symbol)
                currencies.add(md.quote_currency.symbol)
        
        currencies_list = list(currencies)
        
        # Limit for performance
        max_currencies = self._parameters.get("max_currencies", 100)
        if len(currencies_list) > max_currencies:
            # Prioritize major currencies
            major_currencies = ["BTC", "ETH", "BNB", "USDT", "USDC", "BUSD"]
            priority_currencies = [c for c in currencies_list if c in major_currencies]
            other_currencies = [c for c in currencies_list if c not in priority_currencies]
            
            remaining_slots = max_currencies - len(priority_currencies)
            if remaining_slots > 0:
                currencies_list = priority_currencies + other_currencies[:remaining_slots]
            else:
                currencies_list = priority_currencies[:max_currencies]
        
        return currencies_list
    
    def _create_pair_lookup(self, market_data: List[MarketData]) -> Dict[str, MarketData]:
        """Create lookup dictionary for trading pairs."""
        return {md.symbol: md for md in market_data if md.is_suitable_for_arbitrage()}
    
    def _find_pair(self, currency_a: str, currency_b: str, pair_lookup: Dict[str, MarketData]) -> Optional[str]:
        """Find trading pair between two currencies."""
        pair_1 = f"{currency_a}{currency_b}"
        pair_2 = f"{currency_b}{currency_a}"
        
        if pair_1 in pair_lookup:
            return pair_1
        elif pair_2 in pair_lookup:
            return pair_2
        else:
            return None
    
    def _calculate_triangular_cycles(
        self,
        coin_a: str, coin_b: str, coin_c: str,
        pair_ab: str, pair_bc: str, pair_ca: str,
        pair_lookup: Dict[str, MarketData]
    ) -> List[Opportunity]:
        """Calculate profitability for both possible triangular cycles."""
        opportunities = []
        
        # Get market data for pairs
        md_ab = pair_lookup[pair_ab]
        md_bc = pair_lookup[pair_bc]
        md_ca = pair_lookup[pair_ca]
        
        # Cycle 1: A -> B -> C -> A
        opp_1 = self._calculate_single_cycle(
            [coin_a, coin_b, coin_c, coin_a],
            [pair_ab, pair_bc, pair_ca],
            [md_ab, md_bc, md_ca]
        )
        if opp_1:
            opportunities.append(opp_1)
        
        # Cycle 2: A -> C -> B -> A  
        opp_2 = self._calculate_single_cycle(
            [coin_a, coin_c, coin_b, coin_a],
            [pair_ca, pair_bc, pair_ab],
            [md_ca, md_bc, md_ab]
        )
        if opp_2:
            opportunities.append(opp_2)
        
        return opportunities
    
    def _calculate_single_cycle(
        self,
        path: List[str],
        pairs: List[str],
        market_data: List[MarketData]
    ) -> Optional[Opportunity]:
        """Calculate profitability for a single triangular cycle."""
        try:
            # Calculate conversion factors
            factors = []
            for i, md in enumerate(market_data):
                from_currency = path[i]
                to_currency = path[i + 1]
                
                factor = self._get_conversion_factor(from_currency, to_currency, md)
                if factor is None:
                    return None
                factors.append(factor)
            
            # Calculate gross profit
            gross_multiplier = 1.0
            for factor in factors:
                gross_multiplier *= factor
            
            gross_profit_percentage = (gross_multiplier - 1) * 100
            
            # Skip unrealistic opportunities
            if gross_profit_percentage <= 0 or gross_profit_percentage > 50:
                return None
            
            # Calculate net profit with fees
            fee_percentages = [
                self._parameters.get("fee_percentage", 0.1),
                self._parameters.get("fee_percentage", 0.1),
                self._parameters.get("fee_percentage", 0.1)
            ]
            
            net_result = calcular_rentabilidad_triangular(
                precios=factors,
                volumes=[0, 0, 0],
                comisiones=fee_percentages
            )
            
            net_profit_percentage = net_result["rentabilidad_neta"]
            
            # Create opportunity entity
            return self._create_opportunity_entity(
                path, pairs, factors, net_profit_percentage
            )
            
        except Exception as e:
            self._logger.debug(f"Error calculating cycle: {e}")
            return None
    
    def _get_conversion_factor(
        self, 
        from_currency: str, 
        to_currency: str, 
        market_data: MarketData
    ) -> Optional[float]:
        """Get conversion factor between currencies using market data."""
        symbol = market_data.symbol
        price = float(market_data.price.amount)
        
        if symbol == f"{from_currency}{to_currency}":
            # Direct pair: FROM/TO
            return price
        elif symbol == f"{to_currency}{from_currency}":
            # Reverse pair: TO/FROM
            return 1 / price if price > 0 else None
        else:
            return None
    
    def _create_opportunity_entity(
        self,
        path: List[str],
        pairs: List[str], 
        factors: List[float],
        net_profit_percentage: float
    ) -> Opportunity:
        """Create Opportunity entity from calculation results."""
        import uuid
        from datetime import datetime, timedelta

        # Create currencies
        base_currency = Currency(path[0])
        intermediate_currency = Currency(path[1])
        quote_currency = Currency(path[2])
        
        # Use default capital from parameters
        capital = Decimal(str(self._parameters.get("default_capital", 100.0)))
        
        # Calculate expected profit
        expected_profit = capital * Decimal(str(net_profit_percentage)) / 100
        
        # Create price objects (simplified - using base currency)
        price_currency = base_currency
        first_price = Price(Decimal(str(factors[0])), price_currency)
        second_price = Price(Decimal(str(factors[1])), price_currency)
        third_price = Price(Decimal(str(factors[2])), price_currency)
        
        return Opportunity(
            opportunity_id=str(uuid.uuid4()),
            base_currency=base_currency,
            intermediate_currency=intermediate_currency,
            quote_currency=quote_currency,
            estimated_profit_percentage=ProfitPercentage(net_profit_percentage),
            required_capital=capital,
            expected_profit=expected_profit,
            first_pair_price=first_price,
            second_pair_price=second_price,
            third_pair_price=third_price,
            detection_timestamp=datetime.utcnow(),
            status=OpportunityStatus.DETECTED,
            expiry_timestamp=datetime.utcnow() + timedelta(
                seconds=self._parameters.get("opportunity_ttl_seconds", 300)
            ),
            confidence_score=0.8,
            risk_score=0.3
        )
    
    def _calculate_confidence_score(
        self, 
        stats: Dict[str, int], 
        market_data: List[MarketData]
    ) -> float:
        """Calculate confidence score for the detection results."""
        base_score = 0.8
        
        # Adjust based on data quality
        data_quality = self._assess_market_data_quality(market_data)
        
        # Adjust based on detection efficiency
        if stats["total_combinations"] > 0:
            efficiency = stats["valid_triangles"] / stats["total_combinations"]
            if efficiency > 0.1:
                base_score += 0.1
            elif efficiency < 0.01:
                base_score -= 0.2
        
        # Adjust based on opportunity density
        if stats["valid_triangles"] > 0:
            opportunity_density = stats["opportunities_found"] / stats["valid_triangles"]
            if opportunity_density > 0.05:
                base_score += 0.1
        
        return max(0.0, min(1.0, base_score * data_quality))
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for triangular arbitrage strategy."""
        return {
            "profit_threshold_percentage": 0.1,
            "max_capital_per_opportunity": 1000.0,
            "max_data_age_seconds": 60,
            "min_liquidity_usd": 100000.0,
            "fee_percentage": 0.1,
            "max_currencies": 100,
            "default_capital": 100.0,
            "opportunity_ttl_seconds": 300
        }
    
    def get_min_market_data_requirements(self) -> Dict[str, Any]:
        """Get minimum requirements for triangular arbitrage."""
        return {
            "min_symbols": 20,  # Need enough pairs to form triangles
            "min_liquidity_usd": 100000,
            "max_spread_percentage": 0.5,
            "max_data_age_seconds": 60
        }


# Import required modules
from ..entities.opportunity import OpportunityStatus
