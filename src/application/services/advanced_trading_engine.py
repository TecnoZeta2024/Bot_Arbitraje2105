"""
Trading Engine Avanzado con Arquitectura Limpia
Orquestador principal que integra todos los componentes del sistema
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict

from ..domain.entities.market_data import MarketData
from ..domain.entities.trading_signal import TradingSignal
from ..domain.strategies.base_strategy import BaseStrategy
from ..domain.strategies.scalping_strategy import ScalpingStrategy
from ..domain.strategies.day_trading_strategy import DayTradingStrategy
from ..domain.risk_management.advanced_risk_manager import AdvancedRiskManager
from ..infrastructure.websockets.exchange_websocket_manager import ExchangeWebSocketManager
from ..infrastructure.ai_analysis.gemini_analyzer import GeminiAnalyzer
from ..infrastructure.real_time_data.stream_processor import RealTimeDataProcessor
from ..infrastructure.monitoring.system_monitor import SystemMonitor
from ..infrastructure.messaging.notification_service import NotificationService
from ..infrastructure.container.di_container import DIContainer, ServiceLocator
import os


@dataclass
class TradingEngineConfig:
    """Configuración del motor de trading."""
    # Configuración general
    enabled_strategies: List[str]
    trading_symbols: List[str]
    initial_capital: float
    max_positions: int
    
    # Configuración de risk management
    max_daily_loss_pct: float
    max_position_size_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    
    # Configuración de WebSockets
    exchange_name: str
    websocket_reconnect_delay: int
    
    # Configuración de IA
    gemini_api_key: str
    ai_confidence_threshold: float
    
    # Configuración de notificaciones
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    enable_notifications: bool
    
    # Configuración de monitoreo
    monitoring_interval: int
    health_check_interval: int
    
    @classmethod
    def from_env(cls) -> 'TradingEngineConfig':
        """Crea configuración desde variables de entorno."""
        return cls(
            enabled_strategies=os.getenv('ENABLED_STRATEGIES', 'scalping,day_trading').split(','),
            trading_symbols=os.getenv('TRADING_SYMBOLS', 'BTCUSDT,ETHUSDT,ADAUSDT').split(','),
            initial_capital=float(os.getenv('INITIAL_CAPITAL', '10000')),
            max_positions=int(os.getenv('MAX_POSITIONS', '5')),
            
            max_daily_loss_pct=float(os.getenv('MAX_DAILY_LOSS_PCT', '2.0')),
            max_position_size_pct=float(os.getenv('MAX_POSITION_SIZE_PCT', '10.0')),
            stop_loss_pct=float(os.getenv('STOP_LOSS_PCT', '1.0')),
            take_profit_pct=float(os.getenv('TAKE_PROFIT_PCT', '2.0')),
            
            exchange_name=os.getenv('EXCHANGE_NAME', 'binance'),
            websocket_reconnect_delay=int(os.getenv('WEBSOCKET_RECONNECT_DELAY', '5')),
            
            gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
            ai_confidence_threshold=float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.7')),
            
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            enable_notifications=os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true',
            
            monitoring_interval=int(os.getenv('MONITORING_INTERVAL', '60')),
            health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
        )


class AdvancedTradingEngine:
    """Motor de trading avanzado con arquitectura limpia."""
    
    def __init__(self, config: TradingEngineConfig, container: DIContainer):
        self.config = config
        self.container = container
        self.logger = logging.getLogger("AdvancedTradingEngine")
        
        # Estado del motor
        self.is_running = False
        self.start_time = None
        self.current_positions = {}
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.successful_trades = 0
        
        # Componentes principales
        self.websocket_manager = None
        self.data_processor = None
        self.ai_analyzer = None
        self.risk_manager = None
        self.strategies = {}
        self.system_monitor = None
        self.notification_service = None
        
        # Métricas de rendimiento
        self.performance_metrics = {
            'signals_generated': 0,
            'signals_executed': 0,
            'total_volume': 0.0,
            'avg_execution_time': 0.0,
            'last_signal_time': None
        }
        
        self.logger.info("AdvancedTradingEngine initialized")
    
    async def initialize(self):
        """Inicializa todos los componentes del motor."""
        self.logger.info("Initializing trading engine components...")
        
        try:
            # Configurar ServiceLocator
            ServiceLocator.set_container(self.container)
            
            # Registrar servicios en el contenedor
            await self._register_services()
            
            # Inicializar componentes principales
            await self._initialize_components()
            
            # Configurar suscripciones y callbacks
            await self._setup_subscriptions()
            
            # Registrar health checks
            await self._setup_monitoring()
            
            self.logger.info("Trading engine initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing trading engine: {e}")
            raise
    
    async def _register_services(self):
        """Registra todos los servicios en el contenedor DI."""
        # Registrar configuración
        self.container.register_instance(TradingEngineConfig, self.config)
        
        # Registrar componentes principales como singletons
        self.container.register_singleton(ExchangeWebSocketManager)
        self.container.register_singleton(RealTimeDataProcessor)
        self.container.register_singleton(GeminiAnalyzer)
        self.container.register_singleton(AdvancedRiskManager)
        self.container.register_singleton(SystemMonitor)
        self.container.register_singleton(NotificationService)
        
        # Registrar estrategias como transient
        self.container.register_transient(ScalpingStrategy)
        self.container.register_transient(DayTradingStrategy)
        
        self.logger.info("Services registered in DI container")
    
    async def _initialize_components(self):
        """Inicializa todos los componentes principales."""
        # WebSocket Manager
        self.websocket_manager = self.container.resolve(ExchangeWebSocketManager)
        
        # Data Processor
        self.data_processor = self.container.resolve(RealTimeDataProcessor)
        await self.data_processor.start()
        
        # AI Analyzer
        self.ai_analyzer = self.container.resolve(GeminiAnalyzer)
        
        # Risk Manager
        self.risk_manager = self.container.resolve(AdvancedRiskManager)
        
        # System Monitor
        self.system_monitor = self.container.resolve(SystemMonitor)
        await self.system_monitor.start()
        
        # Notification Service
        self.notification_service = self.container.resolve(NotificationService)
        
        # Configurar notificaciones si están habilitadas
        if self.config.enable_notifications:
            if self.config.telegram_bot_token and self.config.telegram_chat_id:
                self.notification_service.configure_telegram(
                    self.config.telegram_bot_token,
                    self.config.telegram_chat_id
                )
        
        await self.notification_service.start()
        
        # Inicializar estrategias habilitadas
        await self._initialize_strategies()
        
        self.logger.info("All components initialized successfully")
    
    async def _initialize_strategies(self):
        """Inicializa las estrategias habilitadas."""
        for strategy_name in self.config.enabled_strategies:
            try:
                if strategy_name.lower() == 'scalping':
                    strategy = self.container.resolve(ScalpingStrategy)
                elif strategy_name.lower() == 'day_trading':
                    strategy = self.container.resolve(DayTradingStrategy)
                else:
                    self.logger.warning(f"Unknown strategy: {strategy_name}")
                    continue
                
                self.strategies[strategy_name] = strategy
                self.logger.info(f"Initialized strategy: {strategy_name}")
                
            except Exception as e:
                self.logger.error(f"Error initializing strategy {strategy_name}: {e}")
    
    async def _setup_subscriptions(self):
        """Configura suscripciones a datos de mercado."""
        # Suscribirse a datos de mercado para cada símbolo
        for symbol in self.config.trading_symbols:
            self.data_processor.subscribe(symbol, self._on_market_data_received)
            
            # Suscribirse a WebSockets
            await self.websocket_manager.subscribe_to_ticker(symbol)
            await self.websocket_manager.subscribe_to_orderbook(symbol)
        
        self.logger.info(f"Subscribed to market data for {len(self.config.trading_symbols)} symbols")
    
    async def _setup_monitoring(self):
        """Configura health checks y monitoreo."""
        # Health check del motor de trading
        def trading_engine_health_check():
            from ..infrastructure.monitoring.system_monitor import HealthCheck, HealthStatus
            
            if not self.is_running:
                return HealthCheck(
                    component="trading_engine",
                    status=HealthStatus.UNHEALTHY,
                    message="Trading engine is not running",
                    timestamp=datetime.now()
                )
            
            # Verificar conexiones WebSocket
            if not self.websocket_manager.is_connected():
                return HealthCheck(
                    component="trading_engine",
                    status=HealthStatus.DEGRADED,
                    message="WebSocket connection issues",
                    timestamp=datetime.now()
                )
            
            return HealthCheck(
                component="trading_engine",
                status=HealthStatus.HEALTHY,
                message="Trading engine operating normally",
                timestamp=datetime.now(),
                details={
                    "active_strategies": len(self.strategies),
                    "active_positions": len(self.current_positions),
                    "daily_pnl": self.daily_pnl,
                    "total_trades": self.total_trades
                }
            )
        
        self.system_monitor.health_checker.register_health_check(
            "trading_engine", 
            trading_engine_health_check, 
            self.config.health_check_interval
        )
    
    async def start(self):
        """Inicia el motor de trading."""
        if self.is_running:
            self.logger.warning("Trading engine is already running")
            return
        
        self.logger.info("Starting Advanced Trading Engine...")
        
        try:
            # Inicializar si no se ha hecho
            if self.websocket_manager is None:
                await self.initialize()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # Conectar WebSockets
            await self.websocket_manager.connect_all()
            
            # Iniciar loops principales
            asyncio.create_task(self._trading_loop())
            asyncio.create_task(self._monitoring_loop())
            asyncio.create_task(self._performance_reporter_loop())
            
            # Notificar inicio
            await self.notification_service.notify_system_status(
                "INICIADO",
                f"Motor de trading iniciado exitosamente\n"
                f"Estrategias: {', '.join(self.config.enabled_strategies)}\n"
                f"Símbolos: {', '.join(self.config.trading_symbols)}\n"
                f"Capital inicial: ${self.config.initial_capital:,.2f}"
            )
            
            self.logger.info("Trading engine started successfully")
            
        except Exception as e:
            self.is_running = False
            self.logger.error(f"Error starting trading engine: {e}")
            raise
    
    async def stop(self):
        """Detiene el motor de trading."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping trading engine...")
        
        self.is_running = False
        
        try:
            # Cerrar todas las posiciones abiertas
            await self._close_all_positions()
            
            # Desconectar WebSockets
            if self.websocket_manager:
                await self.websocket_manager.disconnect_all()
            
            # Detener componentes
            if self.data_processor:
                await self.data_processor.stop()
            
            if self.system_monitor:
                await self.system_monitor.stop()
            
            if self.notification_service:
                await self.notification_service.stop()
            
            # Notificar parada
            await self.notification_service.notify_system_status(
                "DETENIDO",
                f"Motor de trading detenido\n"
                f"P&L del día: ${self.daily_pnl:,.2f}\n"
                f"Trades totales: {self.total_trades}\n"
                f"Tasa de éxito: {(self.successful_trades/max(self.total_trades,1)*100):.1f}%"
            )
            
            self.logger.info("Trading engine stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")
    
    async def _on_market_data_received(self, market_data: MarketData):
        """Callback para datos de mercado recibidos."""
        try:
            # Procesar con todas las estrategias activas
            for strategy_name, strategy in self.strategies.items():
                # Verificar si la estrategia está interesada en este símbolo
                if market_data.symbol in self.config.trading_symbols:
                    signal = await strategy.analyze(market_data)
                    
                    if signal:
                        await self._process_trading_signal(signal, strategy_name)
        
        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")
    
    async def _process_trading_signal(self, signal: TradingSignal, strategy_name: str):
        """Procesa una señal de trading."""
        try:
            self.performance_metrics['signals_generated'] += 1
            self.performance_metrics['last_signal_time'] = datetime.now()
            
            # Validar señal con AI
            if signal.ai_analysis:
                if signal.ai_analysis.confidence < self.config.ai_confidence_threshold:
                    self.logger.info(f"Signal rejected due to low AI confidence: {signal.ai_analysis.confidence}")
                    return
            
            # Verificar riesgos
            risk_approved = await self.risk_manager.validate_signal(signal)
            
            if not risk_approved:
                self.logger.info(f"Signal rejected by risk manager: {signal.symbol}")
                return
            
            # Calcular tamaño de posición
            position_size = await self.risk_manager.calculate_position_size(
                signal, self.config.initial_capital
            )
            
            if position_size <= 0:
                self.logger.info(f"Invalid position size calculated: {position_size}")
                return
            
            # Ejecutar señal (simulación)
            success = await self._execute_signal(signal, position_size, strategy_name)
            
            if success:
                self.performance_metrics['signals_executed'] += 1
                
                # Notificar señal
                await self.notification_service.notify_trade_signal(
                    signal.symbol,
                    signal.action.value,
                    signal.price,
                    signal.ai_analysis.confidence if signal.ai_analysis else 0.0
                )
        
        except Exception as e:
            self.logger.error(f"Error processing trading signal: {e}")
    
    async def _execute_signal(self, signal: TradingSignal, position_size: float, strategy_name: str) -> bool:
        """Ejecuta una señal de trading (simulación)."""
        try:
            execution_time = datetime.now()
            
            # Simular ejecución
            position = {
                'id': f"pos_{execution_time.strftime('%Y%m%d_%H%M%S_%f')}",
                'symbol': signal.symbol,
                'action': signal.action.value,
                'size': position_size,
                'entry_price': signal.price,
                'entry_time': execution_time,
                'strategy': strategy_name,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'status': 'open'
            }
            
            self.current_positions[position['id']] = position
            self.total_trades += 1
            
            self.logger.info(
                f"Executed {signal.action.value} signal for {signal.symbol} "
                f"at ${signal.price:.6f} with size ${position_size:.2f}"
            )
            
            # Simular cierre aleatorio después de un tiempo
            asyncio.create_task(self._simulate_position_close(position))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            return False
    
    async def _simulate_position_close(self, position: Dict[str, Any]):
        """Simula el cierre de una posición después de un tiempo aleatorio."""
        import random
        
        # Esperar entre 1-30 minutos (simulación)
        wait_time = random.randint(60, 1800)
        await asyncio.sleep(wait_time)
        
        if position['id'] not in self.current_positions:
            return
        
        # Simular precio de cierre (±2% del precio de entrada)
        price_change_pct = random.uniform(-2.0, 2.0)
        close_price = position['entry_price'] * (1 + price_change_pct / 100)
        
        # Calcular P&L
        if position['action'] == 'BUY':
            pnl = (close_price - position['entry_price']) * position['size'] / position['entry_price']
        else:
            pnl = (position['entry_price'] - close_price) * position['size'] / position['entry_price']
        
        pnl_pct = (pnl / position['size']) * 100
        
        # Actualizar posición
        position['exit_price'] = close_price
        position['exit_time'] = datetime.now()
        position['pnl'] = pnl
        position['pnl_pct'] = pnl_pct
        position['status'] = 'closed'
        
        # Actualizar métricas
        self.daily_pnl += pnl
        if pnl > 0:
            self.successful_trades += 1
        
        # Remover de posiciones activas
        del self.current_positions[position['id']]
        
        # Notificar P&L
        await self.notification_service.notify_profit_loss(
            position['symbol'],
            pnl,
            pnl_pct,
            position['size']
        )
        
        self.logger.info(
            f"Closed position {position['id']} - "
            f"P&L: ${pnl:.2f} ({pnl_pct:.2f}%)"
        )
    
    async def _close_all_positions(self):
        """Cierra todas las posiciones abiertas."""
        for position_id in list(self.current_positions.keys()):
            position = self.current_positions[position_id]
            # Simular cierre inmediato
            await self._simulate_position_close(position)
    
    async def _trading_loop(self):
        """Loop principal de trading."""
        while self.is_running:
            try:
                # Verificar límites de riesgo diarios
                if abs(self.daily_pnl) > self.config.initial_capital * (self.config.max_daily_loss_pct / 100):
                    await self.notification_service.notify_critical_alert(
                        "Límite de pérdida diaria alcanzado",
                        f"P&L diario: ${self.daily_pnl:.2f}\n"
                        f"Límite: {self.config.max_daily_loss_pct}%",
                        "risk_manager"
                    )
                    
                    # Detener trading por el día
                    await self.stop()
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)
    
    async def _monitoring_loop(self):
        """Loop de monitoreo del sistema."""
        while self.is_running:
            try:
                # Actualizar métricas del sistema
                self.system_monitor.metrics_collector.set_gauge(
                    "trading.active_positions", len(self.current_positions)
                )
                
                self.system_monitor.metrics_collector.set_gauge(
                    "trading.daily_pnl", self.daily_pnl
                )
                
                self.system_monitor.metrics_collector.set_gauge(
                    "trading.total_trades", self.total_trades
                )
                
                if self.total_trades > 0:
                    win_rate = (self.successful_trades / self.total_trades) * 100
                    self.system_monitor.metrics_collector.set_gauge(
                        "trading.win_rate", win_rate
                    )
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _performance_reporter_loop(self):
        """Loop de reportes de rendimiento."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Cada hora
                
                await self._generate_performance_report()
                
            except Exception as e:
                self.logger.error(f"Error in performance reporter: {e}")
    
    async def _generate_performance_report(self):
        """Genera un reporte de rendimiento."""
        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        win_rate = (self.successful_trades / max(self.total_trades, 1)) * 100
        
        report = (
            f"📊 Reporte de Rendimiento\n\n"
            f"⏰ Tiempo activo: {uptime}\n"
            f"💰 P&L diario: ${self.daily_pnl:.2f}\n"
            f"📈 Trades totales: {self.total_trades}\n"
            f"✅ Trades exitosos: {self.successful_trades}\n"
            f"📊 Tasa de éxito: {win_rate:.1f}%\n"
            f"📊 Posiciones activas: {len(self.current_positions)}\n"
            f"📡 Señales generadas: {self.performance_metrics['signals_generated']}\n"
            f"⚡ Señales ejecutadas: {self.performance_metrics['signals_executed']}"
        )
        
        await self.notification_service.notify_system_status("REPORTE", report)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del motor."""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "daily_pnl": self.daily_pnl,
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "win_rate": (self.successful_trades / max(self.total_trades, 1)) * 100,
            "active_positions": len(self.current_positions),
            "active_strategies": list(self.strategies.keys()),
            "performance_metrics": self.performance_metrics,
            "config": asdict(self.config)
        }
