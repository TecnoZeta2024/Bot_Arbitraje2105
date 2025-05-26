"""
Adaptador para el exchange Binance
Basado en el cliente WebSocket anterior con mejoras
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable

import aiohttp
import websockets

logger = logging.getLogger(__name__)

class BinanceAdapter:
    """
    Adaptador para la conexión con Binance
    Implementa la interfaz común para exchanges
    """
    
    def __init__(self):
        # Configuración
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.api_url = "https://api.binance.com"
        self.testnet_ws_url = "wss://testnet.binance.vision/ws"
        self.testnet_api_url = "https://testnet.binance.vision"
        
        # Estado
        self.is_connected = False
        self.is_testnet = True  # Por defecto, usar testnet para seguridad
        self.websocket = None
        self.subscriptions = []
        self.orderbooks = {}
        self.tickers = {}
        
        # Callbacks
        self.data_callback = None
        self.error_callback = None
        
        # Control de reconexión
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 30
        self.reconnect_delay = 5
        self._reconnect_lock = asyncio.Lock()
        self._listen_task = None
        
        logger.info("BinanceAdapter inicializado")
    
    def set_testnet(self, enabled: bool):
        """Establece si se usa el entorno de testnet"""
        self.is_testnet = enabled
        logger.info(f"Testnet: {'activado' if enabled else 'desactivado'}")
    
    def set_data_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Establece el callback para recibir datos"""
        self.data_callback = callback
    
    def set_error_callback(self, callback: Callable[[str, Exception], None]):
        """Establece el callback para errores"""
        self.error_callback = callback
    
    async def connect(self) -> bool:
        """Conecta al WebSocket de Binance"""
        async with self._reconnect_lock:
            # Si ya está conectado, no hacer nada
            if self.is_connected and self.websocket:
                return True
            
            # Resetear estado
            self.websocket = None
            self.is_connected = False
            
            while self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    logger.info(f"Conectando a Binance WebSocket (Intento {self.reconnect_attempts + 1})")
                    
                    # Seleccionar URL según modo
                    ws_url = self.testnet_ws_url if self.is_testnet else self.ws_url
                    
                    # Conectar con opciones mejoradas
                    self.websocket = await websockets.connect(
                        ws_url,
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=10
                    )
                    
                    self.is_connected = True
                    self.reconnect_attempts = 0
                    logger.info(f"Conectado a Binance WebSocket ({('testnet' if self.is_testnet else 'producción')})")
                    
                    # Reactivar suscripciones previas
                    if self.subscriptions:
                        await self._send_subscription()
                    
                    # Iniciar tarea de escucha
                    if self._listen_task and not self._listen_task.done():
                        self._listen_task.cancel()
                    
                    self._listen_task = asyncio.create_task(self._listen_messages())
                    return True
                    
                except Exception as e:
                    self.is_connected = False
                    self.reconnect_attempts += 1
                    
                    error_msg = f"Error conectando a Binance: {str(e)}"
                    logger.error(error_msg)
                    
                    if self.error_callback:
                        self.error_callback("connection_error", e)
                    
                    # Backoff exponencial con límite
                    wait_time = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 300)
                    logger.info(f"Reintentando en {wait_time} segundos...")
                    await asyncio.sleep(wait_time)
            
            logger.error("Número máximo de intentos de reconexión alcanzado")
            return False
    
    async def disconnect(self):
        """Desconecta del WebSocket"""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Desconectado de Binance WebSocket")
            except Exception as e:
                logger.error(f"Error al desconectar de Binance: {e}")
            
            self.websocket = None
            self.is_connected = False
            
            if self._listen_task and not self._listen_task.done():
                self._listen_task.cancel()
    
    async def subscribe_to_ticker(self, symbol: str):
        """Suscribe a actualizaciones de ticker para un símbolo"""
        stream = f"{symbol.lower()}@ticker"
        
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            logger.info(f"Añadida suscripción a ticker: {symbol}")
            
            if self.is_connected:
                await self._send_subscription()
    
    async def subscribe_to_orderbook(self, symbol: str, depth: int = 20):
        """Suscribe a actualizaciones de orderbook para un símbolo"""
        stream = f"{symbol.lower()}@depth{depth}"
        
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            logger.info(f"Añadida suscripción a orderbook: {symbol}")
            
            if self.is_connected:
                await self._send_subscription()
    
    async def subscribe_to_klines(self, symbol: str, interval: str = "1m"):
        """Suscribe a actualizaciones de klines/candlesticks para un símbolo"""
        stream = f"{symbol.lower()}@kline_{interval}"
        
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            logger.info(f"Añadida suscripción a klines {interval}: {symbol}")
            
            if self.is_connected:
                await self._send_subscription()
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de ticker para un símbolo mediante REST API"""
        url = f"{self.testnet_api_url if self.is_testnet else self.api_url}/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_ticker_data(data)
                    else:
                        logger.error(f"Error en la API de Binance: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error obteniendo ticker para {symbol}: {e}")
            return None
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Obtiene datos de orderbook para un símbolo mediante REST API"""
        url = f"{self.testnet_api_url if self.is_testnet else self.api_url}/api/v3/depth"
        params = {"symbol": symbol, "limit": limit}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_orderbook_data(symbol, data)
                    else:
                        logger.error(f"Error en la API de Binance: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error obteniendo orderbook para {symbol}: {e}")
            return None
    
    async def _listen_messages(self):
        """Escucha mensajes del WebSocket"""
        if not self.websocket:
            logger.error("No hay conexión WebSocket establecida")
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decodificando mensaje JSON: {e}")
                except Exception as e:
                    logger.error(f"Error procesando mensaje WebSocket: {e}")
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Conexión WebSocket cerrada correctamente")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Conexión WebSocket cerrada con error: {e}")
            self.is_connected = False
            # Intentar reconectar
            asyncio.create_task(self.connect())
        except Exception as e:
            logger.error(f"Error inesperado en el WebSocket: {e}")
            self.is_connected = False
            # Intentar reconectar
            asyncio.create_task(self.connect())
    
    async def _send_subscription(self):
        """Envía mensaje de suscripción al WebSocket"""
        if not self.websocket or not self.is_connected:
            logger.warning("No se pueden enviar suscripciones: WebSocket no conectado")
            return
        
        try:
            subscription_message = {
                "method": "SUBSCRIBE",
                "params": self.subscriptions,
                "id": int(time.time() * 1000)  # ID único basado en timestamp
            }
            
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"Enviado mensaje de suscripción para {len(self.subscriptions)} streams")
            
        except Exception as e:
            logger.error(f"Error enviando suscripciones: {e}")
            self.is_connected = False
            # Intentar reconectar
            asyncio.create_task(self.connect())
    
    async def _handle_websocket_message(self, data: Dict[str, Any]):
        """Procesa los mensajes recibidos del WebSocket"""
        # Ignorar mensajes de respuesta a suscripciones
        if 'result' in data:
            return
        
        try:
            # Determinar tipo de mensaje
            if 'e' in data:
                event_type = data['e']
                
                if event_type == '24hrTicker':
                    # Ticker de 24h
                    formatted_data = self._format_ticker_ws_data(data)
                    
                    # Almacenar en caché
                    self.tickers[formatted_data['data']['symbol']] = formatted_data['data']
                    
                    # Enviar al callback
                    if self.data_callback:
                        self.data_callback(formatted_data)
                
                elif event_type == 'depthUpdate':
                    # Actualización de orderbook
                    formatted_data = self._format_orderbook_ws_data(data)
                    
                    # Actualizar caché
                    symbol = formatted_data['data']['symbol']
                    if symbol not in self.orderbooks:
                        # Obtener snapshot inicial
                        snapshot = await self.get_orderbook(symbol)
                        if snapshot:
                            self.orderbooks[symbol] = snapshot['data']
                    
                    # Enviar al callback
                    if self.data_callback:
                        self.data_callback(formatted_data)
                
                elif event_type == 'kline':
                    # Datos de klines
                    formatted_data = self._format_kline_data(data)
                    
                    # Enviar al callback
                    if self.data_callback:
                        self.data_callback(formatted_data)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de Binance: {e}")
    
    def _format_ticker_ws_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea datos de ticker recibidos por WebSocket"""
        return {
            "type": "market_data",
            "data": {
                "symbol": data['s'],
                "price": float(data['c']),
                "volume24h": float(data['v']),
                "changePercent24h": float(data['P']),
                "high24h": float(data['h']),
                "low24h": float(data['l']),
                "timestamp": int(data['E']),
                "source": "binance",
                "is_testnet": self.is_testnet
            }
        }
    
    def _format_ticker_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea datos de ticker recibidos por REST API"""
        return {
            "type": "market_data",
            "data": {
                "symbol": data['symbol'],
                "price": float(data['lastPrice']),
                "volume24h": float(data['volume']),
                "changePercent24h": float(data['priceChangePercent']),
                "high24h": float(data['highPrice']),
                "low24h": float(data['lowPrice']),
                "timestamp": int(time.time() * 1000),
                "source": "binance",
                "is_testnet": self.is_testnet,
                "rest_api": True
            }
        }
    
    def _format_orderbook_ws_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea datos de orderbook recibidos por WebSocket"""
        return {
            "type": "orderbook_update",
            "data": {
                "symbol": data['s'],
                "bids": [[float(bid[0]), float(bid[1])] for bid in data['b']],
                "asks": [[float(ask[0]), float(ask[1])] for ask in data['a']],
                "timestamp": int(data['E']),
                "source": "binance",
                "is_testnet": self.is_testnet
            }
        }
    
    def _format_orderbook_data(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea datos de orderbook recibidos por REST API"""
        return {
            "type": "orderbook_data",
            "data": {
                "symbol": symbol,
                "bids": [[float(bid[0]), float(bid[1])] for bid in data['bids']],
                "asks": [[float(ask[0]), float(ask[1])] for ask in data['asks']],
                "timestamp": int(time.time() * 1000),
                "source": "binance",
                "is_testnet": self.is_testnet,
                "rest_api": True
            }
        }
    
    def _format_kline_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea datos de klines recibidos por WebSocket"""
        kline = data['k']
        return {
            "type": "kline_data",
            "data": {
                "symbol": kline['s'],
                "interval": kline['i'],
                "open": float(kline['o']),
                "high": float(kline['h']),
                "low": float(kline['l']),
                "close": float(kline['c']),
                "volume": float(kline['v']),
                "timestamp": int(kline['t']),
                "is_closed": kline['x'],
                "source": "binance",
                "is_testnet": self.is_testnet
            }
        }
