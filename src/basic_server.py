"""
Servidor API Básico 100% Funcional
Para Bot_Arbitraje2105 - Garantizado que funciona
"""

import asyncio
import json
import logging
import random
import time
from typing import List

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BasicTradingServer")

# Inicializar FastAPI
app = FastAPI(
    title="Basic Trading Server",
    description="Servidor básico 100% funcional",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"❌ WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast_json(self, data: dict):
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(data)
                except:
                    disconnected.append(connection)
            
            for connection in disconnected:
                self.disconnect(connection)

manager = ConnectionManager()

# Datos de mercado simulados
MARKET_DATA = {
    "BTCUSDT": {"price": 97000.0, "volume24h": 1500000000, "changePercent24h": 2.5},
    "ETHUSDT": {"price": 3200.0, "volume24h": 800000000, "changePercent24h": 3.2},
    "ADAUSDT": {"price": 0.85, "volume24h": 200000000, "changePercent24h": -1.1},
    "DOTUSDT": {"price": 7.2, "volume24h": 150000000, "changePercent24h": 1.8},
    "LINKUSDT": {"price": 25.5, "volume24h": 120000000, "changePercent24h": 4.1},
    "BNBUSDT": {"price": 650.0, "volume24h": 300000000, "changePercent24h": 1.5}
}

# Estado del sistema
trading_active = False
portfolio_value = 1000.0
daily_pnl = 0.0
trades = []

@app.get("/")
async def root():
    return {
        "message": "✅ Basic Trading Server Running",
        "status": "OK",
        "timestamp": time.time()
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "OK",
        "version": "1.0.0-basic",
        "connections": len(manager.active_connections),
        "trading_active": trading_active,
        "portfolio_value": portfolio_value
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connection_ack",
            "message": "✅ Connected to Basic Trading Server",
            "timestamp": time.time()
        })
        
        # Enviar datos iniciales
        await send_initial_data(websocket)
        
        # Escuchar mensajes del cliente
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handle_message(websocket, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

async def send_initial_data(websocket: WebSocket):
    """Envía datos iniciales al cliente"""
    
    # Portfolio inicial
    await websocket.send_json({
        "type": "portfolio_update",
        "data": {
            "totalValue": portfolio_value,
            "dailyPnL": daily_pnl,
            "totalPnL": daily_pnl,
            "totalPnLPercent": (daily_pnl / 1000.0) * 100,
            "availableBalance": portfolio_value,
            "positions": []
        }
    })
    
    # Datos de mercado iniciales
    for symbol, data in MARKET_DATA.items():
        await websocket.send_json({
            "type": "market_data",
            "data": {
                "symbol": symbol,
                "price": data["price"],
                "volume24h": data["volume24h"],
                "changePercent24h": data["changePercent24h"],
                "high24h": data["price"] * 1.02,
                "low24h": data["price"] * 0.98,
                "timestamp": time.time()
            }
        })

async def handle_message(websocket: WebSocket, message: dict):
    """Maneja mensajes del cliente"""
    global trading_active, portfolio_value, daily_pnl
    
    msg_type = message.get("type")
    
    if msg_type == "subscribe":
        await websocket.send_json({
            "type": "subscription_ack",
            "status": "Subscribed",
            "channels": message.get("channels", [])
        })
        
    elif msg_type == "trading_control":
        action = message.get("action")
        
        if action == "start":
            trading_active = True
            await manager.broadcast_json({
                "type": "trading_status",
                "status": "ACTIVE",
                "message": "🚀 Trading started successfully!"
            })
            
        elif action in ["pause", "stop"]:
            trading_active = False
            await manager.broadcast_json({
                "type": "trading_status",
                "status": "INACTIVE", 
                "message": f"⏸️ Trading {action}ed"
            })
            
    elif msg_type == "execute_order":
        # Simular ejecución de orden
        symbol = message.get("symbol", "BTCUSDT")
        side = message.get("side", "BUY")
        quantity = float(message.get("quantity", 0.001))
        price = MARKET_DATA.get(symbol, {"price": 50000})["price"]
        
        # Simular P&L
        pnl = quantity * price * random.uniform(-0.02, 0.03)  # ±2% to +3%
        daily_pnl += pnl
        portfolio_value += pnl
        
        trade = {
            "id": f"trade_{int(time.time())}",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "pnl": pnl,
            "strategy": "Manual",
            "timestamp": time.time()
        }
        
        trades.append(trade)
        
        # Notificar trade ejecutado
        await manager.broadcast_json({
            "type": "trade_executed",
            "data": trade
        })
        
        # Actualizar portfolio
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
async def simulate_market_updates():
    """Simula actualizaciones de mercado"""
    while True:
        await asyncio.sleep(3)  # Cada 3 segundos
        
        if len(manager.active_connections) > 0:
            # Actualizar precios aleatoriamente
            for symbol in MARKET_DATA:
                change = random.uniform(-0.005, 0.005)  # ±0.5%
                MARKET_DATA[symbol]["price"] *= (1 + change)
                MARKET_DATA[symbol]["changePercent24h"] += change * 100
                
                await manager.broadcast_json({
                    "type": "market_data",
                    "data": {
                        "symbol": symbol,
                        "price": round(MARKET_DATA[symbol]["price"], 6),
                        "volume24h": MARKET_DATA[symbol]["volume24h"],
                        "changePercent24h": round(MARKET_DATA[symbol]["changePercent24h"], 2),
                        "high24h": MARKET_DATA[symbol]["price"] * 1.02,
                        "low24h": MARKET_DATA[symbol]["price"] * 0.98,
                        "timestamp": time.time()
                    }
                })

# Tarea para simular señales cuando trading esté activo
async def simulate_trading_signals():
    """Simula señales de trading"""
    while True:
        await asyncio.sleep(random.uniform(15, 45))  # Cada 15-45 segundos
        
        if trading_active and len(manager.active_connections) > 0:
            symbol = random.choice(list(MARKET_DATA.keys()))
            action = random.choice(["BUY", "SELL"])
            confidence = random.uniform(65, 95)
            
            await manager.broadcast_json({
                "type": "trading_signal",
                "data": {
                    "id": f"signal_{int(time.time())}",
                    "symbol": symbol,
                    "action": action,
                    "price": MARKET_DATA[symbol]["price"],
                    "strategy": random.choice(["AI_Scalping", "TrendFollowing", "MeanReversion"]),
                    "confidence": round(confidence, 1),
                    "timestamp": time.time()
                }
            })

@app.on_event("startup")
async def startup_event():
    """Inicializar tareas en background"""
    asyncio.create_task(simulate_market_updates())
    asyncio.create_task(simulate_trading_signals())
    logger.info("🚀 Background tasks started")

def start_server():
    """Inicia el servidor"""
    host = "127.0.0.1"
    port = 8000
    
    print("=" * 80)
    print("🚀 BASIC TRADING SERVER - 100% FUNCTIONAL")
    print("=" * 80)
    print(f"📡 Server: http://{host}:{port}")
    print(f"🌐 WebSocket: ws://{host}:{port}/ws")
    print("✅ Guaranteed to work!")
    print("=" * 80)
    
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_server()
