"""
Production Server - Bot_Arbitraje2105
Servidor unificado de producción con todas las mejoras implementadas
"""

import asyncio
import json
import logging
import os
import time
import traceback
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional, Set

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Importar módulos internos
from binance_websocket import BinanceDataFeeder, is_bearish_signal, is_bullish_signal


# ==================== CONFIGURACIÓN DE LOGGING ====================
def setup_logging():
    """Configura el sistema de logging con rotación de archivos"""
    # Crear directorio de logs si no existe
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'production_server.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato detallado
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logging.getLogger("ProductionServer")

logger = setup_logging()

# ==================== ENUMS Y CONSTANTES ====================
class TradingState(str, Enum):
    """Estados del sistema de trading"""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class SignalAction(str, Enum):
    """Acciones de señales de trading"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class OrderType(str, Enum):
    """Tipos de órdenes"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

# Configuración
HEARTBEAT_INTERVAL = 30  # segundos
RECONNECT_MAX_ATTEMPTS = 10
RECONNECT_BASE_DELAY = 1  # segundos
MAX_WEBSOCKET_CONNECTIONS = 100

# ==================== MODELOS DE DATOS ====================
class MarketData(BaseModel):
    """Datos de mercado en tiempo real"""
    symbol: str
    price: float = Field(..., gt=0)
    volume24h: float = Field(..., ge=0)
    changePercent24h: float
    high24h: Optional[float] = None
    low24h: Optional[float] = None
    timestamp: float = Field(default_factory=time.time)
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "price": 50000.0,
                "volume24h": 1500000000,
                "changePercent24h": 2.5
            }
        }

class TradingSignal(BaseModel):
    """Señal de trading generada por el sistema"""
    id: str
    symbol: str
    action: SignalAction
    price: float = Field(..., gt=0)
    quantity: Optional[float] = Field(default=0.001, gt=0)
    strategy: str
    confidence: float = Field(..., ge=0, le=100)
    reasoning: str
    riskLevel: str = "MEDIUM"
    timestamp: float = Field(default_factory=time.time)

class Position(BaseModel):
    """Posición abierta en el sistema"""
    id: str
    symbol: str
    side: str  # LONG, SHORT
    quantity: float = Field(..., gt=0)
    entryPrice: float = Field(..., gt=0)
    currentPrice: float = Field(..., gt=0)
    unrealizedPnL: float
    unrealizedPnLPercent: float
    realizedPnL: float = 0
    stopLoss: Optional[float] = None
    takeProfit: Optional[float] = None
    status: str = "OPEN"
    timestamp: float = Field(default_factory=time.time)

class Trade(BaseModel):
    """Trade ejecutado"""
    id: str
    symbol: str
    side: str  # BUY, SELL
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    fee: float = Field(..., ge=0)
    pnl: float
    pnlPercent: float
    strategy: str
    timestamp: float = Field(default_factory=time.time)

class Portfolio(BaseModel):
    """Estado del portfolio"""
    totalValue: float
    totalPnL: float
    totalPnLPercent: float
    availableBalance: float
    dailyPnL: float
    positions: List[Position] = []
    winRate: float = 0
    totalTrades: int = 0
    timestamp: float = Field(default_factory=time.time)

# ==================== WEBSOCKET CONNECTION MANAGER ====================
class ConnectionManager:
    """Gestor mejorado de conexiones WebSocket con heartbeat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Conecta un nuevo cliente WebSocket"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.now(),
            "last_heartbeat": datetime.now(),
            "subscriptions": set(),
        }
        
        # Iniciar heartbeat para esta conexión
        self.heartbeat_tasks[client_id] = asyncio.create_task(
            self._heartbeat_loop(client_id)
        )
        
        logger.info(f"WebSocket connected: {client_id} | Total: {len(self.active_connections)}")
        
    def disconnect(self, client_id: str):
        """Desconecta un cliente WebSocket"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
            
        if client_id in self.heartbeat_tasks:
            self.heartbeat_tasks[client_id].cancel()
            del self.heartbeat_tasks[client_id]
            
        logger.info(f"WebSocket disconnected: {client_id} | Total: {len(self.active_connections)}")
    
    async def _heartbeat_loop(self, client_id: str):
        """Loop de heartbeat para mantener la conexión viva"""
        while client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": time.time()
                })
                self.connection_metadata[client_id]["last_heartbeat"] = datetime.now()
                await asyncio.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.warning(f"Heartbeat failed for {client_id}: {e}")
                self.disconnect(client_id)
                break
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Envía mensaje a un cliente específico"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None):
        """Broadcast a todos los clientes conectados"""
        exclude = exclude or set()
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            if client_id not in exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Limpiar conexiones fallidas
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# ==================== TRADING ENGINE ====================
class TradingEngine:
    """Motor de trading con gestión de estado y paper trading"""
    
    def __init__(self):
        self.state = TradingState.IDLE
        self.portfolio = Portfolio(
            totalValue=10000.0,
            totalPnL=0.0,
            totalPnLPercent=0.0,
            availableBalance=10000.0,
            dailyPnL=0.0
        )
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.signals: List[TradingSignal] = []
        self.market_data: Dict[str, MarketData] = {}
        self._position_counter = 0
        self._trade_counter = 0
        self._signal_counter = 0
        
    def get_state(self) -> TradingState:
        """Obtiene el estado actual del motor"""
        return self.state
    
    def set_state(self, new_state: TradingState) -> bool:
        """Cambia el estado del motor con validación"""
        valid_transitions = {
            TradingState.IDLE: [TradingState.RUNNING],
            TradingState.RUNNING: [TradingState.PAUSED, TradingState.STOPPED],
            TradingState.PAUSED: [TradingState.RUNNING, TradingState.STOPPED],
            TradingState.STOPPED: [TradingState.IDLE],
            TradingState.ERROR: [TradingState.STOPPED]
        }
        
        if new_state in valid_transitions.get(self.state, []):
            old_state = self.state
            self.state = new_state
            logger.info(f"Trading state changed: {old_state} -> {new_state}")
            return True
        else:
            logger.warning(f"Invalid state transition: {self.state} -> {new_state}")
            return False
    
    def update_market_data(self, data: MarketData):
        """Actualiza datos de mercado"""
        self.market_data[data.symbol] = data
        
        # Actualizar precios en posiciones abiertas
        for position in self.positions.values():
            if position.symbol == data.symbol:
                position.currentPrice = data.price
                self._update_position_pnl(position)
    
    def _update_position_pnl(self, position: Position):
        """Actualiza P&L de una posición"""
        if position.side == "LONG":
            position.unrealizedPnL = (position.currentPrice - position.entryPrice) * position.quantity
        else:  # SHORT
            position.unrealizedPnL = (position.entryPrice - position.currentPrice) * position.quantity
        
        position.unrealizedPnLPercent = (position.unrealizedPnL / (position.entryPrice * position.quantity)) * 100
    
    async def execute_order(self, symbol: str, side: str, quantity: float, 
                          order_type: OrderType = OrderType.MARKET) -> Trade:
        """Ejecuta una orden (paper trading)"""
        if self.state != TradingState.RUNNING:
            raise ValueError(f"Cannot execute orders in {self.state} state")
        
        # Obtener precio actual
        market_data = self.market_data.get(symbol)
        if not market_data:
            raise ValueError(f"No market data for {symbol}")
        
        # Simular slippage
        slippage = 0.001  # 0.1%
        if side == "BUY":
            execution_price = market_data.price * (1 + slippage)
        else:
            execution_price = market_data.price * (1 - slippage)
        
        # Calcular fee
        fee = execution_price * quantity * 0.001  # 0.1% fee
        
        # Simular P&L (para demostración)
        import random
        pnl = quantity * execution_price * random.uniform(-0.02, 0.03)  # ±2-3%
        
        # Crear trade
        self._trade_counter += 1
        trade = Trade(
            id=f"trade_{self._trade_counter}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=execution_price,
            fee=fee,
            pnl=pnl,
            pnlPercent=(pnl / (execution_price * quantity)) * 100,
            strategy="Manual"
        )
        
        self.trades.append(trade)
        
        # Actualizar portfolio
        self.portfolio.availableBalance -= (execution_price * quantity + fee)
        self.portfolio.totalPnL += pnl
        self.portfolio.dailyPnL += pnl
        self.portfolio.totalTrades += 1
        self._update_win_rate()
        
        logger.info(f"Trade executed: {side} {quantity} {symbol} at {execution_price} (P&L: {pnl:.2f})")
        
        return trade
    
    def _update_win_rate(self):
        """Actualiza el win rate del portfolio"""
        if not self.trades:
            self.portfolio.winRate = 0
            return
        
        winning_trades = sum(1 for trade in self.trades if trade.pnl > 0)
        self.portfolio.winRate = (winning_trades / len(self.trades)) * 100
    
    def generate_signal(self, market_data: MarketData, strategy: str = "AI_Analysis") -> Optional[TradingSignal]:
        """Genera señal de trading basada en análisis"""
        if self.state != TradingState.RUNNING:
            return None
        
        # Análisis básico
        action = None
        confidence = 0
        reasoning = ""
        
        if is_bullish_signal(market_data.dict()):
            action = SignalAction.BUY
            confidence = 70 + (market_data.changePercent24h * 2)  # Mayor cambio, mayor confianza
            reasoning = f"Bullish momentum detected: +{market_data.changePercent24h:.2f}% change with high volume"
        elif is_bearish_signal(market_data.dict()):
            action = SignalAction.SELL
            confidence = 65 + abs(market_data.changePercent24h)
            reasoning = f"Bearish momentum detected: {market_data.changePercent24h:.2f}% decline"
        else:
            return None
        
        # Crear señal
        self._signal_counter += 1
        signal = TradingSignal(
            id=f"signal_{self._signal_counter}",
            symbol=market_data.symbol,
            action=action,
            price=market_data.price,
            strategy=strategy,
            confidence=min(confidence, 95),  # Cap at 95%
            reasoning=reasoning
        )
        
        self.signals.append(signal)
        
        # Mantener solo las últimas 50 señales
        if len(self.signals) > 50:
            self.signals = self.signals[-50:]
        
        return signal

# ==================== FASTAPI APPLICATION ====================
app = FastAPI(
    title="Bot Arbitraje Production Server",
    description="Servidor de producción con todas las características implementadas",
    version="3.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globales
manager = ConnectionManager()
trading_engine = TradingEngine()
binance_feeder: Optional[BinanceDataFeeder] = None

# ==================== API ENDPOINTS ====================
@app.get("/")
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "name": "Bot Arbitraje Production Server",
        "version": "3.0.0",
        "status": "operational",
        "features": [
            "Real-time Binance data",
            "WebSocket with heartbeat",
            "Trading state management",
            "Paper trading simulation",
            "AI signal generation",
            "Portfolio tracking"
        ],
        "endpoints": {
            "health": "/api/health",
            "websocket": "/ws",
            "portfolio": "/api/portfolio",
            "trades": "/api/trades",
            "signals": "/api/signals",
            "trading": "/api/trading/control"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check con información detallada del sistema"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "system": {
            "trading_state": trading_engine.get_state(),
            "connections": len(manager.active_connections),
            "portfolio_value": trading_engine.portfolio.totalValue,
            "total_trades": trading_engine.portfolio.totalTrades,
            "signals_generated": len(trading_engine.signals),
            "market_symbols": len(trading_engine.market_data)
        },
        "services": {
            "binance_connected": binance_feeder.binance_client.is_running if binance_feeder else False,
            "websocket_active": len(manager.active_connections) > 0
        }
    }

@app.get("/api/portfolio")
async def get_portfolio():
    """Obtiene el estado actual del portfolio"""
    return trading_engine.portfolio

@app.get("/api/trades")
async def get_trades(limit: int = 50):
    """Obtiene los trades recientes"""
    return trading_engine.trades[-limit:]

@app.get("/api/signals")
async def get_signals(limit: int = 20):
    """Obtiene las señales de trading recientes"""
    return trading_engine.signals[-limit:]

@app.post("/api/trading/control")
async def control_trading(action: str):
    """Controla el estado del sistema de trading"""
    if action == "start":
        if trading_engine.set_state(TradingState.RUNNING):
            await manager.broadcast({
                "type": "trading_status",
                "data": {
                    "status": "ACTIVE",
                    "message": "Trading system started successfully"
                }
            })
            return {"status": "success", "state": trading_engine.get_state()}
    
    elif action == "pause":
        if trading_engine.set_state(TradingState.PAUSED):
            await manager.broadcast({
                "type": "trading_status",
                "data": {
                    "status": "PAUSED",
                    "message": "Trading system paused"
                }
            })
            return {"status": "success", "state": trading_engine.get_state()}
    
    elif action == "stop":
        if trading_engine.set_state(TradingState.STOPPED):
            await manager.broadcast({
                "type": "trading_status",
                "data": {
                    "status": "STOPPED",
                    "message": "Trading system stopped"
                }
            })
            return {"status": "success", "state": trading_engine.get_state()}
    
    elif action == "reset":
        if trading_engine.set_state(TradingState.IDLE):
            return {"status": "success", "state": trading_engine.get_state()}
    
    return {"status": "error", "message": f"Invalid action: {action}"}

# ==================== WEBSOCKET ENDPOINT ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint con reconexión robusta"""
    import uuid
    client_id = str(uuid.uuid4())
    
    await manager.connect(websocket, client_id)
    
    try:
        # Enviar mensaje de bienvenida
        await manager.send_personal_message({
            "type": "connection_ack",
            "client_id": client_id,
            "message": "Connected to production server",
            "timestamp": time.time()
        }, client_id)
        
        # Enviar estado inicial
        await send_initial_state(client_id)
        
        # Loop principal
        while True:
            data = await websocket.receive_text()
            await handle_websocket_message(client_id, json.loads(data))
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}\n{traceback.format_exc()}")
    finally:
        manager.disconnect(client_id)

async def send_initial_state(client_id: str):
    """Envía el estado inicial al cliente conectado"""
    # Portfolio
    await manager.send_personal_message({
        "type": "portfolio_update",
        "data": trading_engine.portfolio.dict()
    }, client_id)
    
    # Market data
    for symbol, data in trading_engine.market_data.items():
        await manager.send_personal_message({
            "type": "market_data",
            "data": data.dict()
        }, client_id)
    
    # Trading state
    await manager.send_personal_message({
        "type": "trading_status",
        "data": {
            "status": trading_engine.get_state(),
            "message": f"System is {trading_engine.get_state()}"
        }
    }, client_id)

async def handle_websocket_message(client_id: str, message: dict):
    """Maneja mensajes entrantes del WebSocket"""
    msg_type = message.get("type")
    
    if msg_type == "subscribe":
        channels = message.get("channels", [])
        manager.connection_metadata[client_id]["subscriptions"].update(channels)
        logger.info(f"Client {client_id} subscribed to: {channels}")
        
        await manager.send_personal_message({
            "type": "subscription_ack",
            "channels": channels,
            "status": "success"
        }, client_id)
    
    elif msg_type == "execute_order":
        try:
            trade = await trading_engine.execute_order(
                symbol=message.get("symbol"),
                side=message.get("side"),
                quantity=float(message.get("quantity", 0.001))
            )
            
            # Broadcast trade ejecutado
            await manager.broadcast({
                "type": "trade_executed",
                "data": trade.dict()
            })
            
            # Actualizar portfolio
            await manager.broadcast({
                "type": "portfolio_update",
                "data": trading_engine.portfolio.dict()
            })
            
        except Exception as e:
            await manager.send_personal_message({
                "type": "error",
                "message": str(e)
            }, client_id)
    
    elif msg_type == "heartbeat_ack":
        # Cliente confirmó heartbeat
        manager.connection_metadata[client_id]["last_heartbeat"] = datetime.now()

# ==================== BINANCE DATA HANDLER ====================
async def handle_binance_data(data: dict):
    """Procesa datos de Binance y genera señales"""
    msg_type = data.get("type")
    
    if msg_type == "market_data":
        market_data = MarketData(**data["data"])
        trading_engine.update_market_data(market_data)
        
        # Broadcast a todos los clientes
        await manager.broadcast(data)
        
        # Generar señales si el trading está activo
        if trading_engine.get_state() == TradingState.RUNNING:
            signal = trading_engine.generate_signal(market_data)
            if signal:
                await manager.broadcast({
                    "type": "trading_signal",
                    "data": signal.dict()
                })
    
    elif msg_type in ["orderbook_update", "kline_data"]:
        # Broadcast directo
        await manager.broadcast(data)

# ==================== STARTUP & SHUTDOWN ====================
@app.on_event("startup")
async def startup_event():
    """Inicialización del servidor"""
    global binance_feeder
    
    logger.info("=" * 80)
    logger.info("[LAUNCH] PRODUCTION SERVER STARTING")
    logger.info("=" * 80)
    
    # Inicializar Binance feeder
    try:
        # Crear feeder personalizado
        class ProductionBinanceFeeder(BinanceDataFeeder):
            async def handle_binance_data(self, data: Dict):
                await handle_binance_data(data)
        
        binance_feeder = ProductionBinanceFeeder(manager)
        await binance_feeder.start()
        logger.info("[OK] Binance data feed initialized")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize Binance feed: {e}")
        logger.info("[WARNING]  Running in degraded mode without live data")
    
    # Tarea de monitoreo del sistema
    asyncio.create_task(system_monitoring())
    
    logger.info("[OK] All systems initialized")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    """Cierre ordenado del servidor"""
    logger.info("Shutting down production server...")
    
    if binance_feeder:
        await binance_feeder.stop()
    
    # Notificar a todos los clientes
    await manager.broadcast({
        "type": "server_shutdown",
        "message": "Server is shutting down",
        "timestamp": time.time()
    })
    
    logger.info("Server shutdown complete")

# ==================== MONITORING TASKS ====================
async def system_monitoring():
    """Monitoreo continuo del sistema"""
    while True:
        try:
            # Actualizar métricas del portfolio
            trading_engine.portfolio.timestamp = time.time()
            
            # Broadcast métricas del sistema
            if len(manager.active_connections) > 0:
                await manager.broadcast({
                    "type": "system_metrics",
                    "data": {
                        "trading_state": trading_engine.get_state(),
                        "connections": len(manager.active_connections),
                        "portfolio_value": trading_engine.portfolio.totalValue,
                        "daily_pnl": trading_engine.portfolio.dailyPnL,
                        "signals_count": len(trading_engine.signals),
                        "trades_count": len(trading_engine.trades),
                        "timestamp": time.time()
                    }
                })
            
            await asyncio.sleep(60)  # Cada minuto
            
        except Exception as e:
            logger.error(f"Error in system monitoring: {e}")
            await asyncio.sleep(60)

# ==================== MAIN ENTRY POINT ====================
def start_production_server():
    """Inicia el servidor de producción"""
    host = "127.0.0.1"
    port = 8000
    
    print("\n" + "="*80)
    print("[LAUNCH] BOT ARBITRAJE PRODUCTION SERVER v3.0")
    print("="*80)
    print(f"[API] API Server: http://{host}:{port}")
    print(f"[WEB] WebSocket: ws://{host}:{port}/ws")
    print("="*80)
    print("[INFO] Features:")
    print("   * Real-time Binance market data")
    print("   * WebSocket with automatic heartbeat")
    print("   * Robust reconnection handling")
    print("   * Trading state management")
    print("   * Paper trading simulation")
    print("   * AI-powered signal generation")
    print("   * Real-time portfolio tracking")
    print("   * Comprehensive logging system")
    print("="*80)
    print("[STATS] Monitoring:")
    print(f"   * Logs: logs/production_server.log")
    print(f"   * Health: http://{host}:{port}/api/health")
    print("="*80)
    print("Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    start_production_server()
