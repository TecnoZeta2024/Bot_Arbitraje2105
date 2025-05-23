"""
Binance WebSocket Client Implementation
Handles real-time data streaming from Binance API
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .websocket_manager import BaseWebSocketClient, ExchangeType, StreamType


class BinanceWebSocketClient(BaseWebSocketClient):
    """
    Binance-specific WebSocket client implementation
    Supports ticker, orderbook, trades, and klines streams
    """
    
    def __init__(self):
        super().__init__(ExchangeType.BINANCE)
        self._stream_counter = 0
    
    @property
    def base_url(self) -> str:
        """Binance WebSocket stream endpoint"""
        return "wss://stream.binance.com:9443/ws/"
    
    async def format_subscription_message(self, stream_type: StreamType, symbols: List[str]) -> Dict:
        """
        Format subscription message for Binance API
        
        Binance uses combined streams: /ws/<streamName1>/<streamName2>/<streamName3>
        """
        streams = []
        
        for symbol in symbols:
            symbol_lower = symbol.lower()
            
            if stream_type == StreamType.TICKER:
                streams.append(f"{symbol_lower}@ticker")
            elif stream_type == StreamType.ORDERBOOK:
                streams.append(f"{symbol_lower}@depth10@100ms")  # 10 levels, 100ms updates
            elif stream_type == StreamType.TRADES:
                streams.append(f"{symbol_lower}@trade")
            elif stream_type == StreamType.KLINES:
                streams.append(f"{symbol_lower}@kline_1m")  # 1-minute klines
        
        # Binance subscription message format
        return {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": self._get_next_id()
        }
    
    async def parse_message(self, message: Dict) -> Optional[Dict]:
        """
        Parse incoming message from Binance WebSocket
        
        Returns standardized format regardless of stream type
        """
        try:
            # Skip subscription confirmation messages
            if "result" in message or "id" in message:
                return None
            
            # Extract stream name and data
            stream = message.get("stream", "")
            data = message.get("data", {})
            
            if not stream or not data:
                return None
            
            # Parse based on stream type
            if "@ticker" in stream:
                return await self._parse_ticker_data(stream, data)
            elif "@depth" in stream:
                return await self._parse_orderbook_data(stream, data)
            elif "@trade" in stream:
                return await self._parse_trade_data(stream, data)
            elif "@kline" in stream:
                return await self._parse_kline_data(stream, data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing Binance message: {e}")
            return None
    
    async def _parse_ticker_data(self, stream: str, data: Dict) -> Dict:
        """Parse ticker data from Binance"""
        symbol = data.get("s", "")
        
        return {
            "exchange": "binance",
            "stream_type": "ticker",
            "symbol": symbol,
            "timestamp": datetime.fromtimestamp(data.get("E", 0) / 1000),
            "price": Decimal(data.get("c", "0")),  # Current close price
            "price_change": Decimal(data.get("p", "0")),  # Price change
            "price_change_percent": Decimal(data.get("P", "0")),  # Price change percent
            "volume": Decimal(data.get("v", "0")),  # 24h volume
            "high_24h": Decimal(data.get("h", "0")),  # 24h high
            "low_24h": Decimal(data.get("l", "0")),  # 24h low
            "open_24h": Decimal(data.get("o", "0")),  # 24h open
            "bid_price": Decimal(data.get("b", "0")),  # Best bid price
            "ask_price": Decimal(data.get("a", "0")),  # Best ask price
            "bid_qty": Decimal(data.get("B", "0")),  # Best bid quantity
            "ask_qty": Decimal(data.get("A", "0")),  # Best ask quantity
            "count": int(data.get("n", 0)),  # Trade count
            "raw_data": data
        }
    
    async def _parse_orderbook_data(self, stream: str, data: Dict) -> Dict:
        """Parse order book data from Binance"""
        symbol = stream.split("@")[0].upper()
        
        # Parse bids and asks
        bids = [
            {"price": Decimal(bid[0]), "quantity": Decimal(bid[1])}
            for bid in data.get("bids", [])
        ]
        
        asks = [
            {"price": Decimal(ask[0]), "quantity": Decimal(ask[1])}
            for ask in data.get("asks", [])
        ]
        
        return {
            "exchange": "binance",
            "stream_type": "orderbook",
            "symbol": symbol,
            "timestamp": datetime.fromtimestamp(data.get("E", 0) / 1000),
            "bids": bids,
            "asks": asks,
            "last_update_id": data.get("lastUpdateId"),
            "raw_data": data
        }
    
    async def _parse_trade_data(self, stream: str, data: Dict) -> Dict:
        """Parse trade data from Binance"""
        symbol = data.get("s", "")
        
        return {
            "exchange": "binance",
            "stream_type": "trades",
            "symbol": symbol,
            "timestamp": datetime.fromtimestamp(data.get("T", 0) / 1000),
            "trade_id": data.get("t"),
            "price": Decimal(data.get("p", "0")),
            "quantity": Decimal(data.get("q", "0")),
            "buyer_order_id": data.get("b"),
            "seller_order_id": data.get("a"),
            "trade_time": datetime.fromtimestamp(data.get("T", 0) / 1000),
            "is_buyer_maker": data.get("m", False),
            "raw_data": data
        }
    
    async def _parse_kline_data(self, stream: str, data: Dict) -> Dict:
        """Parse kline (candlestick) data from Binance"""
        kline = data.get("k", {})
        symbol = kline.get("s", "")
        
        return {
            "exchange": "binance",
            "stream_type": "klines",
            "symbol": symbol,
            "timestamp": datetime.fromtimestamp(kline.get("t", 0) / 1000),
            "open_time": datetime.fromtimestamp(kline.get("t", 0) / 1000),
            "close_time": datetime.fromtimestamp(kline.get("T", 0) / 1000),
            "open_price": Decimal(kline.get("o", "0")),
            "high_price": Decimal(kline.get("h", "0")),
            "low_price": Decimal(kline.get("l", "0")),
            "close_price": Decimal(kline.get("c", "0")),
            "volume": Decimal(kline.get("v", "0")),
            "trade_count": int(kline.get("n", 0)),
            "interval": kline.get("i", "1m"),
            "is_closed": kline.get("x", False),  # Whether this kline is closed
            "quote_volume": Decimal(kline.get("q", "0")),
            "taker_buy_volume": Decimal(kline.get("V", "0")),
            "taker_buy_quote_volume": Decimal(kline.get("Q", "0")),
            "raw_data": data
        }
    
    def _get_next_id(self) -> int:
        """Get next subscription ID"""
        self._stream_counter += 1
        return self._stream_counter
    
    async def subscribe_combined_stream(self, streams: List[str], callback):
        """
        Subscribe to multiple streams in a single connection
        Binance-specific optimization for multiple subscriptions
        """
        if len(streams) > 1:
            # Use combined stream endpoint for multiple streams
            combined_url = f"{self.base_url.rstrip('/')}/{'/'.join(streams)}"
            
            # Override base_url temporarily for this connection
            original_url = self.base_url
            self.base_url = combined_url
            
            try:
                success = await self.connect()
                if success:
                    # Store callback for all streams
                    for stream in streams:
                        # Extract symbol and stream type from stream name
                        parts = stream.split('@')
                        if len(parts) >= 2:
                            symbol = parts[0].upper()
                            stream_type = parts[1].split('_')[0]  # Remove interval if present
                            
                            subscription_key = f"{stream_type}:{symbol}"
                            self.callbacks[subscription_key] = callback
                            self.subscriptions.add(subscription_key)
                
                return success
                
            finally:
                # Restore original URL
                self.base_url = original_url
        else:
            # Single stream subscription
            return await self.connect()


# Example usage and configuration
BINANCE_STREAM_EXAMPLES = {
    "ticker_streams": [
        "btcusdt@ticker",
        "ethusdt@ticker",
        "adausdt@ticker"
    ],
    "orderbook_streams": [
        "btcusdt@depth10@100ms",
        "ethusdt@depth10@100ms"
    ],
    "kline_streams": [
        "btcusdt@kline_1m",
        "ethusdt@kline_1m",
        "btcusdt@kline_5m"
    ]
}
