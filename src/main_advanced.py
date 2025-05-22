"""
Advanced Personal Trading Platform - Main Entry Point
Bot_Arbitraje2105 - Versión 2.0 Avanzada

Sistema completo de trading con:
- Múltiples estrategias (Scalping, Day Trading, Arbitraje)
- IA avanzada con Google Gemini
- WebSockets en tiempo real
- Gestión de riesgos institucional
- Monitoreo y alertas
- Arquitectura limpia con DI
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.container.di_container import DIContainer
from application.services.advanced_trading_engine import AdvancedTradingEngine, TradingEngineConfig


def setup_logging():
    """Configura el sistema de logging avanzado."""
    
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configuración de logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Console handler con encoding UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler con encoding UTF-8
    file_handler = logging.FileHandler(
        logs_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Logger principal
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[console_handler, file_handler]
    )
    
    # Configurar loggers específicos
    loggers = {
        'AdvancedTradingEngine': logging.INFO,
        'DIContainer': logging.INFO,
        'WebSocketManager': logging.INFO,
        'GeminiAnalyzer': logging.INFO,
        'RealTimeDataProcessor': logging.INFO,
        'SystemMonitor': logging.INFO,
        'NotificationService': logging.INFO,
        'ScalpingStrategy': logging.INFO,
        'DayTradingStrategy': logging.INFO,
        'AdvancedRiskManager': logging.INFO
    }
    
    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    # Reducir verbosidad de librerías externas
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    main_logger = logging.getLogger("Main")
    main_logger.info("Logging system initialized")
    
    return main_logger


def print_banner():
    """Muestra el banner de inicio."""
    banner = """
================================================================================
                                                                              
              ** ADVANCED PERSONAL TRADING PLATFORM 2.0 **                  
                            Bot_Arbitraje2105                                
                                                                              
  Features:                                                               
     * Multi-Strategy Trading (Scalping, Day Trading, Arbitrage)             
     * AI-Powered Analysis (Google Gemini Integration)                       
     * Real-time WebSocket Data Streams                                      
     * Institutional-Grade Risk Management                                   
     * Advanced Monitoring & Alerting                                        
     * Clean Architecture with Dependency Injection                          
                                                                              
  Performance Goals:                                                       
     * Scalping: 50-200 trades/day, 0.01-0.1% per trade                     
     * Day Trading: 5-20 trades/day, 0.5-2% per trade                       
     * Win Rate: >65% | Max Drawdown: <10% | Sharpe Ratio: >1.5             
                                                                              
  Risk Management:                                                        
     * Dynamic Stop-Loss based on ATR volatility                             
     * Position Sizing with AI confidence weighting                          
     * Multi-layer risk validation                                           
     * Real-time portfolio monitoring                                        
                                                                              
================================================================================
    """
    print(banner)


def validate_environment_config() -> bool:
    """Valida la configuración del entorno."""
    logger = logging.getLogger("ConfigValidator")
    
    try:
        # Cargar variables de entorno desde .env
        from dotenv import load_dotenv
        load_dotenv()
        
        config = TradingEngineConfig.from_env()
        
        # Validaciones críticas
        if not config.gemini_api_key:
            logger.error("GEMINI_API_KEY is required for AI analysis")
            return False
        
        if config.initial_capital <= 0:
            logger.error("INITIAL_CAPITAL must be greater than 0")
            return False
        
        if not config.trading_symbols:
            logger.error("TRADING_SYMBOLS cannot be empty")
            return False
        
        if not config.enabled_strategies:
            logger.error("ENABLED_STRATEGIES cannot be empty")
            return False
        
        # Validaciones de warning
        if config.max_daily_loss_pct > 10:
            logger.warning(f"High daily loss limit: {config.max_daily_loss_pct}%")
        
        if config.initial_capital < 1000:
            logger.warning(f"Low initial capital: ${config.initial_capital}")
        
        logger.info("Environment configuration validated successfully")
        logger.info(f"Trading symbols: {', '.join(config.trading_symbols)}")
        logger.info(f"Enabled strategies: {', '.join(config.enabled_strategies)}")
        logger.info(f"Initial capital: ${config.initial_capital:,.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return False


def setup_signal_handlers(trading_engine: AdvancedTradingEngine):
    """Configura manejadores de señales del sistema."""
    logger = logging.getLogger("SignalHandler")
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(graceful_shutdown(trading_engine))
    
    # Registrar manejadores para señales de terminación
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Terminación del proceso
    
    logger.info("Signal handlers configured")


async def graceful_shutdown(trading_engine: AdvancedTradingEngine):
    """Realiza un cierre graceful del sistema."""
    logger = logging.getLogger("Shutdown")
    
    try:
        logger.info("Initiating graceful shutdown...")
        
        # Detener el motor de trading
        await trading_engine.stop()
        
        logger.info("Graceful shutdown completed")
        
        # Terminar el loop de eventos
        loop = asyncio.get_event_loop()
        loop.stop()
        
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")
        sys.exit(1)


async def health_check_startup():
    """Realiza health checks de inicio."""
    logger = logging.getLogger("HealthCheck")
    
    try:
        # Verificar conectividad a internet
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('https://httpbin.org/get', timeout=5) as response:
                if response.status != 200:
                    raise Exception("Internet connectivity check failed")
        
        logger.info("Internet connectivity check passed")
        
        # Verificar API de Gemini
        from dotenv import load_dotenv
        load_dotenv()
        config = TradingEngineConfig.from_env()
        if config.gemini_api_key:
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            
            # Test simple de API
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Test connection")
            
            logger.info("Gemini API connectivity check passed")
        
        logger.info("All startup health checks passed")
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False


async def main():
    """Función principal de la aplicación."""
    
    # Configurar logging
    logger = setup_logging()
    
    # Mostrar banner
    print_banner()
    
    try:
        logger.info("Starting Advanced Personal Trading Platform...")
        
        # Validar configuración
        if not validate_environment_config():
            logger.error("Configuration validation failed")
            return 1
        
        # Health checks de inicio
        if not await health_check_startup():
            logger.error("Startup health checks failed")
            return 1
        
        # Crear configuración
        from dotenv import load_dotenv
        load_dotenv()
        config = TradingEngineConfig.from_env()
        
        # Configurar contenedor de DI
        logger.info("Setting up Dependency Injection container...")
        container = DIContainer()
        
        # Crear motor de trading
        logger.info("Initializing Advanced Trading Engine...")
        trading_engine = AdvancedTradingEngine(config, container)
        
        # Configurar manejadores de señales
        setup_signal_handlers(trading_engine)
        
        # Inicializar y comenzar el motor
        logger.info("Initializing trading engine components...")
        await trading_engine.initialize()
        
        logger.info("Starting trading engine...")
        await trading_engine.start()
        
        logger.info("Trading engine started successfully!")
        logger.info("Press Ctrl+C to stop the application gracefully")
        
        # Mantener la aplicación corriendo
        try:
            while trading_engine.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        
        # Cierre graceful
        await graceful_shutdown(trading_engine)
        
        logger.info("Application terminated successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
        
    except Exception as e:
        logger.error(f"Critical error in main application: {e}")
        logger.exception("Exception details:")
        return 1


def run():
    """Punto de entrada para ejecutar la aplicación."""
    
    # Verificar versión de Python
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Verificar que estamos en el directorio correcto
    current_dir = Path(__file__).parent
    if not (current_dir / "domain").exists():
        print("Error: Please run from the src/ directory")
        print("Usage: cd src && python main.py")
        sys.exit(1)
    
    try:
        # Ejecutar la aplicación
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
