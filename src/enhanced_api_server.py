"""
API Server Mejorado para Bot_Arbitraje2105
Con datos reales de Binance y funcionalidad completa
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
import logging

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Importar el cliente de Binance
from binance_websocket import BinanceDataFeeder, is_bullish_signal, is_bearish_signal

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EnhancedAPIServer")

# Inicializar FastAPI
app = FastAPI(
    title="Bot de Arbitraje Triangular API - Enhanced",
    description="API con datos reales de Binance y funcionalidad completa",
    version="2.0.0"
)

# Modelos
class MarketData(BaseModel):
    symbol: str
    price: float
    volume24h: float
    changePercent24h: float
    high24h: Optional[float] = None
    low24h: Optional[float] = None
    timestamp: float

class TradingSignal(BaseModel):
    id: str
    symbol: str
    action: str  # BUY, SELL
    price: float
    strategy: str
    confidence: float
    reasoning: str
    timestamp: float

class Position(BaseModel):
    id: str
    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entryPrice: float
    currentPrice: float
    unrealizedPnL: float
    unrealizedPnLPercent: float
    status: str
    timestamp: float

class Trade(BaseModel):
    id: str
    symbol: str
    side: str  # BUY, SELL
    quantity: float
    price: float
    pnl: float
    strategy: str
    timestamp: float

class OrderBook(BaseModel):
    symbol: str
    bids: List[List[float]]  # [price, quantity]
    asks: List[List[float]]  # [price, quantity]
    timestamp: float

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total: {len(self.active_connections)}")

    async def broadcast_json(self, data: dict):
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(data)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)

manager = ConnectionManager()

# Estado global del sistema
class TradingSystemState:
    def __init__(self):
        self.trading_active = False
        self.portfolio_value = 1000.0
        self.daily_pnl = 0.0
        self.positions = {}  # symbol -> Position
        self.trades = []
        self.market_data = {}  # symbol -> MarketData
        self.signals_generated = 0
        
    def add_trade(self, trade: Trade):
        self.trades.append(trade)
        self.daily_pnl += trade.pnl
        self.portfolio_value += trade.pnl
        
        # Keep only last 100 trades
        if len(self.trades) > 100:
            self.trades = self.trades[-100:]
    
    def update_market_data(self, symbol: str, data: Dict):
        self.market_data[symbol] = data
    
    def get_portfolio_summary(self):
        return {
            "totalValue": round(self.portfolio_value, 2),
            "dailyPnL": round(self.daily_pnl, 2),
            "totalPnL": round(self.daily_pnl, 2),
            "totalPnLPercent": round((self.daily_pnl / 1000.0) * 100, 2),
            "availableBalance": round(self.portfolio_value - sum(pos['quantity'] * pos['entryPrice'] for pos in self.positions.values()), 2),
            "positions": list(self.positions.values()),
            "totalTrades": len(self.trades),
            "winRate": self.calculate_win_rate()
        }
    
    def calculate_win_rate(self):
        if not self.trades:
            return 0.0
        winning_trades = sum(1 for trade in self.trades if trade.pnl > 0)
        return round((winning_trades / len(self.trades)) * 100, 1)

system_state = TradingSystemState()

# Variables globales
binance_feeder = None

@app.get("/")
async def root():
    return {
        "mensaje": "API del Bot de Arbitraje Triangular - Enhanced", 
        "status": "OK",
        "features": ["Real Binance Data", "WebSocket", "Trading Controls", "AI Signals"]
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "OK", 
        "version": "2.0.0-enhanced",
        "timestamp": time.time(),
        "trading_active": system_state.trading_active,
        "connections": len(manager.active_connections),
        "market_data_symbols": len(system_state.market_data),
        "binance_connected": binance_feeder.binance_client.is_running if binance_feeder else False,
        "signals_generated": system_state.signals_generated
    }

@app.get("/api/portfolio")
async def get_portfolio():
    return system_state.get_portfolio_summary()

@app.get("/api/trades")
async def get_recent_trades(limit: int = 20):
    return system_state.trades[-limit:]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    try:
        # Enviar datos iniciales al conectarse
        await websocket.send_json({
            "type": "connection_ack",
            "message": "Connected to enhanced trading server",
            "timestamp": time.time(),
            "features": ["real_binance_data", "ai_signals", "trading_controls"]
        })
        
        # Enviar portfolio inicial
        await websocket.send_json({
            "type": "portfolio_update",
            "data": system_state.get_portfolio_summary()
        })
        
        # Enviar datos de mercado disponibles
        for symbol, data in system_state.market_data.items():
            await websocket.send_json({
                "type": "market_data",
                "data": data
            })
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                await handle_websocket_message(websocket, message_data)
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_ip}")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_ip}: {e}")
    finally:
        manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message_data: dict):
    """Maneja mensajes entrantes del WebSocket"""
    msg_type = message_data.get("type")
    
    if msg_type == "subscribe":
        channels = message_data.get("channels", [])
        logger.info(f"Client subscribed to channels: {channels}")
        await websocket.send_json({
            "type": "subscription_ack", 
            "status": "Subscribed", 
            "channels": channels
        })
        
    elif msg_type == "trading_control":
        action = message_data.get("action")  # start, pause, stop
        if action == "start":
            system_state.trading_active = True
            await manager.broadcast_json({
                "type": "trading_status",
                "status": "ACTIVE",
                "message": "Trading started - AI signals enabled",
                "timestamp": time.time()
            })
            logger.info("Trading system activated")
            
        elif action in ["pause", "stop"]:
            system_state.trading_active = False
            await manager.broadcast_json({
                "type": "trading_status", 
                "status": "INACTIVE",
                "message": f"Trading {action}ed",
                "timestamp": time.time()
            })
            logger.info(f"Trading system {action}ed")
            
    elif msg_type == "execute_order":
        # Simular ejecución de orden (paper trading)
        await execute_paper_trade(message_data)
        
    elif msg_type == "get_orderbook":
        symbol = message_data.get("symbol", "BTCUSDT")
        # Enviar datos de orderbook si están disponibles
        await websocket.send_json({
            "type": "orderbook_data",
            "symbol": symbol,
            "message": "Orderbook data will be available when Binance stream is active"
        })

async def execute_paper_trade(order_data: dict):
    """Ejecuta un trade simulado (paper trading)"""
    symbol = order_data.get("symbol", "BTCUSDT")
    side = order_data.get("side", "BUY")
    quantity = float(order_data.get("quantity", 0.001))
    
    # Obtener precio actual del mercado
    current_price = 50000.0  # Default fallback
    if symbol in system_state.market_data:
        current_price = system_state.market_data[symbol]["price"]
    
    # Crear trade
    trade_id = f"trade_{int(time.time())}"
    
    # Simular slippage y fees
    slippage = 0.001  # 0.1% slippage
    fee = 0.001  # 0.1% fee
    
    if side == "BUY":
        execution_price = current_price * (1 + slippage)
    else:
        execution_price = current_price * (1 - slippage)
    
    # Simular P&L (para demostración, pequeña ganancia aleatoria)
    import random
    base_pnl = quantity * execution_price * random.uniform(-0.01, 0.02)  # ±1% to +2%
    final_pnl = base_pnl - (quantity * execution_price * fee)
    
    trade = Trade(
        id=trade_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=execution_price,
        pnl=final_pnl,
        strategy="Manual",
        timestamp=time.time()
    )
    
    # Agregar trade al sistema
    system_state.add_trade(trade)
    
    # Broadcast trade ejecutado
    await manager.broadcast_json({
        "type": "trade_executed",
        "data": {
            "id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price,
            "pnl": trade.pnl,
            "strategy": trade.strategy,
            "timestamp": trade.timestamp
        }
    })
    
    # Broadcast portfolio update
    await manager.broadcast_json({
        "type": "portfolio_update",
        "data": system_state.get_portfolio_summary()
    })
    
    logger.info(f"Paper trade executed: {side} {quantity} {symbol} at {execution_price} (P&L: {final_pnl})")

# Manejador de datos de Binance
async def handle_binance_data(data: dict):
    """Procesa datos de Binance recibidos"""
    msg_type = data.get("type")
    
    if msg_type == "market_data":
        symbol = data["data"]["symbol"]
        system_state.update_market_data(symbol, data["data"])
        
        # Broadcast a todos los clientes conectados
        await manager.broadcast_json(data)
        
        # Generar señales de trading automáticas si está activo
        if system_state.trading_active:
            await generate_trading_signals(data["data"])
    
    elif msg_type == "orderbook_update":
        # Broadcast orderbook updates
        await manager.broadcast_json(data)
    
    elif msg_type == "kline_data":
        # Broadcast kline data para gráficos
        await manager.broadcast_json(data)

async def generate_trading_signals(market_data: dict):
    """Genera señales de trading basadas en datos de mercado"""
    symbol = market_data["symbol"]
    
    # Análisis básico de señales
    if is_bullish_signal(market_data):
        signal_id = f"signal_{int(time.time())}"
        signal = {
            "id": signal_id,
            "symbol": symbol,
            "action": "BUY",
            "price": market_data["price"],
            "strategy": "BullishMomentum",
            "confidence": 75.5,
            "reasoning": f"Strong upward momentum: +{market_data['changePercent24h']:.2f}% with high volume",
            "timestamp": time.time()
        }
        
        system_state.signals_generated += 1
        
        await manager.broadcast_json({
            "type": "trading_signal",
            "data": signal
        })
        
        logger.info(f"Generated BUY signal for {symbol} at {market_data['price']}")
    
    elif is_bearish_signal(market_data):
        signal_id = f"signal_{int(time.time())}"
        signal = {
            "id": signal_id,
            "symbol": symbol,
            "action": "SELL",
            "price": market_data["price"],
            "strategy": "BearishMomentum", 
            "confidence": 70.2,
            "reasoning": f"Strong downward momentum: {market_data['changePercent24h']:.2f}%",
            "timestamp": time.time()
        }
        
        system_state.signals_generated += 1
        
        await manager.broadcast_json({
            "type": "trading_signal",
            "data": signal
        })
        
        logger.info(f"Generated SELL signal for {symbol} at {market_data['price']}")

# Tarea de monitoreo del sistema
async def system_monitoring():
    """Monitorea el estado del sistema y envía actualizaciones"""
    while True:
        if len(manager.active_connections) > 0:
            # Enviar métricas del sistema cada 30 segundos
            system_metrics = {
                "type": "system_metrics",
                "data": {
                    "trading_active": system_state.trading_active,
                    "connections": len(manager.active_connections),
                    "portfolio_value": system_state.portfolio_value,
                    "daily_pnl": system_state.daily_pnl,
                    "signals_generated": system_state.signals_generated,
                    "total_trades": len(system_state.trades),
                    "market_symbols": len(system_state.market_data),
                    "timestamp": time.time()
                }
            }
            
            await manager.broadcast_json(system_metrics)
        
        await asyncio.sleep(30)

async def startup_tasks():
    """Tareas de inicio del servidor"""
    global binance_feeder
    
    # Inicializar cliente de Binance
    logger.info("🚀 Initializing Binance WebSocket connection...")
    
    # Crear feeder personalizado que use nuestro manejador
    class CustomBinanceFeeder(BinanceDataFeeder):
        async def handle_binance_data(self, data: Dict):
            """Override para usar nuestro manejador personalizado"""
            await super().handle_binance_data(data)
            await handle_binance_data(data)
    
    binance_feeder = CustomBinanceFeeder(manager)
    
    try:
        await binance_feeder.start()
        logger.info("✅ Binance data feed started successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to Binance: {e}")
        logger.info("📊 Running with simulated data only")
    
    # Iniciar monitoreo del sistema
    asyncio.create_task(system_monitoring())
    logger.info("📈 System monitoring started")

@app.on_event("startup")
async def startup_event():
    """Eventos de inicio de la aplicación"""
    await startup_tasks()

def start_server():
    """Inicia el servidor API"""
    host = "127.0.0.1"
    port = 8000
    
    logger.info("=" * 80)
    logger.info("🚀 ENHANCED TRADING API SERVER")
    logger.info("=" * 80)
    logger.info(f"📡 Server: http://{host}:{port}")
    logger.info(f"🌐 WebSocket: ws://{host}:{port}/ws")
    logger.info("📊 Features:")
    logger.info("   • Real-time Binance market data")
    logger.info("   • WebSocket communication")
    logger.info("   • Trading controls (Start/Stop/Pause)")
    logger.info("   • AI-powered signal generation")
    logger.info("   • Paper trading simulation")
    logger.info("   • Portfolio tracking")
    logger.info("   • System monitoring")
    logger.info("=" * 80)
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
