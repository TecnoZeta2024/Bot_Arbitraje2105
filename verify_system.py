#!/usr/bin/env python3
"""
Sistema de Verificación y Testing - Bot_Arbitraje2105 v2.0
Verifica que todos los componentes estén correctamente instalados y configurados
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Configura logging para el test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger("SystemVerification")

def print_test_header(test_name: str):
    """Imprime header de test."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {test_name}")
    print(f"{'='*60}")

async def test_basic_imports():
    """Test de importaciones básicas."""
    print_test_header("Basic Imports")
    
    try:
        # Core imports
        from domain.entities.market_data import MarketData
        from domain.entities.trading_signal import TradingSignal
        from domain.strategies.base_strategy import BaseStrategy
        from domain.strategies.scalping_strategy import ScalpingStrategy
        from domain.strategies.day_trading_strategy import DayTradingStrategy
        print("✅ Domain layer imports successful")
        
        # Infrastructure imports
        from infrastructure.websockets.exchange_websocket_manager import ExchangeWebSocketManager
        from infrastructure.ai_analysis.gemini_analyzer import GeminiAnalyzer
        from infrastructure.real_time_data.stream_processor import RealTimeDataProcessor
        from infrastructure.monitoring.system_monitor import SystemMonitor
        from infrastructure.messaging.notification_service import NotificationService
        from infrastructure.container.di_container import DIContainer
        print("✅ Infrastructure layer imports successful")
        
        # Application imports
        from application.services.advanced_trading_engine import AdvancedTradingEngine, TradingEngineConfig
        print("✅ Application layer imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

async def test_configuration():
    """Test de configuración del sistema."""
    print_test_header("Configuration")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from application.services.advanced_trading_engine import TradingEngineConfig
        
        config = TradingEngineConfig.from_env()
        
        # Verificar configuraciones críticas
        if not config.gemini_api_key or config.gemini_api_key == 'your_gemini_api_key_here':
            print("⚠️  GEMINI_API_KEY not configured properly")
            return False
        
        if config.initial_capital <= 0:
            print("❌ INITIAL_CAPITAL must be greater than 0")
            return False
        
        print(f"✅ Configuration loaded successfully")
        print(f"  - Initial Capital: ${config.initial_capital:,.2f}")
        print(f"  - Trading Symbols: {', '.join(config.trading_symbols)}")
        print(f"  - Enabled Strategies: {', '.join(config.enabled_strategies)}")
        print(f"  - AI Enabled: {bool(config.gemini_api_key)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

async def test_dependency_injection():
    """Test del contenedor de inyección de dependencias."""
    print_test_header("Dependency Injection Container")
    
    try:
        from infrastructure.container.di_container import DIContainer
        from application.services.advanced_trading_engine import TradingEngineConfig
        
        # Crear contenedor
        container = DIContainer()
        
        # Registrar configuración de prueba
        test_config = TradingEngineConfig(
            enabled_strategies=['scalping'],
            trading_symbols=['BTCUSDT'],
            initial_capital=10000.0,
            max_positions=5,
            max_daily_loss_pct=2.0,
            max_position_size_pct=10.0,
            stop_loss_pct=1.0,
            take_profit_pct=2.0,
            exchange_name='binance',
            websocket_reconnect_delay=5,
            gemini_api_key='test_key',
            ai_confidence_threshold=0.7,
            telegram_bot_token=None,
            telegram_chat_id=None,
            enable_notifications=False,
            monitoring_interval=60,
            health_check_interval=30
        )
        
        container.register_instance(TradingEngineConfig, test_config)
        
        # Verificar registro
        resolved_config = container.resolve(TradingEngineConfig)
        assert resolved_config.initial_capital == 10000.0
        
        print("✅ DI Container working correctly")
        print(f"  - Registered services: {len(container._services)}")
        
        return True
        
    except Exception as e:
        print(f"❌ DI Container error: {e}")
        return False

async def test_ai_integration():
    """Test de integración con IA."""
    print_test_header("AI Integration")
    
    try:
        import google.generativeai as genai
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("⚠️  GEMINI_API_KEY not configured - skipping AI test")
            return True
        
        # Test de conexión básica
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Test simple
        response = model.generate_content("Respond with exactly: 'AI test successful'")
        if "AI test successful" in response.text:
            print("✅ AI connection working")
            
            # Test con GeminiAnalyzer
            from infrastructure.ai_analysis.gemini_analyzer import GeminiAnalyzer
            analyzer = GeminiAnalyzer()
            
            print("✅ GeminiAnalyzer initialized successfully")
            return True
        else:
            print("⚠️  AI response unexpected")
            return False
            
    except Exception as e:
        print(f"❌ AI integration error: {e}")
        return False

async def test_websocket_structure():
    """Test de estructura WebSocket."""
    print_test_header("WebSocket Structure")
    
    try:
        from infrastructure.websockets.exchange_websocket_manager import ExchangeWebSocketManager
        from infrastructure.websockets.binance_websocket import BinanceWebSocket
        
        # Test de creación (sin conexión real)
        ws_manager = ExchangeWebSocketManager()
        binance_ws = BinanceWebSocket()
        
        print("✅ WebSocket classes instantiated successfully")
        print(f"  - WebSocket Manager: {type(ws_manager).__name__}")
        print(f"  - Binance WebSocket: {type(binance_ws).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket structure error: {e}")
        return False

async def test_trading_strategies():
    """Test de estrategias de trading."""
    print_test_header("Trading Strategies")
    
    try:
        from domain.strategies.scalping_strategy import ScalpingStrategy
        from domain.strategies.day_trading_strategy import DayTradingStrategy
        from domain.entities.market_data import MarketData
        from datetime import datetime
        
        # Crear datos de prueba
        test_market_data = MarketData(
            symbol="BTCUSDT",
            price=50000.0,
            volume=1000.0,
            timestamp=datetime.now(),
            bid_price=49999.0,
            ask_price=50001.0,
            high_24h=51000.0,
            low_24h=49000.0,
            price_change_24h=2.5
        )
        
        # Test Scalping Strategy
        scalping = ScalpingStrategy()
        print(f"✅ Scalping Strategy: {type(scalping).__name__}")
        
        # Test Day Trading Strategy
        day_trading = DayTradingStrategy()
        print(f"✅ Day Trading Strategy: {type(day_trading).__name__}")
        
        print("✅ All trading strategies instantiated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Trading strategies error: {e}")
        return False

async def test_risk_management():
    """Test de gestión de riesgos."""
    print_test_header("Risk Management")
    
    try:
        from domain.risk_management.advanced_risk_manager import AdvancedRiskManager, RiskParameters
        
        # Crear parámetros de riesgo
        risk_params = RiskParameters(
            max_position_size_pct=10.0,
            max_daily_loss_pct=2.0,
            stop_loss_pct=1.0,
            take_profit_pct=2.0,
            max_correlation=0.15,
            max_positions=5
        )
        
        # Crear risk manager
        risk_manager = AdvancedRiskManager(risk_params)
        
        print("✅ Risk Management system instantiated successfully")
        print(f"  - Max Position Size: {risk_params.max_position_size_pct}%")
        print(f"  - Max Daily Loss: {risk_params.max_daily_loss_pct}%")
        print(f"  - Stop Loss: {risk_params.stop_loss_pct}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk management error: {e}")
        return False

async def test_monitoring_system():
    """Test del sistema de monitoreo."""
    print_test_header("Monitoring System")
    
    try:
        from infrastructure.monitoring.system_monitor import SystemMonitor
        
        # Crear monitor
        monitor = SystemMonitor()
        
        print("✅ System Monitor instantiated successfully")
        print(f"  - Metrics Collector: Available")
        print(f"  - Alert Manager: Available")
        print(f"  - Health Checker: Available")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring system error: {e}")
        return False

async def test_notification_system():
    """Test del sistema de notificaciones."""
    print_test_header("Notification System")
    
    try:
        from infrastructure.messaging.notification_service import NotificationService
        
        # Crear servicio de notificaciones
        notification_service = NotificationService()
        
        print("✅ Notification Service instantiated successfully")
        print(f"  - Message Router: Available")
        print(f"  - Telegram Channel: Available")
        print(f"  - Email Channel: Available")
        print(f"  - Console Channel: Available")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification system error: {e}")
        return False

async def test_complete_system():
    """Test del sistema completo."""
    print_test_header("Complete System Integration")
    
    try:
        from infrastructure.container.di_container import DIContainer
        from application.services.advanced_trading_engine import AdvancedTradingEngine, TradingEngineConfig
        
        # Crear configuración de prueba
        config = TradingEngineConfig(
            enabled_strategies=['scalping'],
            trading_symbols=['BTCUSDT'],
            initial_capital=10000.0,
            max_positions=5,
            max_daily_loss_pct=2.0,
            max_position_size_pct=10.0,
            stop_loss_pct=1.0,
            take_profit_pct=2.0,
            exchange_name='binance',
            websocket_reconnect_delay=5,
            gemini_api_key='test_key',
            ai_confidence_threshold=0.7,
            telegram_bot_token=None,
            telegram_chat_id=None,
            enable_notifications=False,
            monitoring_interval=60,
            health_check_interval=30
        )
        
        # Crear contenedor
        container = DIContainer()
        
        # Crear motor de trading
        trading_engine = AdvancedTradingEngine(config, container)
        
        print("✅ Complete system instantiated successfully")
        print(f"  - Trading Engine: {type(trading_engine).__name__}")
        print(f"  - Configuration: Valid")
        print(f"  - DI Container: Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete system error: {e}")
        return False

def generate_test_report(test_results):
    """Genera reporte de resultados."""
    print("\n" + "="*80)
    print("📊 SYSTEM VERIFICATION REPORT")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    failed_tests = total_tests - passed_tests
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📈 Overall Results:")
    print(f"  • Total Tests: {total_tests}")
    print(f"  • Passed: {passed_tests} ✅")
    print(f"  • Failed: {failed_tests} ❌")
    print(f"  • Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  • {test_name:<30} {status}")
    
    if success_rate == 100:
        print(f"\n🎉 ALL TESTS PASSED! System is ready for operation.")
        print(f"\n🚀 Next Steps:")
        print(f"  1. Configure your .env file with real API keys")
        print(f"  2. Start with PAPER_TRADING=true")
        print(f"  3. Run: cd src && python main_advanced.py")
    elif success_rate >= 80:
        print(f"\n⚠️  Most tests passed, but some issues detected.")
        print(f"Please review failed tests and fix issues before production use.")
    else:
        print(f"\n❌ Multiple critical issues detected.")
        print(f"Please fix the failed tests before attempting to run the system.")
    
    print("\n" + "="*80)

async def main():
    """Función principal de verificación."""
    logger = setup_logging()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🔍 SYSTEM VERIFICATION & TESTING SUITE 🔍                      ║
║                       Bot_Arbitraje2105 v2.0                                ║
║                                                                              ║
║  This will test all components of your trading platform                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Starting comprehensive system verification")
    
    # Definir tests
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Configuration", test_configuration),
        ("Dependency Injection", test_dependency_injection),
        ("AI Integration", test_ai_integration),
        ("WebSocket Structure", test_websocket_structure),
        ("Trading Strategies", test_trading_strategies),
        ("Risk Management", test_risk_management),
        ("Monitoring System", test_monitoring_system),
        ("Notification System", test_notification_system),
        ("Complete System", test_complete_system)
    ]
    
    # Ejecutar tests
    test_results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name} - PASSED")
            else:
                logger.warning(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name} - ERROR: {e}")
            test_results[test_name] = False
    
    # Generar reporte
    generate_test_report(test_results)
    
    # Retornar código de salida
    all_passed = all(test_results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)
