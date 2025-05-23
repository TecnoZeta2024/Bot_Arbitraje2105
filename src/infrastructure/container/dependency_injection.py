"""
Dependency Injection Container for the Triangular Arbitrage Bot.
Centralizes all dependency configuration and wiring.
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from ...utils.config import settings
from ...utils.logger import get_logger
from ..database.market_data_repository_impl import MarketDataRepositoryImpl
from ..database.operation_repository_impl import OperationRepositoryImpl
from ..database.opportunity_repository_impl import OpportunityRepositoryImpl
from ..database.trading_pair_repository_impl import TradingPairRepositoryImpl
from ..external_apis.binance_client import BinanceClient
from ..external_apis.gemini_client import GeminiClient
from ..external_apis.mobula_client import MobulaClient
from ..external_apis.supabase_client import SupabaseClient


class Container(containers.DeclarativeContainer):
    """
    Main dependency injection container.
    
    Configures all dependencies following the Dependency Inversion Principle.
    Domain layer depends on abstractions, infrastructure provides implementations.
    """
    
    # Configuration
    config = providers.Object(settings)
    
    # Logging
    logger = providers.Singleton(get_logger, "container")
    
    # External API Clients (Infrastructure Layer)
    binance_client = providers.Singleton(
        BinanceClient,
        api_key=config.binance_api_key,
        api_secret=config.binance_api_secret,
        testnet=config.binance_testnet
    )
    
    supabase_client = providers.Singleton(
        SupabaseClient,
        url=config.provided.supabase_url,
        key=config.provided.supabase_key
    )
    
    mobula_client = providers.Singleton(
        MobulaClient,
        api_key=config.mobula_api_key
    )
    
    gemini_client = providers.Singleton(
        GeminiClient,
        api_key=config.provided.gemini_api_key
    )
    
    # Repository Implementations (Infrastructure Layer)
    opportunity_repository = providers.Singleton(
        OpportunityRepositoryImpl,
        supabase_client=supabase_client
    )
    
    operation_repository = providers.Singleton(
        OperationRepositoryImpl,
        supabase_client=supabase_client
    )
    
    market_data_repository = providers.Singleton(
        MarketDataRepositoryImpl,
        supabase_client=supabase_client
    )
    
    trading_pair_repository = providers.Singleton(
        TradingPairRepositoryImpl,
        binance_client=binance_client,
        supabase_client=supabase_client
    )


class ApplicationContainer(containers.DeclarativeContainer):
    """
    Application layer container.
    
    Contains use cases and application services.
    """
    
    # Import base container
    infrastructure = providers.DependenciesContainer()
    
    # Use Cases will be added here
    # Application Services will be added here


# Global container instance
container = Container()
app_container = ApplicationContainer()
app_container.infrastructure.override(container)


def wire_container():
    """Wire the container to enable dependency injection."""
    container.wire(modules=[
        "src.core.detectar_oportunidades",
        "src.core.ejecutar_ciclo", 
        "src.core.api_server",
        "src.application.services",
        "src.application.use_cases"
    ])


def unwire_container():
    """Unwire the container (useful for testing)."""
    container.unwire()


# Dependency injection decorators for easy use
def inject_binance_client(func):
    """Decorator to inject Binance client."""
    return inject(func)


def inject_opportunity_repository(func):
    """Decorator to inject opportunity repository."""
    return inject(func)


def inject_operation_repository(func):
    """Decorator to inject operation repository."""
    return inject(func)


# Context manager for dependency injection
class DIContext:
    """Context manager for dependency injection setup and teardown."""
    
    def __enter__(self):
        wire_container()
        return container
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        unwire_container()
