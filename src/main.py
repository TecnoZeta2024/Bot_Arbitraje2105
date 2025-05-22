"""
Main application entry point
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .application.services.trading_engine import TradingEngine, TradingEngineConfig
from .domain.trading_signals.trading_signal import StrategyType
from .infrastructure.websockets.websocket_manager import ExchangeType


def setup_logging():
    """Setup comprehensive logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/trading_engine.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set specific log levels for different components
    logging.getLogger("websocket").setLevel(logging.INFO)
    logging.getLogger("ai.gemini").setLevel(logging.INFO)
    logging.getLogger("strategy").setLevel(logging.INFO)
    logging.getLogger("risk").setLevel(logging.INFO)
    logging.getLogger("trading.engine").setLevel(logging.INFO)


def create_trading_config() -> TradingEngineConfig:
    """Create trading engine configuration from environment variables"""
    config = TradingEngineConfig()
    
    # Get configuration from environment
    config.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
    
    # Capital configuration
    initial_capital = os.getenv('INITIAL_CAPITAL', '10000')
    config.initial_capital = Decimal(initial_capital)
    
    # Trading symbols (comma-separated)
    symbols = os.getenv('TRADING_SYMBOLS', 'BTCUSDT,ETHUSDT,ADAUSDT,DOTUSDT,LINKUSDT')
    config.trading_symbols = [s.strip() for s in symbols.split(',')]
    
    # Strategy configuration
    enabled_strategies = os.getenv('ENABLED_STRATEGIES', 'scalping,day_trading')
    strategy_mapping = {
        'scalping': StrategyType.SCALPING,
        'day_trading': StrategyType.DAY_TRADING,
        'triangular_arbitrage': StrategyType.TRIANGULAR_ARBITRAGE
    }
    
    config.enabled_strategies = [
        strategy_mapping[s.strip().lower()] 
        for s in enabled_strategies.split(',')
        if s.strip().lower() in strategy_mapping
    ]
    
    # Exchange configuration
    enabled_exchanges = os.getenv('ENABLED_EXCHANGES', 'binance')
    exchange_mapping = {
        'binance': ExchangeType.BINANCE,
        'coinbase': ExchangeType.COINBASE,
        'kraken': ExchangeType.KRAKEN
    }
    
    config.enabled_exchanges = [
        exchange_mapping[e.strip().lower()]
        for e in enabled_exchanges.split(',')
        if e.strip().lower() in exchange_mapping
    ]
    
    # Risk management
    config.risk_params.max_daily_loss = Decimal(os.getenv('MAX_DAILY_LOSS', '0.02'))
    config.risk_params.max_position_size = Decimal(os.getenv('MAX_POSITION_SIZE', '0.05'))
    config.risk_params.max_concurrent_positions = int(os.getenv('MAX_CONCURRENT_POSITIONS', '8'))
    
    # AI configuration
    config.ai_enabled = os.getenv('AI_ENABLED', 'true').lower() == 'true'
    
    return config


async def main():
    """Main application entry point"""
    print("🚀 Starting Advanced Trading Application 🚀")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger("main")
    
    try:
        # Create configuration
        config = create_trading_config()
        
        # Validate configuration
        if config.ai_enabled and not config.gemini_api_key:
            logger.error("AI is enabled but GEMINI_API_KEY is not set")
            logger.info("Please set GEMINI_API_KEY environment variable")
            return
        
        if not config.trading_symbols:
            logger.error("No trading symbols configured")
            return
        
        if not config.enabled_strategies:
            logger.error("No trading strategies enabled")
            return
        
        if not config.enabled_exchanges:
            logger.error("No exchanges enabled")
            return
        
        # Log configuration
        logger.info(f"Initial Capital: ${config.initial_capital}")
        logger.info(f"Trading Symbols: {', '.join(config.trading_symbols)}")
        logger.info(f"Enabled Strategies: {', '.join([s.value for s in config.enabled_strategies])}")
        logger.info(f"Enabled Exchanges: {', '.join([e.value for e in config.enabled_exchanges])}")
        logger.info(f"AI Enabled: {config.ai_enabled}")
        
        # Create and start trading engine
        engine = TradingEngine(config)
        
        logger.info("Starting trading engine...")
        await engine.start_trading()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    asyncio.run(main())
