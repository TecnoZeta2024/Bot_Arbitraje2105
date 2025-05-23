"""
WebSocket Manager for multiple cryptocurrency exchanges
Implements real-time data streaming with connection pooling and automatic reconnection
"""

import asyncio
import json
import logging
import ssl
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import websockets


class ExchangeType(Enum):
    """Supported exchanges"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    KUCOIN = "kucoin"
    OKX = "okx"


class StreamType(Enum):
    """Types of data streams"""
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    KLINES = "klines"


class ConnectionStatus(Enum):
    """WebSocket connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class BaseWebSocketClient(ABC):
    """
    Abstract base class for exchange WebSocket clients
    Implements common connection management and error handling
    """
    
    def __init__(self, exchange_type: ExchangeType):
        self.exchange_type = exchange_type
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.websocket = None
        self.subscriptions = set()
        self.callbacks = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.logger = logging.getLogger(f"websocket.{exchange_type.value}")
        
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base WebSocket URL for the exchange"""
        pass
    
    @abstractmethod
    async def format_subscription_message(self, stream_type: StreamType, symbols: List[str]) -> Dict:
        """Format subscription message for specific exchange"""
        pass
    
    @abstractmethod
    async def parse_message(self, message: Dict) -> Optional[Dict]:
        """Parse incoming message from exchange"""
        pass
    
    async def connect(self) -> bool:
        """Establish WebSocket connection"""
        try:
            self.connection_status = ConnectionStatus.CONNECTING
            self.logger.info(f"Connecting to {self.exchange_type.value}...")
            
            # Create SSL context for secure connections
            ssl_context = ssl.create_default_context()
            
            self.websocket = await websockets.connect(
                self.base_url,
                ssl=ssl_context,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connection_status = ConnectionStatus.CONNECTED
            self.reconnect_attempts = 0
            self.logger.info(f"Connected to {self.exchange_type.value}")
            
            # Start message handling loop
            asyncio.create_task(self._message_handler())
            
            return True
            
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(f"Connection failed to {self.exchange_type.value}: {e}")
            return False
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.logger.info(f"Disconnected from {self.exchange_type.value}")
    
    async def subscribe(self, stream_type: StreamType, symbols: List[str], callback: Callable):
        """Subscribe to data stream"""
        subscription_msg = await self.format_subscription_message(stream_type, symbols)
        
        # Store callback for this subscription
        subscription_key = f"{stream_type.value}:{':'.join(symbols)}"
        self.callbacks[subscription_key] = callback
        self.subscriptions.add(subscription_key)
        
        if self.websocket and self.connection_status == ConnectionStatus.CONNECTED:
            await self.websocket.send(json.dumps(subscription_msg))
            self.logger.info(f"Subscribed to {stream_type.value} for {symbols}")
    
    async def _message_handler(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    parsed_data = await self.parse_message(data)
                    
                    if parsed_data:
                        # Route message to appropriate callback
                        await self._route_message(parsed_data)
                        
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning(f"Connection closed to {self.exchange_type.value}")
            await self._handle_disconnection()
        except Exception as e:
            self.logger.error(f"Message handler error: {e}")
            await self._handle_disconnection()
    
    async def _route_message(self, data: Dict):
        """Route parsed message to appropriate callback"""
        stream_type = data.get('stream_type')
        symbol = data.get('symbol')
        
        if stream_type and symbol:
            subscription_key = f"{stream_type}:{symbol}"
            callback = self.callbacks.get(subscription_key)
            
            if callback:
                try:
                    await callback(data)
                except Exception as e:
                    self.logger.error(f"Callback error for {subscription_key}: {e}")
    
    async def _handle_disconnection(self):
        """Handle connection loss and attempt reconnection"""
        self.connection_status = ConnectionStatus.DISCONNECTED
        
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.connection_status = ConnectionStatus.RECONNECTING
            self.logger.info(f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts}")
            
            # Exponential backoff
            await asyncio.sleep(2 ** self.reconnect_attempts)
            
            if await self.connect():
                # Re-subscribe to all previous subscriptions
                await self._resubscribe()
        else:
            self.connection_status = ConnectionStatus.ERROR
            self.logger.error(f"Max reconnection attempts reached for {self.exchange_type.value}")
    
    async def _resubscribe(self):
        """Re-subscribe to all previous subscriptions after reconnection"""
        for subscription_key in list(self.subscriptions):
            stream_type_str, symbols_str = subscription_key.split(':', 1)
            stream_type = StreamType(stream_type_str)
            symbols = symbols_str.split(':')
            callback = self.callbacks[subscription_key]
            
            await self.subscribe(stream_type, symbols, callback)


class ExchangeWebSocketManager:
    """
    Manager for multiple exchange WebSocket connections
    Implements connection pooling and unified interface
    """
    
    def __init__(self):
        self.clients: Dict[ExchangeType, BaseWebSocketClient] = {}
        self.logger = logging.getLogger("websocket.manager")
        
    def add_exchange(self, client: BaseWebSocketClient):
        """Add exchange client to manager"""
        self.clients[client.exchange_type] = client
        self.logger.info(f"Added {client.exchange_type.value} client")
    
    async def connect_all(self) -> Dict[ExchangeType, bool]:
        """Connect to all configured exchanges"""
        results = {}
        
        connection_tasks = [
            self._connect_exchange(exchange_type, client)
            for exchange_type, client in self.clients.items()
        ]
        
        completed_tasks = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        for i, (exchange_type, _) in enumerate(self.clients.items()):
            results[exchange_type] = not isinstance(completed_tasks[i], Exception)
            
        return results
    
    async def _connect_exchange(self, exchange_type: ExchangeType, client: BaseWebSocketClient) -> bool:
        """Connect to specific exchange"""
        try:
            return await client.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect to {exchange_type.value}: {e}")
            return False
    
    async def subscribe_ticker(self, symbols: List[str], callback: Callable, exchanges: Optional[List[ExchangeType]] = None):
        """Subscribe to ticker data across specified exchanges"""
        target_exchanges = exchanges or list(self.clients.keys())
        
        tasks = []
        for exchange_type in target_exchanges:
            if exchange_type in self.clients:
                client = self.clients[exchange_type]
                tasks.append(client.subscribe(StreamType.TICKER, symbols, callback))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe_orderbook(self, symbols: List[str], callback: Callable, exchanges: Optional[List[ExchangeType]] = None):
        """Subscribe to order book data across specified exchanges"""
        target_exchanges = exchanges or list(self.clients.keys())
        
        tasks = []
        for exchange_type in target_exchanges:
            if exchange_type in self.clients:
                client = self.clients[exchange_type]
                tasks.append(client.subscribe(StreamType.ORDERBOOK, symbols, callback))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_connection_status(self) -> Dict[ExchangeType, ConnectionStatus]:
        """Get connection status for all exchanges"""
        return {
            exchange_type: client.connection_status
            for exchange_type, client in self.clients.items()
        }
    
    async def disconnect_all(self):
        """Disconnect from all exchanges"""
        tasks = [
            client.disconnect()
            for client in self.clients.values()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.info("Disconnected from all exchanges")
