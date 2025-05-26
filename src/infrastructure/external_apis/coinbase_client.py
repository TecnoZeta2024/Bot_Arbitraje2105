"""
Cliente WebSocket de Coinbase para datos de mercado en tiempo real.
"""

import asyncio
import json
import logging
import time
from typing import Callable, Dict, List, Optional

import aiohttp
import websockets
from aiohttp import ClientSession

logger = logging.getLogger("CoinbaseWebSocket")

class CoinbaseWebSocketClient:
    def __init__(self, callback_function: Optional[Callable] = None):
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        self.callback = callback_function
        self.subscriptions = []
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 30
        self.reconnect_delay = 5
        self._listen_task = None
        self._reconnect_lock = asyncio.Lock()

    async def connect(self):
        """Conecta al WebSocket de Coinbase con backoff exponencial."""
        async with self._reconnect_lock:
            while self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    logger.info(f"Attempting to connect to Coinbase WebSocket (Attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                    
                    self.websocket = await websockets.connect(
                        self.ws_url,
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=10
                    )
                    
                    self.is_running = True
                    self.reconnect_attempts = 0
                    logger.info("Connected to Coinbase WebSocket")
                    
                    if self.subscriptions:
                        await self.send_subscription()
                    
                    if self._listen_task and not self._listen_task.done():
                        self._listen_task.cancel()
                    
                    self._listen_task = asyncio.create_task(self.listen_messages())
                    return
                    
                except Exception as e:
                    logger.error(f"Error connecting to Coinbase WebSocket: {e}")
                    self.is_running = False
                    self.reconnect_attempts += 1
                    
                    wait_time = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 300)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
            
            logger.error("Max reconnect attempts reached. Could not connect to Coinbase WebSocket.")

    async def listen_messages(self):
        """Escucha mensajes del WebSocket de Coinbase."""
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
            logger.info("Coinbase WebSocket connection closed normally.")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Coinbase WebSocket connection closed with error: {e}")
            self.is_running = False
            await self.connect()
        except Exception as e:
            logger.error(f"Unexpected error in listen_messages: {e}")
            self.is_running = False
            await self.connect()
    
    async def subscribe_orderbook(self, product_ids: List[str], channels: List[str] = ["level2"]):
        """Suscribirse a orderbook (level2) para una lista de product_ids."""
        subscription_message = {
            "type": "subscribe",
            "product_ids": product_ids,
            "channels": channels
        }
        if subscription_message not in self.subscriptions:
            self.subscriptions.append(subscription_message)
            if self.websocket and self.is_running:
                await self.send_subscription()
    
    async def send_subscription(self):
        """Envía la suscripción al WebSocket de Coinbase."""
        if self.websocket and self.subscriptions:
            try:
                # Coinbase requiere enviar cada suscripción individualmente
                for sub_msg in self.subscriptions:
                    await self.websocket.send(json.dumps(sub_msg))
                    logger.info(f"Subscribed to Coinbase streams: {sub_msg}")
                # Limpiar suscripciones enviadas para evitar reenvío
                self.subscriptions = [] 
            except Exception as e:
                logger.error(f"Error sending Coinbase subscription: {e}")
    
    async def close(self):
        """Cierra la conexión WebSocket."""
        self.is_running = False
        
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            
        if self.websocket:
            await self.websocket.close()
            logger.info("Coinbase WebSocket connection closed")

class CoinbaseDataFeeder:
    def __init__(self, api_manager, orderbook_aggregator=None):
        self.api_manager = api_manager
        self.orderbook_aggregator = orderbook_aggregator
        self.coinbase_client = CoinbaseWebSocketClient(self.handle_coinbase_data)
        self.product_ids = [
            "BTC-USD", "ETH-USD"
        ]
        self._running = False
        
    async def start(self):
        """Inicia el feed de datos de Coinbase."""
        self._running = True
        await self.coinbase_client.connect()
        
        await asyncio.sleep(1)
        
        await self.coinbase_client.subscribe_orderbook(self.product_ids, channels=["level2"])
        
        logger.info(f"Started Coinbase data feed for {len(self.product_ids)} product IDs")
    
    async def handle_coinbase_data(self, data: Dict):
        """Procesa datos de Coinbase y los envía al agregador."""
        try:
            if not self._running:
                return
            
            # Coinbase level2 updates can be 'l2update' or 'snapshot'
            if data.get('type') == 'l2update':
                orderbook_data = {
                    "type": "orderbook_update",
                    "data": {
                        "symbol": data['product_id'],
                        "bids": [[float(price), float(size)] for side, price, size in data['changes'] if side == 'buy'],
                        "asks": [[float(price), float(size)] for side, price, size in data['changes'] if side == 'sell'],
                        "timestamp": int(time.time() * 1000) # Coinbase provides time in ISO format, convert to ms
                    }
                }
                
                if self.orderbook_aggregator:
                    await self.orderbook_aggregator.process_coinbase_orderbook_update(orderbook_data)
                
                await self.api_manager.broadcast(orderbook_data) # Broadcast to frontend if needed
            
            elif data.get('type') == 'snapshot':
                # Initial snapshot of the orderbook
                orderbook_data = {
                    "type": "orderbook_snapshot",
                    "data": {
                        "symbol": data['product_id'],
                        "bids": [[float(bid[0]), float(bid[1])] for bid in data['bids']],
                        "asks": [[float(ask[0]), float(ask[1])] for ask in data['asks']],
                        "timestamp": int(time.time() * 1000)
                    }
                }
                
                if self.orderbook_aggregator:
                    await self.orderbook_aggregator.process_coinbase_orderbook_snapshot(orderbook_data)
                
                await self.api_manager.broadcast(orderbook_data) # Broadcast to frontend if needed

        except Exception as e:
            logger.error(f"Error processing Coinbase data: {e}", exc_info=True)
    
    async def stop(self):
        """Detiene el feed de datos."""
        self._running = False
        await self.coinbase_client.close()

async def initialize_coinbase_feed(api_manager):
    """Inicializa el feed de Coinbase en el API server."""
    coinbase_feeder = CoinbaseDataFeeder(api_manager)
    await coinbase_feeder.start()
    return coinbase_feeder
