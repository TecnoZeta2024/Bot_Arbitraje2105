"""
Cliente WebSocket de Binance para datos de mercado en tiempo real
Integración con Bot_Arbitraje2105 - Frontend-First Visibility
"""

import asyncio
import json
import logging
from typing import Callable, Dict, List, Optional

import aiohttp
import websockets

logger = logging.getLogger("BinanceWebSocket")

class BinanceWebSocketClient:
    def __init__(self, callback_function: Optional[Callable] = None):
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.callback = callback_function
        self.subscriptions = []
        self.websocket = None
        self.is_running = False
        
    async def connect(self):
        """Conecta al WebSocket de Binance"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_running = True
            logger.info("Connected to Binance WebSocket")
            
            # Escuchar mensajes en background
            asyncio.create_task(self.listen_messages())
            
        except Exception as e:
            logger.error(f"Error connecting to Binance WebSocket: {e}")
    
    async def listen_messages(self):
        """Escucha mensajes del WebSocket"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if self.callback:
                    await self.callback(data)
        except Exception as e:
            logger.error(f"Error listening to messages: {e}")
            self.is_running = False
    
    async def subscribe_ticker(self, symbol: str):
        """Suscribirse a ticker de un símbolo"""
        stream = f"{symbol.lower()}@ticker"
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            await self.send_subscription()
    
    async def subscribe_kline(self, symbol: str, interval: str = "1m"):
        """Suscribirse a klines/candlesticks"""
        stream = f"{symbol.lower()}@kline_{interval}"
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            await self.send_subscription()
    
    async def subscribe_orderbook(self, symbol: str, levels: int = 20):
        """Suscribirse a orderbook"""
        stream = f"{symbol.lower()}@depth{levels}"
        if stream not in self.subscriptions:
            self.subscriptions.append(stream)
            await self.send_subscription()
    
    async def send_subscription(self):
        """Envía la suscripción al WebSocket"""
        if self.websocket and self.subscriptions:
            subscription_message = {
                "method": "SUBSCRIBE",
                "params": self.subscriptions,
                "id": 1
            }
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"Subscribed to {len(self.subscriptions)} streams")
    
    async def get_24hr_ticker_stats(self) -> Dict:
        """Obtiene estadísticas de 24hr via REST API"""
        url = "https://api.binance.com/api/v3/ticker/24hr"
        
        try:
            async with aiohttp.ClientSession() as session:
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
        if self.websocket:
            await self.websocket.close()
            logger.info("Binance WebSocket connection closed")

# Cliente integrado para el API Server
class BinanceDataFeeder:
    def __init__(self, api_manager):
        self.api_manager = api_manager  # ConnectionManager del API server
        self.binance_client = BinanceWebSocketClient(self.handle_binance_data)
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
            "BNBUSDT", "XRPUSDT", "LTCUSDT", "SOLUSDT", "AVAXUSDT"
        ]
        
    async def start(self):
        """Inicia el feed de datos de Binance"""
        await self.binance_client.connect()
        
        # Suscribirse a todos los símbolos
        for symbol in self.symbols:
            await self.binance_client.subscribe_ticker(symbol)
            await self.binance_client.subscribe_kline(symbol, "1m")
            await self.binance_client.subscribe_orderbook(symbol, 10)
        
        logger.info(f"Started Binance data feed for {len(self.symbols)} symbols")
    
    async def handle_binance_data(self, data: Dict):
        """Procesa datos de Binance y los envía al frontend"""
        try:
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
                    
                    await self.api_manager.broadcast_json(market_data)
                
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
                        
                        await self.api_manager.broadcast_json(candle_data)
                
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
                    
                    await self.api_manager.broadcast_json(orderbook_data)
                    
        except Exception as e:
            logger.error(f"Error processing Binance data: {e}")
    
    async def stop(self):
        """Detiene el feed de datos"""
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
