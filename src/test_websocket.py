"""
Script de prueba para verificar la conexión WebSocket
Diagnostica problemas de conexión entre frontend y backend
"""

import asyncio
import json
import logging
import time
import websockets

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WebSocketTest")

async def test_websocket_connection():
    """Prueba la conexión WebSocket al servidor"""
    uri = "ws://localhost:8001/ws"
    
    try:
        logger.info(f"Conectando a {uri}...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Conexión establecida exitosamente")
            
            # Escuchar mensaje de bienvenida
            welcome = await websocket.recv()
            logger.info(f"Mensaje de bienvenida: {welcome}")
            
            # Suscribirse a canales
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["market_data", "trading_signals", "portfolio_updates"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            logger.info("📤 Enviado mensaje de suscripción")
            
            # Responder a heartbeats y recibir datos
            message_count = 0
            start_time = time.time()
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get("type")
                    
                    if msg_type == "heartbeat":
                        # Responder al heartbeat
                        await websocket.send(json.dumps({
                            "type": "heartbeat_ack",
                            "timestamp": time.time()
                        }))
                        logger.info("💓 Heartbeat recibido y respondido")
                    
                    elif msg_type == "market_data":
                        symbol = data["data"]["symbol"]
                        price = data["data"]["price"]
                        logger.info(f"📊 Market Data: {symbol} = ${price:,.2f}")
                    
                    elif msg_type == "connection_ack":
                        logger.info(f"✅ Connection ACK: {data.get('message')}")
                    
                    else:
                        logger.info(f"📨 Mensaje tipo '{msg_type}' recibido")
                    
                    # Estadísticas cada 30 segundos
                    if time.time() - start_time > 30:
                        logger.info(f"📈 Estadísticas: {message_count} mensajes en {int(time.time() - start_time)} segundos")
                        start_time = time.time()
                        message_count = 0
                        
                except asyncio.TimeoutError:
                    logger.warning("⏱️ Timeout esperando mensaje (60s)")
                    
    except websockets.exceptions.InvalidURI:
        logger.error("❌ URI inválida")
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"❌ Error de WebSocket: {e}")
    except ConnectionRefusedError:
        logger.error("❌ Conexión rechazada - ¿Está el servidor ejecutándose en http://localhost:8001?")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {type(e).__name__}: {e}")

async def test_binance_connection():
    """Prueba directa de conexión a Binance"""
    uri = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
    
    try:
        logger.info("Probando conexión directa a Binance...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Conectado a Binance WebSocket")
            
            # Recibir algunos mensajes
            for i in range(5):
                message = await websocket.recv()
                data = json.loads(message)
                
                if 's' in data and 'c' in data:
                    logger.info(f"🔄 Binance: {data['s']} = ${float(data['c']):,.2f}")
                
    except Exception as e:
        logger.error(f"❌ Error conectando a Binance: {e}")

async def main():
    """Ejecuta las pruebas"""
    logger.info("=== INICIANDO PRUEBAS DE WEBSOCKET ===")
    
    # Primero probar conexión directa a Binance
    logger.info("\n1. Probando conexión a Binance...")
    await test_binance_connection()
    
    # Luego probar conexión al servidor local
    logger.info("\n2. Probando conexión al servidor local...")
    await test_websocket_connection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Prueba interrumpida por el usuario")
