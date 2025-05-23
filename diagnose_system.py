"""
Script de diagnóstico del sistema Bot Arbitraje
Verifica el estado de los servicios y conexiones
"""

import asyncio
import json
import aiohttp
import websockets
import time
from datetime import datetime

# Colores para la consola
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

async def check_backend_api():
    """Verifica el API del backend"""
    print_info("Verificando API del backend...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check root endpoint
            async with session.get('http://localhost:8001/') as response:
                if response.status == 200:
                    data = await response.json()
                    print_success(f"API Backend operativo - Version: {data.get('version')}")
                else:
                    print_error(f"API Backend respondió con código: {response.status}")
                    return False
            
            # Check health endpoint
            async with session.get('http://localhost:8001/api/health') as response:
                if response.status == 200:
                    health = await response.json()
                    print_success(f"Health check OK - Estado: {health.get('status')}")
                    print_info(f"  - Estado de trading: {health['system']['trading_state']}")
                    print_info(f"  - Conexiones WebSocket: {health['system']['connections']}")
                    print_info(f"  - Trades totales: {health['system']['total_trades']}")
                    print_info(f"  - Símbolos de mercado: {health['system']['market_symbols']}")
                    return True
                else:
                    print_error("Health check falló")
                    return False
                    
    except aiohttp.ClientConnectionError:
        print_error("No se puede conectar al backend en http://localhost:8001")
        print_warning("Asegúrate de que el servidor esté ejecutándose")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False

async def check_websocket_connection():
    """Verifica la conexión WebSocket"""
    print_info("\nVerificando conexión WebSocket...")
    
    try:
        uri = "ws://localhost:8001/ws"
        async with websockets.connect(uri) as websocket:
            print_success("Conexión WebSocket establecida")
            
            # Esperar mensaje de bienvenida
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome)
            print_success(f"Mensaje de bienvenida recibido: {welcome_data.get('type')}")
            
            # Suscribirse a canales
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["market_data"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            print_success("Suscripción enviada")
            
            # Esperar algunos mensajes
            print_info("Esperando mensajes de datos...")
            messages_received = 0
            start_time = time.time()
            
            while time.time() - start_time < 10:  # Escuchar por 10 segundos
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "heartbeat":
                        # Responder al heartbeat
                        await websocket.send(json.dumps({
                            "type": "heartbeat_ack",
                            "timestamp": time.time()
                        }))
                        print_info("💓 Heartbeat recibido y respondido")
                    elif msg_type == "market_data":
                        symbol = data["data"]["symbol"]
                        price = data["data"]["price"]
                        print_success(f"📊 Datos de mercado: {symbol} = ${price:,.2f}")
                        messages_received += 1
                    else:
                        print_info(f"Mensaje recibido: {msg_type}")
                        
                except asyncio.TimeoutError:
                    continue
            
            if messages_received > 0:
                print_success(f"✨ Recibidos {messages_received} mensajes de datos de mercado")
                return True
            else:
                print_warning("No se recibieron datos de mercado")
                return False
                
    except websockets.exceptions.InvalidURI:
        print_error("URI de WebSocket inválida")
        return False
    except ConnectionRefusedError:
        print_error("Conexión WebSocket rechazada")
        print_warning("Verifica que el servidor esté ejecutándose en ws://localhost:8001/ws")
        return False
    except Exception as e:
        print_error(f"Error en WebSocket: {type(e).__name__}: {e}")
        return False

async def check_binance_connection():
    """Verifica la conexión directa a Binance"""
    print_info("\nVerificando conexión a Binance...")
    
    try:
        # Test REST API
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.binance.com/api/v3/ping') as response:
                if response.status == 200:
                    print_success("API REST de Binance accesible")
                else:
                    print_error(f"API REST de Binance respondió con: {response.status}")
                    return False
        
        # Test WebSocket
        uri = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
        async with websockets.connect(uri) as websocket:
            print_success("WebSocket de Binance conectado")
            
            # Recibir un mensaje
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            if 's' in data and 'c' in data:
                print_success(f"Datos de Binance: {data['s']} = ${float(data['c']):,.2f}")
                return True
                
    except Exception as e:
        print_error(f"Error conectando a Binance: {e}")
        return False

async def check_frontend():
    """Verifica si el frontend está respondiendo"""
    print_info("\nVerificando frontend...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:5173/') as response:
                if response.status == 200:
                    print_success("Frontend respondiendo en http://localhost:5173")
                    return True
                else:
                    print_warning(f"Frontend respondió con código: {response.status}")
                    return False
    except:
        print_warning("Frontend no está respondiendo")
        print_info("Ejecuta 'npm run dev' en el directorio frontend")
        return False

async def main():
    """Ejecuta todas las verificaciones"""
    print_header("DIAGNÓSTICO DEL SISTEMA BOT ARBITRAJE")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "backend_api": False,
        "websocket": False,
        "binance": False,
        "frontend": False
    }
    
    # Verificar componentes
    results["backend_api"] = await check_backend_api()
    
    if results["backend_api"]:
        results["websocket"] = await check_websocket_connection()
    
    results["binance"] = await check_binance_connection()
    results["frontend"] = await check_frontend()
    
    # Resumen
    print_header("RESUMEN DEL DIAGNÓSTICO")
    
    all_ok = all(results.values())
    
    for component, status in results.items():
        if status:
            print_success(f"{component.replace('_', ' ').title()}: OPERATIVO")
        else:
            print_error(f"{component.replace('_', ' ').title()}: FALLA")
    
    print("")
    if all_ok:
        print_success("🎉 Todos los sistemas están operativos!")
    else:
        print_warning("Algunos componentes necesitan atención")
        
        if not results["backend_api"]:
            print_info("\nPara iniciar el backend:")
            print_info("  cd C:\\Users\\zamor\\Bot_Arbitraje2105")
            print_info("  python src\\production_server.py")
        
        if not results["frontend"]:
            print_info("\nPara iniciar el frontend:")
            print_info("  cd C:\\Users\\zamor\\Bot_Arbitraje2105\\frontend")
            print_info("  npm run dev")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDiagnóstico interrumpido por el usuario")
