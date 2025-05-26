"""
Servicio de backend para la UI de Scalper's Brain
Actúa como puente entre la interfaz de usuario y los servicios de dominio
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

logger = logging.getLogger(__name__)

class UIBackendService(QObject):
    """
    Servicio que conecta la interfaz de usuario con los servicios de backend
    Usa señales Qt para comunicarse con la interfaz de manera thread-safe
    """
    
    # Señales para comunicación con la UI
    market_data_updated = pyqtSignal(dict)
    opportunity_detected = pyqtSignal(dict)
    trading_status_changed = pyqtSignal(dict)
    notification_received = pyqtSignal(str, str, int, bool)  # mensaje, level, timeout, persistent
    connection_status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Referencias a servicios
        self.exchange_adapters = {}
        self.market_data_service = None
        self.trading_service = None
        self.strategy_service = None
        
        # Estado interno
        self.is_trading_active = False
        self.active_exchange = None
        self.paper_trading_mode = True
        self.active_strategies = {}
        
        # Cola de eventos para procesamiento asíncrono
        self.event_queue = asyncio.Queue()
        
        # Timer para actualización periódica
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_updates)
        self.update_timer.start(100)  # 100ms para procesamiento frecuente
        
        logger.info("UIBackendService inicializado")
    
    def register_exchange_adapter(self, exchange_id: str, adapter):
        """Registra un adaptador de exchange"""
        self.exchange_adapters[exchange_id] = adapter
        logger.info(f"Adaptador de exchange registrado: {exchange_id}")
    
    def register_market_data_service(self, service):
        """Registra el servicio de datos de mercado"""
        self.market_data_service = service
        logger.info("Servicio de datos de mercado registrado")
    
    def register_trading_service(self, service):
        """Registra el servicio de trading"""
        self.trading_service = service
        logger.info("Servicio de trading registrado")
    
    def register_strategy_service(self, service):
        """Registra el servicio de estrategias"""
        self.strategy_service = service
        logger.info("Servicio de estrategias registrado")
    
    async def start(self):
        """Inicia el servicio backend"""
        logger.info("Iniciando servicios backend...")
        
        # Iniciar procesamiento de eventos
        asyncio.create_task(self._process_event_queue())
        
        # Establecer exchange por defecto
        await self.set_exchange("binance")
        
        # Emitir estado de conexión inicial
        self.connection_status_changed.emit("Conectando...")
        
        # Enviar notificación de inicio
        self.send_notification("Servicios backend iniciados", "info")
        
        logger.info("Servicios backend iniciados")
    
    async def set_exchange(self, exchange_id: str) -> bool:
        """Establece el exchange activo"""
        if exchange_id not in self.exchange_adapters:
            logger.warning(f"Exchange no disponible: {exchange_id}")
            self.send_notification(f"Exchange {exchange_id} no disponible", "error")
            return False
        
        # Si ya hay un exchange activo, desconectarlo
        if self.active_exchange:
            await self.exchange_adapters[self.active_exchange].disconnect()
        
        # Establecer nuevo exchange
        self.active_exchange = exchange_id
        adapter = self.exchange_adapters[exchange_id]
        
        # Conectar al exchange
        try:
            success = await adapter.connect()
            
            if success:
                self.connection_status_changed.emit(f"Conectado a {exchange_id}")
                self.send_notification(f"Conectado a {exchange_id}", "success")
                logger.info(f"Exchange establecido: {exchange_id}")
                
                # Iniciar suscripción a datos
                asyncio.create_task(self._subscribe_to_market_data())
                
                return True
            else:
                self.connection_status_changed.emit("Error de conexión")
                self.send_notification(f"Error al conectar con {exchange_id}", "error")
                logger.error(f"Error al conectar con el exchange: {exchange_id}")
                return False
                
        except Exception as e:
            self.connection_status_changed.emit("Error de conexión")
            self.send_notification(f"Error al conectar con {exchange_id}: {str(e)}", "error")
            logger.exception(f"Excepción al conectar con el exchange {exchange_id}: {e}")
            return False
    
    async def start_trading(self):
        """Inicia el trading automático"""
        if not self.active_exchange:
            self.send_notification("No hay exchange configurado", "error")
            return False
        
        self.is_trading_active = True
        
        # Notificar cambio de estado
        status_info = {
            'active': True,
            'mode': 'Paper Trading' if self.paper_trading_mode else 'Trading Real',
            'exchange': self.active_exchange,
            'timestamp': time.time()
        }
        
        self.trading_status_changed.emit(status_info)
        
        self.send_notification(
            f"Trading iniciado en modo {'Paper Trading' if self.paper_trading_mode else 'Trading Real'}", 
            "warning" if not self.paper_trading_mode else "info"
        )
        
        logger.info(f"Trading iniciado: {status_info}")
        return True
    
    async def stop_trading(self):
        """Detiene el trading automático"""
        self.is_trading_active = False
        
        # Notificar cambio de estado
        status_info = {
            'active': False,
            'mode': 'Paper Trading' if self.paper_trading_mode else 'Trading Real',
            'exchange': self.active_exchange,
            'timestamp': time.time()
        }
        
        self.trading_status_changed.emit(status_info)
        self.send_notification("Trading detenido", "warning")
        
        logger.info("Trading detenido")
        return True
    
    async def set_paper_trading(self, enabled: bool):
        """Establece el modo paper trading"""
        if self.paper_trading_mode == enabled:
            return
        
        self.paper_trading_mode = enabled
        
        # Notificar cambio de estado
        status_info = {
            'active': self.is_trading_active,
            'mode': 'Paper Trading' if enabled else 'Trading Real',
            'exchange': self.active_exchange,
            'timestamp': time.time()
        }
        
        self.trading_status_changed.emit(status_info)
        
        # Advertencia importante si se desactiva paper trading
        if not enabled:
            self.send_notification(
                "¡ATENCIÓN! Modo de trading real activado. Se utilizarán fondos reales.", 
                "error", 
                timeout=10000,
                persistent=True
            )
        else:
            self.send_notification("Modo paper trading activado", "info")
        
        logger.info(f"Modo paper trading: {enabled}")
        return True
    
    async def activate_strategy(self, strategy_id: str, enabled: bool):
        """Activa o desactiva una estrategia"""
        if strategy_id not in self.active_strategies:
            self.active_strategies[strategy_id] = {
                'enabled': enabled,
                'settings': {}
            }
        else:
            self.active_strategies[strategy_id]['enabled'] = enabled
        
        # Si hay un servicio de estrategias, notificarle
        if self.strategy_service:
            try:
                await self.strategy_service.set_strategy_status(strategy_id, enabled)
            except Exception as e:
                logger.error(f"Error al cambiar estado de estrategia {strategy_id}: {e}")
        
        logger.info(f"Estrategia {strategy_id}: {'activada' if enabled else 'desactivada'}")
        return True
    
    async def update_strategy_settings(self, strategy_id: str, settings: Dict[str, Any]):
        """Actualiza la configuración de una estrategia"""
        if strategy_id not in self.active_strategies:
            self.active_strategies[strategy_id] = {
                'enabled': False,
                'settings': settings
            }
        else:
            self.active_strategies[strategy_id]['settings'] = settings
        
        # Si hay un servicio de estrategias, notificarle
        if self.strategy_service:
            try:
                await self.strategy_service.update_strategy_settings(strategy_id, settings)
            except Exception as e:
                logger.error(f"Error al actualizar configuración de estrategia {strategy_id}: {e}")
        
        logger.info(f"Configuración de estrategia {strategy_id} actualizada")
        return True
    
    async def execute_trade(self, trade_request: Dict[str, Any]):
        """Ejecuta una operación de trading"""
        if not self.active_exchange:
            self.send_notification("No hay exchange configurado", "error")
            return False
        
        # Si el trading está inactivo, rechazar la operación
        if not self.is_trading_active:
            self.send_notification("El trading está desactivado", "error")
            return False
        
        # Preparar datos de la operación
        trade_data = {
            **trade_request,
            'exchange': self.active_exchange,
            'paper_trading': self.paper_trading_mode,
            'timestamp': time.time()
        }
        
        try:
            # Si hay un servicio de trading, ejecutar la operación
            if self.trading_service:
                result = await self.trading_service.execute_trade(trade_data)
                
                # Notificar resultado
                if result.get('success', False):
                    self.send_notification(
                        f"Operación ejecutada: {trade_data.get('side', 'COMPRA/VENTA')} "
                        f"{trade_data.get('symbol', 'UNKNOWN')} a {trade_data.get('price', 0.0)}",
                        "success"
                    )
                else:
                    self.send_notification(
                        f"Error al ejecutar operación: {result.get('error', 'Error desconocido')}",
                        "error"
                    )
                
                return result
            else:
                # Simulación básica si no hay servicio
                self.send_notification(
                    f"Simulación: {trade_data.get('side', 'COMPRA/VENTA')} "
                    f"{trade_data.get('symbol', 'UNKNOWN')} a {trade_data.get('price', 0.0)}",
                    "info"
                )
                return {'success': True, 'simulated': True}
                
        except Exception as e:
            logger.exception(f"Error al ejecutar operación: {e}")
            self.send_notification(f"Error al ejecutar operación: {str(e)}", "error")
            return {'success': False, 'error': str(e)}
    
    def send_notification(self, message: str, level: str = 'info', timeout: int = 3000, persistent: bool = False):
        """Envía una notificación a la UI"""
        self.notification_received.emit(message, level, timeout, persistent)
        logger.debug(f"Notificación enviada: [{level}] {message}")
    
    async def _process_event_queue(self):
        """Procesa los eventos de la cola de manera asíncrona"""
        while True:
            try:
                event = await self.event_queue.get()
                event_type = event.get('type')
                
                if event_type == 'market_data':
                    self.market_data_updated.emit(event)
                elif event_type == 'opportunity':
                    self.opportunity_detected.emit(event)
                elif event_type == 'notification':
                    self.send_notification(
                        event.get('message', ''),
                        event.get('level', 'info'),
                        event.get('timeout', 3000),
                        event.get('persistent', False)
                    )
                
                self.event_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")
    
    @pyqtSlot()
    def process_updates(self):
        """Procesa actualizaciones periódicas (llamado por QTimer)"""
        # Este método se ejecuta en el hilo de Qt
        pass
    
    async def _subscribe_to_market_data(self):
        """Suscribe a datos de mercado del exchange activo"""
        if not self.active_exchange or not self.exchange_adapters:
            logger.warning("No se puede suscribir a datos: No hay exchange activo")
            return
        
        try:
            adapter = self.exchange_adapters[self.active_exchange]
            # Configurar callback para datos de mercado
            adapter.set_data_callback(self._handle_market_data)
            
            # Suscribirse a símbolos predeterminados
            symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
            for symbol in symbols:
                await adapter.subscribe_to_ticker(symbol)
                await adapter.subscribe_to_orderbook(symbol)
                # Pequeña pausa para no sobrecargar
                await asyncio.sleep(0.1)
            
            logger.info(f"Suscrito a datos de mercado para {len(symbols)} símbolos en {self.active_exchange}")
            
        except Exception as e:
            logger.exception(f"Error al suscribirse a datos de mercado: {e}")
    
    def _handle_market_data(self, data: Dict[str, Any]):
        """Callback para procesar datos de mercado recibidos"""
        # Añadir a la cola para procesamiento asíncrono
        asyncio.create_task(self.event_queue.put(data))
