"""
Orchestration service for opportunity detection - Refactored with SRP.
"""

import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.infrastructure.external_apis.binance_client import BinanceClient, binance_data_client
from src.infrastructure.external_apis.mobula_client import MobulaClient
from src.domain.services.market_data_fetcher import MarketDataFetcher
from src.domain.services.opportunity_finder import OpportunityFinder
from src.domain.services.cache_manager import CacheManager
from src.utils.config import settings
from src.utils.logger import get_logger
from src.core.telegram.telegram_handler import telegram_handler
from src.infrastructure.external_apis.supabase_client import SupabaseClient

logger = get_logger("deteccion")

"""
Módulo refactorizado para detectar oportunidades de arbitraje triangular.
Aplica Single Responsibility Principle - cada clase tiene una responsabilidad específica.
"""


class OpportunityDetectionOrchestrator:
    """
    Orchestrates the opportunity detection process.
    
    This class coordinates different services but doesn't implement the business logic itself.
    Follows the Single Responsibility Principle - only responsible for orchestration.
    """
    
    def __init__(
        self,
        binance_client: BinanceClient,
        mobula_client: MobulaClient,
        cache_dir: str = "./cache"
    ):
        self._binance_client = binance_client
        self._mobula_client = mobula_client
        
        # Initialize specialized services (SRP applied)
        self._market_data_fetcher = MarketDataFetcher(binance_client, mobula_client)
        self._opportunity_finder = OpportunityFinder()
        self._cache_manager = CacheManager(cache_dir)
        
        self._logger = get_logger(self.__class__.__name__)
    
    async def detect_opportunities(
        self,
        webhook_url: Optional[str] = None,
        use_cache: bool = False,
        cache_filepath: Optional[str] = None,
        cache_dir: str = "./cache"
    ) -> List[Dict[str, Any]]:
        """
        Main orchestration method for opportunity detection.
        
        Args:
            webhook_url: URL to send opportunities to
            use_cache: Whether to use cached data
            cache_filepath: Specific cache file to use
            cache_dir: Cache directory path
            
        Returns:
            List of opportunities found
        """
        start_time = time.time()
        self._logger.info("=== STARTING OPPORTUNITY DETECTION ORCHESTRATION ===")
        
        try:
            # Validate configuration
            profit_threshold, initial_capital = self._get_configuration()
            
            # Get market data (using cache or fresh fetch)
            symbols, tickers = await self._get_market_data(use_cache, cache_filepath)
            
            if not symbols or not tickers:
                self._logger.error("Failed to obtain market data")
                return []
            
            # Find opportunities using specialized service
            opportunities = self._opportunity_finder.find_opportunities(
                symbols=symbols,
                tickers=tickers,
                profit_threshold=profit_threshold,
                capital=initial_capital
            )
            
            # Process and send opportunities
            if opportunities:
                await self._process_opportunities(opportunities, webhook_url)
            else:
                self._logger.info(f"No opportunities found above {profit_threshold}% threshold")
            
            # Convert to legacy format for backward compatibility
            legacy_opportunities = [self._convert_to_legacy_format(opp) for opp in opportunities]
            
            execution_time = time.time() - start_time
            self._logger.info(f"=== DETECTION COMPLETED IN {execution_time:.2f} SECONDS ===")
            
            return legacy_opportunities
            
        except Exception as e:
            self._logger.error(f"Error in opportunity detection orchestration: {e}", exc_info=True)
            return []
    
    def _get_configuration(self) -> tuple[float, float]:
        """Get and validate configuration parameters."""
        try:
            profit_threshold = settings.umbral_rentabilidad
            initial_capital = settings.capital_inicial
            
            # Validate configuration
            if not isinstance(profit_threshold, (int, float)) or profit_threshold <= 0:
                self._logger.warning(f"Invalid profit threshold: {profit_threshold}. Using default: 1.0%")
                profit_threshold = 1.0
                
            if not isinstance(initial_capital, (int, float)) or initial_capital <= 0:
                self._logger.warning(f"Invalid initial capital: {initial_capital}. Using default: 100")
                initial_capital = 100.0
            
            self._logger.info(f"Configuration: Threshold={profit_threshold}%, Capital={initial_capital}")
            return profit_threshold, initial_capital
            
        except AttributeError as e:
            self._logger.error(f"Configuration error: {e}. Using defaults.")
            return 1.0, 100.0
    
    async def _get_market_data(
        self, 
        use_cache: bool, 
        cache_filepath: Optional[str]
    ) -> tuple[List[str], Dict[str, float]]:
        """Get market data from cache or fresh fetch."""
        symbols = []
        tickers = {}
        
        if use_cache or cache_filepath:
            symbols, tickers = self._load_from_cache(cache_filepath)
            
            if symbols and tickers:
                self._logger.info("Using cached market data")
                return symbols, tickers
            else:
                self._logger.info("Cache load failed or empty, fetching fresh data")
        
        # Fetch fresh data
        symbols, tickers = await self._market_data_fetcher.fetch_symbols_and_tickers(
            token_search_limit=settings.max_tokens_considerados,
            prefer_mobula=True
        )
        
        # Save to cache if successful
        if symbols and tickers:
            try:
                self._cache_manager.save_market_data(symbols, tickers, {
                    "source": "fresh_fetch",
                    "fetch_time": datetime.now().isoformat()
                })
            except Exception as e:
                self._logger.warning(f"Failed to save to cache: {e}")
        
        return symbols, tickers
    
    def _load_from_cache(self, cache_filepath: Optional[str]) -> tuple[List[str], Dict[str, float]]:
        """Load market data from cache."""
        try:
            if cache_filepath:
                return self._cache_manager.load_cache_file(cache_filepath)
            else:
                return self._cache_manager.load_latest_market_data()
        except Exception as e:
            self._logger.error(f"Error loading from cache: {e}")
            return [], {}
    
    async def _process_opportunities(
        self, 
        opportunities: List, 
        webhook_url: Optional[str]
    ) -> None:
        """Process found opportunities."""
        self._logger.info(f"Processing {len(opportunities)} opportunities")
        
        # Log to Supabase and send Telegram notifications
        for opportunity in opportunities:
            try:
                # Convert to DTO format for compatibility
                opportunity_data = self._convert_to_legacy_format(opportunity)
                
                # Log to Supabase
                supabase_client = SupabaseClient()
                supabase_client.insertar_oportunidad(opportunity_data)
                
                # Send Telegram notification and request confirmation
                telegram_handler.notify_and_request_confirmation(opportunity_data)
                
                self._logger.info(f"Processed opportunity {opportunity.opportunity_id}")
                
            except Exception as e:
                self._logger.error(f"Error processing opportunity: {e}")
    
    def _convert_to_legacy_format(self, opportunity) -> Dict[str, Any]:
        """Convert new Opportunity entity to legacy format for backward compatibility."""
        return {
            "opportunity_id": opportunity.opportunity_id,
            "cycle": f"{opportunity.base_currency.symbol} -> {opportunity.intermediate_currency.symbol} -> {opportunity.quote_currency.symbol} -> {opportunity.base_currency.symbol}",
            "profit_percentage_gross": float(opportunity.estimated_profit_percentage.value),
            "profit_percentage_net": float(opportunity.estimated_profit_percentage.value),  # Simplified
            "steps": self._convert_steps_to_legacy(opportunity),
            "capital_inicial": float(opportunity.required_capital),
            "capital_sugerido": float(opportunity.required_capital),
            "ruta": [opportunity.base_currency.symbol, opportunity.intermediate_currency.symbol, 
                    opportunity.quote_currency.symbol, opportunity.base_currency.symbol],
            "pares_comercio": opportunity.get_required_pairs(),
            "rentabilidad_teorica": float(opportunity.estimated_profit_percentage.value),
            "fecha_deteccion": opportunity.detection_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _convert_steps_to_legacy(self, opportunity) -> List[Dict[str, Any]]:
        """Convert opportunity to legacy steps format."""
        pairs = opportunity.get_required_pairs()
        path = opportunity.get_trading_path()
        
        steps = []
        for i, pair in enumerate(pairs):
            if i < len(path) - 1:
                steps.append({
                    "order": i + 1,
                    "from_coin": path[i],
                    "to_coin": path[i + 1],
                    "pair": pair,
                    "amount_in": float(opportunity.required_capital) if i == 0 else 0  # Simplified
                })
        
        return steps


# Legacy functions for backward compatibility
def verificar_modulo_deteccion(binance_client: BinanceClient) -> Dict[str, Any]:
    """
    Legacy function - delegates to the orchestrator's validation logic.
    """
    try:
        # Simple validation using existing client
        binance_markets = binance_client.get_markets()
        
        if not binance_markets or len(binance_markets) == 0:
            return {
                "success": False,
                "message": "No se pudieron obtener los mercados de Binance",
                "details": {"markets_count": 0}
            }
        
        if len(binance_markets) < 100:
            return {
                "success": False,
                "message": f"Insuficientes mercados en Binance ({len(binance_markets)}). Se requieren al menos 100.",
                "details": {"markets_count": len(binance_markets)}
            }
        
        tickers = binance_client.get_tickers()
        if not tickers or len(tickers) == 0:
            return {
                "success": False,
                "message": "No se pudieron obtener los tickers de Binance",
                "details": {"tickers_count": 0}
            }
        
        return {
            "success": True,
            "message": "Módulo de detección correctamente configurado",
            "details": {
                "markets_count": len(binance_markets),
                "tickers_count": len(tickers)
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al verificar el módulo de detección: {str(e)}",
            "details": {"error": str(e)}
        }


async def ejecutar_deteccion(
    binance_client: BinanceClient, 
    mobula_client: MobulaClient, 
    webhook_url: Optional[str] = None,
    use_cache: bool = False,
    cache_filepath: Optional[str] = None,
    cache_dir: str = "./cache"
) -> List[Dict[str, Any]]:
    """
    Legacy function that uses the new orchestrator.
    
    Main entry point for opportunity detection with refactored architecture.
    """
    orchestrator = OpportunityDetectionOrchestrator(
        binance_client=binance_client,
        mobula_client=mobula_client,
        cache_dir=cache_dir
    )
    
    return await orchestrator.detect_opportunities(
        webhook_url=webhook_url,
        use_cache=use_cache,
        cache_filepath=cache_filepath,
        cache_dir=cache_dir
    )


# Additional legacy functions for compatibility
def fetch_market_data(
    binance_client: BinanceClient, 
    mobula_client: MobulaClient, 
    token_search_limit: int = 400,
    use_cache: bool = False,
    cache_dir: str = "./cache"
) -> tuple[List[str], Dict[str, float]]:
    """Legacy wrapper for market data fetching."""
    import asyncio
    
    async def _fetch():
        fetcher = MarketDataFetcher(binance_client, mobula_client)
        return await fetcher.fetch_symbols_and_tickers(token_search_limit, prefer_mobula=True)
    
    return asyncio.run(_fetch())


def find_opportunities(
    symbols: List[str], 
    tickers: Dict[str, float], 
    umbral_rentabilidad: float, 
    capital_inicial: float, 
    fees_percentage: List[float] = None
) -> List[Dict[str, Any]]:
    """Legacy wrapper for opportunity finding."""
    finder = OpportunityFinder()
    opportunities = finder.find_opportunities(
        symbols=symbols,
        tickers=tickers,
        profit_threshold=umbral_rentabilidad,
        capital=capital_inicial,
        fee_percentages=fees_percentage
    )
    
    # Convert to legacy format
    orchestrator = OpportunityDetectionOrchestrator(None, None)  # Dummy orchestrator for conversion
    return [orchestrator._convert_to_legacy_format(opp) for opp in opportunities]


# Cache management functions
def save_market_data_to_cache(symbols: List[str], tickers: Dict[str, float], cache_dir: str = "./cache") -> str:
    """Legacy wrapper for cache saving."""
    cache_manager = CacheManager(cache_dir)
    return cache_manager.save_market_data(symbols, tickers)


def load_market_data_from_cache(cache_dir: str = "./cache") -> tuple[Optional[List[str]], Optional[Dict[str, float]]]:
    """Legacy wrapper for cache loading."""
    cache_manager = CacheManager(cache_dir)
    return cache_manager.load_latest_market_data()


def list_available_cache_files(cache_dir: str = "./cache") -> List[Dict[str, Any]]:
    """Legacy wrapper for listing cache files."""
    cache_manager = CacheManager(cache_dir)
    return cache_manager.list_cache_files()


def load_specific_cache_file(filepath: str) -> tuple[Optional[List[str]], Optional[Dict[str, float]]]:
    """Legacy wrapper for loading specific cache file."""
    cache_manager = CacheManager()
    return cache_manager.load_cache_file(filepath)


# Main execution for backward compatibility
if __name__ == "__main__":
    logger.info("Iniciando script de detección de oportunidades...")
    binance_client_instance = BinanceClient()
    mobula_client_instance = MobulaClient()
    
    import asyncio
    
    if settings.n8n_webhook_oportunidad:
        asyncio.run(ejecutar_deteccion(
            binance_client_instance,
            mobula_client_instance,
            webhook_url=settings.n8n_webhook_oportunidad
        ))
    else:
        asyncio.run(ejecutar_deteccion(binance_client_instance, mobula_client_instance))
    
    logger.info("Script de detección de oportunidades finalizado.")
