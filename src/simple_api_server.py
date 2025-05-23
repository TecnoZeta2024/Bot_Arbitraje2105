"""
API Server Simplificado para Bot_Arbitraje2105
Versión funcional para arrancar HOY - Frontend-First Visibility
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimpleAPIServer")

# Inicializar FastAPI
app = FastAPI(
    title="Bot de Arbitraje Triangular API - Simplified",
    description="API simplificada para desarrollo rápido",
    version="1.0.0"
)

# Modelos básicos
class MarketData(BaseModel):
    symbol: str
    price: float
    volume24h: float
    changePercent24h: float
    timestamp: float

class TradingSignal(BaseModel):
    id: str
    symbol: str
    action: str  # BUY, SELL
    price: float
    strategy: str
    confidence: float
    timestamp: float

class Position(BaseModel):
    id: str
    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entryPrice: float
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

# Datos simulados para demostración
MOCK_MARKET_DATA = {
    "BTCUSDT": {"price": 97000.0, "volume24h": 1500000000, "changePercent24h": 2.5},
    "ETHUSDT": {"price": 3200.0, "volume24h": 800000000, "changePercent24h": 3.2},
    "ADAUSDT": {"price": 0.85, "volume24h": 200000000, "changePercent24h": -1.1},
    "DOTUSDT": {"price": 7.2, "volume24h": 150000000, "changePercent24h": 1.8},
    "LINKUSDT": {"price": 25.5, "volume24h": 120000000, "changePercent24h": 4.1},
    "BNBUSDT": {"price": 650.0, "volume24h": 300000000, "changePercent24h": 1.5},
    "XRPUSDT": {"price": 1.95, "volume24h": 400000000, "changePercent24h": -0.8},
    "LTCUSDT": {"price": 120.0, "volume24h": 180000000, "changePercent24h": 2.1},
    "SOLUSDT": {"price": 140.0, "volume24h": 250000000, "changePercent24h": 5.2},
    "AVAXUSDT": {"price": 42.0, "volume24h": 100000000, "changePercent24h": 3.8}
}

# Variables globales para estado
trading_active = False
portfolio_value = 1000.0
daily_pnl = 0.0

@app.get("/")
async def root():
    return {"mensaje": "API del Bot de Arbitraje Triangular - Simplificada", "status": "OK"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "OK", 
        "version": "1.0.0-simplified",
        "timestamp": time.time(),
        "trading_active": trading_active,
        "connections": len(manager.active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    try:
        # Enviar datos iniciales al conectarse
        await websocket.send_json({
            "type": "connection_ack",
            "message": "Connected to trading server",
            "timestamp": time.time()
        })
        
        # Enviar datos de mercado iniciales
        for symbol, data in MOCK_MARKET_DATA.items():
            await websocket.send_json({
                "type": "market_data",
                "data": {
                    "symbol": symbol,
                    "price": data["price"],
                    "volume24h": data["volume24h"],
                    "changePercent24h": data["changePercent24h"],
                    "timestamp": time.time()
                }
            })
        
        # Enviar portfolio inicial
        await websocket.send_json({
            "type": "portfolio_update",
            "data": {
                "totalValue": portfolio_value,
                "dailyPnL": daily_pnl,
                "totalPnL": 0.0,
                "totalPnLPercent": 0.0,
                "availableBalance": portfolio_value,
                "positions": []
            }
        })
        
        while True:
            # Escuchar mensajes del cliente
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
    global trading_active, portfolio_value, daily_pnl
    
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
            trading_active = True
            await manager.broadcast_json({
                "type": "trading_status",
                "status": "ACTIVE",
                "message": "Trading started",
                "timestamp": time.time()
            })
        elif action in ["pause", "stop"]:
            trading_active = False
            await manager.broadcast_json({
                "type": "trading_status", 
                "status": "INACTIVE",
                "message": f"Trading {action}ed",
                "timestamp": time.time()
            })
            
    elif msg_type == "execute_order":
        # Simular ejecución de orden
        symbol = message_data.get("symbol", "BTCUSDT")
        side = message_data.get("side", "BUY")
        quantity = message_data.get("quantity", 0.001)
        price = message_data.get("price", MOCK_MARKET_DATA.get(symbol, {}).get("price", 50000))
        
        # Simular trade ejecutado
        trade_id = f"trade_{int(time.time())}"
        simulated_pnl = (quantity * price * 0.001)  # 0.1% ganancia simulada
        
        await manager.broadcast_json({
            "type": "trade_executed",
            "data": {
                "id": trade_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "pnl": simulated_pnl,
                "strategy": "Manual",
                "timestamp": time.time()
            }
        })
        
        # Actualizar portfolio
        daily_pnl += simulated_pnl
        portfolio_value += simulated_pnl
        
        await manager.broadcast_json({
            "type": "portfolio_update",
            "data": {
                "totalValue": portfolio_value,
                "dailyPnL": daily_pnl,
                "totalPnL": daily_pnl,
                "totalPnLPercent": (daily_pnl / 1000.0) * 100,
                "availableBalance": portfolio_value
            }
        })

# Tarea en background para simular datos en tiempo real
async def simulate_market_data():
    """Simula datos de mercado en tiempo real"""
    import random
    
    while True:
        if len(manager.active_connections) > 0:
            # Actualizar precios con cambios pequeños
            for symbol in MOCK_MARKET_DATA:
                change = random.uniform(-0.01, 0.01)  # ±1% cambio
                MOCK_MARKET_DATA[symbol]["price"] *= (1 + change)
                MOCK_MARKET_DATA[symbol]["changePercent24h"] += change * 100
                
                await manager.broadcast_json({
                    "type": "market_data",
                    "data": {
                        "symbol": symbol,
                        "price": round(MOCK_MARKET_DATA[symbol]["price"], 6),
                        "volume24h": MOCK_MARKET_DATA[symbol]["volume24h"],
                        "changePercent24h": round(MOCK_MARKET_DATA[symbol]["changePercent24h"], 2),
                        "timestamp": time.time()
                    }
                })
        
        await asyncio.sleep(2)  # Actualizar cada 2 segundos

# Tarea para simular señales de trading
async def simulate_trading_signals():
    """Simula señales de trading automáticas"""
    import random
    
    while True:
        if trading_active and len(manager.active_connections) > 0:
            symbol = random.choice(list(MOCK_MARKET_DATA.keys()))
            action = random.choice(["BUY", "SELL"])
            confidence = random.uniform(0.6, 0.95)
            
            signal_id = f"signal_{int(time.time())}"
            await manager.broadcast_json({
                "type": "trading_signal",
                "data": {
                    "id": signal_id,
                    "symbol": symbol,
                    "action": action,
                    "price": MOCK_MARKET_DATA[symbol]["price"],
                    "strategy": random.choice(["Scalping", "DayTrading"]),
                    "confidence": round(confidence * 100, 1),
                    "timestamp": time.time()
                }
            })
        
        await asyncio.sleep(random.uniform(10, 30))  # Señales cada 10-30 segundos

@app.on_event("startup")
async def startup_event():
    """Iniciar tareas en background al arrancar"""
    asyncio.create_task(simulate_market_data())
    asyncio.create_task(simulate_trading_signals())
    logger.info("Background tasks started")

def start_server():
    """Inicia el servidor API"""
    host = "127.0.0.1"
    port = 8000
    
    logger.info(f"🚀 Starting Simplified API Server on {host}:{port}")
    logger.info("📊 Features: WebSocket, Market Data, Trading Controls")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
