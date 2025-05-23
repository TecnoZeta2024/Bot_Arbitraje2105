"""
Cliente WebSocket de Binance para datos de mercado en tiempo real
Integración con Bot_Arbitraje2105 - Frontend-First Visibility
Version mejorada con mejor manejo de reconexión
"""

import asyncio
import json
import logging
import time
from typing import Callable, Dict, List, Optional

import aiohttp
import websockets
from aiohttp import ClientSession

logger = logging.getLogger("BinanceWebSocket")

class BinanceWebSocketClient:
    def __init__(self, callback_function: Optional[Callable] = None):
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.callback = callback_function
        self.subscriptions = []
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 30
        self.reconnect_delay = 5  # Reducir a 5 segundos inicial
        self._listen_task = None
        self._reconnect_lock = asyncio.Lock()

    async def connect(self):
        """Conecta al WebSocket de Binance con backoff exponencial mejorado"""
        async with self._reconnect_lock:
            while self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    logger.info(f"Attempting to connect to Binance WebSocket (Attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                    
                    # Configurar timeout y opciones de conexión
                    self.websocket = await websockets.connect(
                        self.ws_url,
                        ping_interval=20,  # Enviar ping cada 20 segundos
                        ping_timeout=10,   # Timeout de 10 segundos para el pong
                        close_timeout=10   # Timeout para cerrar conexión
                    )
                    
                    self.is_running = True
                    self.reconnect_attempts = 0
                    logger.info("Connected to Binance WebSocket")
                    
                    # Re-suscribir a los streams después de reconectar
                    if self.subscriptions:
                        await self.send_subscription()
                    
                    # Cancelar tarea anterior si existe
                    if self._listen_task and not self._listen_task.done():
                        self._listen_task.cancel()
                    
                    # Escuchar mensajes en background
                    self._listen_task = asyncio.create_task(self.listen_messages())
                    return
                    
                except Exception as e:
                    logger.error(f"Error connecting to Binance WebSocket: {e}")
                    self.is_running = False
                    self.reconnect_attempts += 1
                    
                    # Backoff exponencial con límite máximo
                    wait_time = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 300)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
            
            logger.error("Max reconnect attempts reached. Could not connect to Binance WebSocket.")

    async def listen_messages(self):
        """Escucha mensajes del WebSocket con mejor manejo de errores"""
        if not self.websocket:
            logger.error("WebSocket is not connected. Cannot listen for messages.")
            return

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    if self.callback:
                        await self.callback(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Binance WebSocket connection closed normally.")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Binance WebSocket connection closed with error: {e}")
            self.is_running = False
            await self.connect()  # Intentar reconectar
        except Exception as e:
            logger.error(f"Unexpected error in listen_messages: {e}")
            self.is_running = False
            await self.connect()  # Intentar reconectar
    
    async def subscribe_ticker(self, symbol: str):
        """Suscribirse a ticker de un símbolo"""
        stream = f"{symbol.lower()}@ticker"
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            if self.websocket and self.is_running:
                await self.send_subscription()
    
    async def subscribe_kline(self, symbol: str, interval: str = "1m"):
        """Suscribirse a klines/candlesticks"""
        stream = f"{symbol.lower()}@kline_{interval}"
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            if self.websocket and self.is_running:
                await self.send_subscription()
    
    async def subscribe_orderbook(self, symbol: str, levels: int = 20):
        """Suscribirse a orderbook"""
        stream = f"{symbol.lower()}@depth{levels}"
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            if self.websocket and self.is_running:
                await self.send_subscription()
    
    async def send_subscription(self):
        """Envía la suscripción al WebSocket con manejo de errores"""
        if self.websocket and self.subscriptions:
            try:
                subscription_message = {
                    "method": "SUBSCRIBE",
                    "params": self.subscriptions,
                    "id": 1
                }
                await self.websocket.send(json.dumps(subscription_message))
                logger.info(f"Subscribed to {len(self.subscriptions)} streams")
            except Exception as e:
                logger.error(f"Error sending subscription: {e}")
    
    async def get_24hr_ticker_stats(self) -> Dict:
        """Obtiene estadísticas de 24hr via REST API"""
        url = "https://api.binance.com/api/v3/ticker/24hr"
        
        try:
            async with ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching 24hr stats: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error in REST API call: {e}")
            return {}
    
    async def close(self):
        """Cierra la conexión WebSocket"""
        self.is_running = False
        
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            
        if self.websocket:
            await self.websocket.close()
            logger.info("Binance WebSocket connection closed")

# Cliente integrado para el API Server
class BinanceDataFeeder:
    def __init__(self, api_manager):
        self.api_manager = api_manager  # ConnectionManager del API server
        self.binance_client = BinanceWebSocketClient(self.handle_binance_data)
        self.symbols = [
            "BTCUSDT", "ETHUSDT"  # Empezar con solo 2 símbolos
        ]
        self._running = False
        
    async def start(self):
        """Inicia el feed de datos de Binance"""
        self._running = True
        await self.binance_client.connect()
        
        # Esperar un poco para asegurar la conexión
        await asyncio.sleep(1)
        
        # Suscribirse a todos los símbolos
        for symbol in self.symbols:
            await self.binance_client.subscribe_ticker(symbol)
            await asyncio.sleep(0.1)  # Pequeño delay entre suscripciones
        
        logger.info(f"Started Binance data feed for {len(self.symbols)} symbols")
    
    async def handle_binance_data(self, data: Dict):
        """Procesa datos de Binance y los envía al frontend"""
        try:
            if not self._running:
                return
                
            if 'e' in data:  # Event type
                event_type = data['e']
                
                if event_type == '24hrTicker':
                    # Datos de ticker 24hr
                    market_data = {
                        "type": "market_data",
                        "data": {
                            "symbol": data['s'],
                            "price": float(data['c']),  # Close price
                            "volume24h": float(data['v']),  # Volume
                            "changePercent24h": float(data['P']),  # Price change percent
                            "high24h": float(data['h']),  # High price
                            "low24h": float(data['l']),   # Low price
                            "timestamp": int(data['E'])   # Event time
                        }
                    }
                    
                    # Usar el método correcto: broadcast
                    await self.api_manager.broadcast(market_data)
                    logger.debug(f"Broadcasted market data for {data['s']}")
                
                elif event_type == 'kline':
                    # Datos de candlesticks
                    kline_data = data['k']
                    if kline_data['x']:  # Kline is closed
                        candle_data = {
                            "type": "kline_data",
                            "data": {
                                "symbol": kline_data['s'],
                                "interval": kline_data['i'],
                                "open": float(kline_data['o']),
                                "high": float(kline_data['h']),
                                "low": float(kline_data['l']),
                                "close": float(kline_data['c']),
                                "volume": float(kline_data['v']),
                                "timestamp": int(kline_data['t'])
                            }
                        }
                        
                        await self.api_manager.broadcast(candle_data)
                
                elif event_type == 'depthUpdate':
                    # Datos de orderbook
                    orderbook_data = {
                        "type": "orderbook_update",
                        "data": {
                            "symbol": data['s'],
                            "bids": [[float(bid[0]), float(bid[1])] for bid in data['b'][:10]],
                            "asks": [[float(ask[0]), float(ask[1])] for ask in data['a'][:10]],
                            "timestamp": int(data['E'])
                        }
                    }
                    
                    await self.api_manager.broadcast(orderbook_data)
                    
        except Exception as e:
            logger.error(f"Error processing Binance data: {e}", exc_info=True)
    
    async def stop(self):
        """Detiene el feed de datos"""
        self._running = False
        await self.binance_client.close()

# Función para integrar con el API server existente
async def initialize_binance_feed(api_manager):
    """Inicializa el feed de Binance en el API server"""
    binance_feeder = BinanceDataFeeder(api_manager)
    await binance_feeder.start()
    return binance_feeder

# Funciones de utilidad para análisis técnico básico
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calcula RSI"""
    if len(prices) < period:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50.0
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def is_bullish_signal(data: Dict) -> bool:
    """Detecta señales alcistas básicas"""
    try:
        price = float(data.get('price', 0))
        change_pct = float(data.get('changePercent24h', 0))
        volume = float(data.get('volume24h', 0))
        
        # Señales básicas:
        # 1. Precio subiendo más de 1%
        # 2. Volumen alto (más de 100M para major coins)
        return change_pct > 1.0 and volume > 100000000
        
    except:
        return False

def is_bearish_signal(data: Dict) -> bool:
    """Detecta señales bajistas básicas"""
    try:
        change_pct = float(data.get('changePercent24h', 0))
        return change_pct < -2.0
        
    except:
        return False
