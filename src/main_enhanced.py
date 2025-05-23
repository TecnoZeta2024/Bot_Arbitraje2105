"""
Main application entry point - Enhanced Version
Production-ready trading application with full integrations
"""

import asyncio
import logging
import os
import sys
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv()

from application.services.enhanced_trading_engine import (
    EnhancedTradingEngine,
    EnhancedTradingEngineConfig,
)
from domain.trading_signals.trading_signal import StrategyType
from infrastructure.websockets.websocket_manager import ExchangeType


def setup_comprehensive_logging():
    """Setup comprehensive logging configuration for production"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure root logger
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
    logging.getLogger("database.supabase").setLevel(logging.INFO)
    logging.getLogger("notifications.telegram").setLevel(logging.INFO)
    logging.getLogger("api.mobula").setLevel(logging.INFO)
    
    # Suppress noisy external libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def create_enhanced_trading_config() -> EnhancedTradingEngineConfig:
    """Create enhanced trading engine configuration with validation"""
    config = EnhancedTradingEngineConfig()
    
    # Validate required configurations
    validation_errors = []
    
    if config.ai_enabled and not config.gemini_api_key:
        validation_errors.append("AI is enabled but GEMINI_API_KEY is not set")
    
    if not config.trading_symbols:
        validation_errors.append("No trading symbols configured")
    
    if not config.enabled_strategies:
        validation_errors.append("No trading strategies enabled")
    
    if not config.enabled_exchanges:
        validation_errors.append("No exchanges enabled")
    
    if ExchangeType.BINANCE in config.enabled_exchanges:
        if not config.binance_api_key or not config.binance_secret_key:
            validation_errors.append("Binance exchange enabled but API credentials missing")
    
    if validation_errors:
        for error in validation_errors:
            print(f"❌ Configuration Error: {error}")
        return None
    
    return config


def print_startup_banner():
    """Print startup banner with system information"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║        🚀 ADVANCED PERSONAL TRADING PLATFORM 2105 🚀                           ║
║                                                                                  ║
║        • Multi-Strategy Trading (Scalping + Day Trading)                        ║
║        • AI-Powered Analysis (Google Gemini)                                    ║
║        • Real-Time WebSocket Data                                               ║
║        • Institutional Risk Management                                          ║
║        • Database Persistence (Supabase)                                       ║
║        • Telegram Notifications                                                ║
║        • Enhanced Market Data (Mobula API)                                     ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
    """)


def print_configuration_summary(config: EnhancedTradingEngineConfig):
    """Print configuration summary"""
    print("📊 CONFIGURATION SUMMARY:")
    print("=" * 50)
    print(f"💰 Initial Capital: ${config.initial_capital}")
    print(f"📈 Trading Symbols: {', '.join(config.trading_symbols)}")
    print(f"🎯 Enabled Strategies: {', '.join([s.value for s in config.enabled_strategies])}")
    print(f"🏦 Enabled Exchanges: {', '.join([e.value for e in config.enabled_exchanges])}")
    print(f"🤖 AI Analysis: {'✅ Enabled' if config.ai_enabled else '❌ Disabled'}")
    print(f"📱 Telegram Notifications: {'✅ Enabled' if config.telegram_enabled else '❌ Disabled'}")
    print(f"💾 Database Logging: {'✅ Enabled' if config.database_enabled else '❌ Disabled'}")
    print(f"📊 Mobula API: {'✅ Enabled' if config.mobula_enabled else '❌ Disabled'}")
    print(f"🧪 Paper Trading: {'✅ Enabled' if config.paper_trading else '❌ Live Trading'}")
    print("=" * 50)


def print_integration_status(integrations_status: dict):
    """Print integration status"""
    print("\n🔗 INTEGRATION STATUS:")
    print("=" * 30)
    for service, status in integrations_status.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {service.title()}: {'Connected' if status else 'Failed'}")
    print("=" * 30)


async def run_system_checks():
    """Run comprehensive system checks before starting"""
    print("\n🔍 RUNNING SYSTEM CHECKS...")
    
    checks_passed = 0
    total_checks = 5
    
    # Check 1: Environment variables
    try:
        required_vars = ['GEMINI_API_KEY', 'BINANCE_API_KEY', 'BINANCE_SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("✅ Environment variables check passed")
            checks_passed += 1
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
    
    # Check 2: Network connectivity
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.binance.com/api/v3/ping') as response:
                if response.status == 200:
                    print("✅ Binance API connectivity check passed")
                    checks_passed += 1
                else:
                    print("❌ Binance API connectivity check failed")
    except Exception as e:
        print(f"❌ Network connectivity check failed: {e}")
    
    # Check 3: AI API
    try:
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and len(gemini_key) > 10:
            print("✅ Google Gemini API key format check passed")
            checks_passed += 1
        else:
            print("❌ Invalid Gemini API key")
    except Exception as e:
        print(f"❌ AI API check failed: {e}")
    
    # Check 4: Database connectivity
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url and supabase_url.startswith('https://'):
            print("✅ Supabase URL format check passed")
            checks_passed += 1
        else:
            print("⚠️  Supabase URL check failed (database features disabled)")
    except Exception as e:
        print(f"❌ Database check failed: {e}")
    
    # Check 5: Telegram configuration
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
        if telegram_token and telegram_chat:
            print("✅ Telegram configuration check passed")
            checks_passed += 1
        else:
            print("⚠️  Telegram configuration incomplete (notifications disabled)")
    except Exception as e:
        print(f"❌ Telegram check failed: {e}")
    
    print(f"\n📊 System checks completed: {checks_passed}/{total_checks} passed")
    
    if checks_passed < 2:
        print("❌ Too many system checks failed. Please review configuration.")
        return False
    
    return True


async def main():
    """Main application entry point with enhanced error handling"""
    print_startup_banner()
    
    # Setup logging
    setup_comprehensive_logging()
    logger = logging.getLogger("main")
    
    try:
        # Run system checks
        system_checks_passed = await run_system_checks()
        if not system_checks_passed:
            print("\n❌ System checks failed. Exiting...")
            return
        
        # Create and validate configuration
        config = create_enhanced_trading_config()
        if not config:
            print("\n❌ Configuration validation failed. Please check your .env file.")
            return
        
        # Print configuration summary
        print_configuration_summary(config)
        
        # Safety confirmation for live trading
        if not config.paper_trading:
            print("\n⚠️  WARNING: LIVE TRADING MODE ENABLED!")
            print("This will use real money. Are you sure? (type 'yes' to continue)")
            confirmation = input().strip().lower()
            if confirmation != 'yes':
                print("❌ Live trading cancelled by user.")
                return
        
        # Create and start enhanced trading engine
        print("\n🚀 INITIALIZING TRADING ENGINE...")
        engine = EnhancedTradingEngine(config)
        
        # Start the engine
        logger.info("Starting enhanced trading engine...")
        await engine.start_trading()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal (Ctrl+C)")
        print("\n\n🛑 SHUTDOWN SIGNAL RECEIVED")
        print("Stopping trading engine safely...")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Application error: {e}")
        raise
        
    finally:
        print("\n✅ Application shutdown complete")
        print("Thank you for using Advanced Personal Trading Platform 2105!")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run the enhanced application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
