"""
OpportunityFinder - Single responsibility for finding arbitrage opportunities.
"""

from typing import List, Dict, Tuple, Optional
import itertools
from decimal import Decimal

from ...domain.entities.opportunity import Opportunity
from ...domain.value_objects.currency import Currency
from ...domain.value_objects.price import Price
from ...domain.value_objects.profit_percentage import ProfitPercentage
from ...utils.calculator import calcular_rentabilidad_triangular
from ...utils.logger import get_logger


class OpportunityFinder:
    """
    Responsible ONLY for finding triangular arbitrage opportunities.
    
    Applies Single Responsibility Principle - this class has only one reason to change:
    when the algorithm for finding opportunities changes.
    """
    
    def __init__(self):
        self._logger = get_logger(self.__class__.__name__)
        
        # Configuration for currency parsing
        self._common_quotes = [
            "USDT", "BUSD", "USDC", "DAI", "TUSD", "FDUSD", "BTC", "ETH", "BNB", 
            "XRP", "SOL", "DOGE", "TRX", "DOT", "MATIC", "AVAX", "SHIB", "LINK", 
            "UNI", "ADA", "WETH", "WBTC", "EUR", "USD", "RUB", "GBP", "JPY", 
            "AUD", "CAD", "CHF"
        ]
        
        self._common_bases = [
            "BTC", "ETH", "BNB", "XRP", "SOL", "DOGE", "TRX", "DOT", "MATIC", 
            "AVAX", "SHIB", "LINK", "UNI", "ADA", "LTC", "ETC", "ATOM", "ALGO", 
            "VET", "NEAR"
        ]
    
    def find_opportunities(
        self, 
        symbols: List[str], 
        tickers: Dict[str, float],
        profit_threshold: float,
        capital: float,
        fee_percentages: List[float] = None
    ) -> List[Opportunity]:
        """
        Find triangular arbitrage opportunities.
        
        Args:
            symbols: List of available trading symbols
            tickers: Dictionary mapping symbols to prices
            profit_threshold: Minimum profit percentage threshold
            capital: Initial capital amount
            fee_percentages: List of fee percentages per trade
            
        Returns:
            List of opportunities found
        """
        self._logger.info("=== FINDING TRIANGULAR ARBITRAGE OPPORTUNITIES ===")
        self._logger.info(f"Parameters: threshold={profit_threshold}%, capital={capital}")
        
        if fee_percentages is None:
            fee_percentages = [0.1, 0.1, 0.1]  # Default 0.1% per trade
        
        # Extract currencies from symbols
        currencies = self._extract_currencies_from_symbols(symbols, tickers)
        if len(currencies) < 3:
            self._logger.warning(f"Insufficient currencies extracted: {len(currencies)}")
            return []
        
        self._logger.info(f"Extracted {len(currencies)} unique currencies")
        
        # Create lookup for available pairs
        available_pairs = self._create_pair_lookup(tickers)
        self._logger.info(f"Available trading pairs: {len(available_pairs)}")
        
        # Find triangular opportunities
        opportunities = self._find_triangular_cycles(
            currencies, 
            available_pairs, 
            profit_threshold, 
            capital, 
            fee_percentages
        )
        
        self._logger.info(f"Found {len(opportunities)} opportunities above threshold")
        return opportunities
    
    def _extract_currencies_from_symbols(
        self, 
        symbols: List[str], 
        tickers: Dict[str, float]
    ) -> List[str]:
        """Extract unique currencies from trading symbols."""
        currencies = set()
        
        # Use symbols that have valid tickers
        valid_symbols = [s for s in symbols if s in tickers and tickers[s] > 0]
        
        # If we have few valid symbols, use all tickers
        if len(valid_symbols) < 50:
            valid_symbols = [s for s, price in tickers.items() if price > 0]
        
        self._logger.info(f"Processing {len(valid_symbols)} valid symbols for currency extraction")
        
        parsed_count = 0
        failed_count = 0
        
        for symbol in valid_symbols:
            base, quote = self._parse_trading_pair(symbol)
            if base and quote:
                currencies.add(base)
                currencies.add(quote)
                parsed_count += 1
            else:
                failed_count += 1
                if failed_count <= 5:  # Log first few failures
                    self._logger.debug(f"Failed to parse symbol: {symbol}")
        
        self._logger.info(f"Parsed {parsed_count} symbols, failed {failed_count}")
        
        currencies = list(currencies)
        
        # Limit currencies for performance (prioritize known currencies)
        max_currencies = 100
        if len(currencies) > max_currencies:
            priority_currencies = [c for c in currencies if c in self._common_bases + self._common_quotes]
            remaining_currencies = [c for c in currencies if c not in priority_currencies]
            
            remaining_slots = max_currencies - len(priority_currencies)
            if remaining_slots > 0:
                currencies = priority_currencies + remaining_currencies[:remaining_slots]
            else:
                currencies = priority_currencies[:max_currencies]
            
            self._logger.info(f"Limited to {len(currencies)} currencies for performance")
        
        return currencies
    
    def _parse_trading_pair(self, symbol: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse a trading symbol into base and quote currencies."""
        # Try common quote currencies first (more reliable)
        for quote in self._common_quotes:
            if symbol.endswith(quote) and len(symbol) > len(quote):
                base = symbol[:-len(quote)]
                if len(base) >= 2:  # Minimum base currency length
                    return base, quote
        
        # Try common base currencies
        for base in self._common_bases:
            if symbol.startswith(base) and len(symbol) > len(base):
                quote = symbol[len(base):]
                if len(quote) >= 2:  # Minimum quote currency length
                    return base, quote
        
        # Fallback: try to split in the middle for medium-length symbols
        if 6 <= len(symbol) <= 8:
            mid = len(symbol) // 2
            base = symbol[:mid]
            quote = symbol[mid:]
            
            # Validate split makes sense
            if (base in self._common_bases or quote in self._common_quotes or
                len(base) >= 3 and len(quote) >= 3):
                return base, quote
        
        return None, None
    
    def _create_pair_lookup(self, tickers: Dict[str, float]) -> Dict[str, float]:
        """Create lookup dictionary for available pairs with valid prices."""
        return {symbol: price for symbol, price in tickers.items() if price > 0}
    
    def _find_triangular_cycles(
        self,
        currencies: List[str],
        available_pairs: Dict[str, float],
        profit_threshold: float,
        capital: float,
        fee_percentages: List[float]
    ) -> List[Opportunity]:
        """Find all valid triangular arbitrage cycles."""
        opportunities = []
        
        total_combinations = 0
        valid_triangles = 0
        profitable_opportunities = 0
        
        self._logger.info(f"Searching triangular cycles among {len(currencies)} currencies")
        
        # Check all combinations of 3 currencies
        for coin_a, coin_b, coin_c in itertools.combinations(currencies, 3):
            total_combinations += 1
            
            # Progress logging for large searches
            if total_combinations % 100000 == 0:
                self._logger.info(f"Progress: {total_combinations} combinations checked")
            
            # Find pairs for the triangle
            pair_ab = self._find_pair(coin_a, coin_b, available_pairs)
            pair_bc = self._find_pair(coin_b, coin_c, available_pairs)
            pair_ca = self._find_pair(coin_c, coin_a, available_pairs)
            
            if not (pair_ab and pair_bc and pair_ca):
                continue
            
            valid_triangles += 1
            
            # Calculate both possible cycles
            cycle_1 = self._calculate_cycle_profitability(
                coin_a, coin_b, coin_c,
                pair_ab, pair_bc, pair_ca,
                available_pairs, capital, fee_percentages
            )
            
            cycle_2 = self._calculate_cycle_profitability(
                coin_a, coin_c, coin_b,
                pair_ca, pair_bc, pair_ab,
                available_pairs, capital, fee_percentages
            )
            
            # Check if cycles meet profit threshold
            for cycle_data in [cycle_1, cycle_2]:
                if cycle_data and cycle_data["net_profit_percentage"] > profit_threshold:
                    opportunity = self._create_opportunity_from_cycle(cycle_data, capital)
                    opportunities.append(opportunity)
                    profitable_opportunities += 1
        
        self._logger.info(f"Search complete: {total_combinations} combinations, "
                         f"{valid_triangles} valid triangles, "
                         f"{profitable_opportunities} profitable opportunities")
        
        return opportunities
    
    def _find_pair(self, currency_a: str, currency_b: str, available_pairs: Dict[str, float]) -> Optional[str]:
        """Find trading pair between two currencies."""
        pair_1 = f"{currency_a}{currency_b}"
        pair_2 = f"{currency_b}{currency_a}"
        
        if pair_1 in available_pairs:
            return pair_1
        elif pair_2 in available_pairs:
            return pair_2
        else:
            return None
    
    def _calculate_cycle_profitability(
        self,
        start_currency: str,
        intermediate_currency: str,
        end_currency: str,
        pair_1: str,
        pair_2: str,
        pair_3: str,
        available_pairs: Dict[str, float],
        capital: float,
        fee_percentages: List[float]
    ) -> Optional[Dict]:
        """Calculate profitability for a specific trading cycle."""
        try:
            # Get prices
            price_1 = available_pairs[pair_1]
            price_2 = available_pairs[pair_2]
            price_3 = available_pairs[pair_3]
            
            # Calculate conversion factors for the cycle
            factor_1 = self._get_conversion_factor(start_currency, intermediate_currency, pair_1, price_1)
            factor_2 = self._get_conversion_factor(intermediate_currency, end_currency, pair_2, price_2)
            factor_3 = self._get_conversion_factor(end_currency, start_currency, pair_3, price_3)
            
            if not all([factor_1, factor_2, factor_3]):
                return None
            
            # Calculate gross profit
            gross_multiplier = factor_1 * factor_2 * factor_3
            gross_profit_percentage = (gross_multiplier - 1) * 100
            
            # Skip obviously unprofitable or unrealistic opportunities
            if gross_profit_percentage <= 0 or gross_profit_percentage > 50:  # Cap at 50%
                return None
            
            # Calculate net profit using existing calculator
            net_result = calcular_rentabilidad_triangular(
                precios=[factor_1, factor_2, factor_3],
                volumes=[0, 0, 0],  # Not used in current implementation
                comisiones=fee_percentages
            )
            
            net_profit_percentage = net_result["rentabilidad_neta"]
            
            return {
                "start_currency": start_currency,
                "intermediate_currency": intermediate_currency,
                "end_currency": end_currency,
                "trading_path": [start_currency, intermediate_currency, end_currency, start_currency],
                "pairs": [pair_1, pair_2, pair_3],
                "prices": [price_1, price_2, price_3],
                "factors": [factor_1, factor_2, factor_3],
                "gross_profit_percentage": gross_profit_percentage,
                "net_profit_percentage": net_profit_percentage,
                "gross_multiplier": gross_multiplier
            }
            
        except Exception as e:
            self._logger.debug(f"Error calculating cycle profitability: {e}")
            return None
    
    def _get_conversion_factor(
        self, 
        from_currency: str, 
        to_currency: str, 
        pair: str, 
        price: float
    ) -> Optional[float]:
        """Get conversion factor for currency pair."""
        if pair == f"{from_currency}{to_currency}":
            # Direct pair: FROM/TO, so 1 FROM = price TO
            return price
        elif pair == f"{to_currency}{from_currency}":
            # Reverse pair: TO/FROM, so 1 FROM = 1/price TO
            return 1 / price if price > 0 else None
        else:
            # Pair doesn't match currencies
            return None
    
    def _create_opportunity_from_cycle(self, cycle_data: Dict, capital: float) -> Opportunity:
        """Create an Opportunity entity from cycle calculation data."""
        import uuid
        from datetime import datetime, timedelta
        
        # Create currencies
        base_currency = Currency(cycle_data["start_currency"])
        intermediate_currency = Currency(cycle_data["intermediate_currency"])
        quote_currency = Currency(cycle_data["end_currency"])
        
        # Create prices (using first price as reference currency)
        price_currency = base_currency  # Simplified assumption
        first_price = Price(Decimal(str(cycle_data["prices"][0])), price_currency)
        second_price = Price(Decimal(str(cycle_data["prices"][1])), price_currency)
        third_price = Price(Decimal(str(cycle_data["prices"][2])), price_currency)
        
        # Calculate expected profit
        expected_profit = Decimal(str(capital)) * Decimal(str(cycle_data["net_profit_percentage"])) / 100
        
        return Opportunity(
            opportunity_id=str(uuid.uuid4()),
            base_currency=base_currency,
            intermediate_currency=intermediate_currency,
            quote_currency=quote_currency,
            estimated_profit_percentage=ProfitPercentage(cycle_data["net_profit_percentage"]),
            required_capital=Decimal(str(capital)),
            expected_profit=expected_profit,
            first_pair_price=first_price,
            second_pair_price=second_price,
            third_pair_price=third_price,
            detection_timestamp=datetime.utcnow(),
            status=OpportunityStatus.DETECTED,
            expiry_timestamp=datetime.utcnow() + timedelta(hours=1),  # 1 hour expiry
            confidence_score=0.8,  # Default confidence
            risk_score=0.3  # Default risk
        )


# Import required modules
from ...domain.entities.opportunity import OpportunityStatus
