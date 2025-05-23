"""
Servidor API para el Bot de Arbitraje Triangular.
Proporciona endpoints para recibir solicitudes de ejecución de arbitraje.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.apis.gemini_client import gemini_client  # Import Gemini client
from src.apis.supabase_client import supabase_client
from src.core.ejecutar_ciclo import ejecutar_arbitraje
from src.utils.config import settings
from src.utils.logger import api_logger, get_logger
from src.utils.prompt_formatter import PromptFormatter  # Import PromptFormatter

# Inicializar FastAPI
app = FastAPI(
    title="Bot de Arbitraje Triangular API",
    description="API para recibir y procesar solicitudes de ejecución de arbitraje",
    version="1.0.0"
)

# Modelos de datos
class ConfirmacionUsuario(BaseModel):
    timestamp: str
    decision: str

class SolicitudEjecucion(BaseModel):
    operacion_id: str
    oportunidad: Dict[str, Any]
    analisis_ia: Dict[str, Any]
    confirmacion_usuario: ConfirmacionUsuario

class ResultadoEjecucion(BaseModel):
    operacion_id: str
    estado: str
    resultado: str
    pares_ejecutados: list
    comisiones: float
    slippage: float
    ganancia_neta: float
    rentabilidad_real: float
    tiempo_ejecucion: float

class OpportunityData(BaseModel):
    """Modelo para los datos de oportunidad recibidos."""
    ruta: list[str]
    capital: float
    # Allow other fields as needed
    model_config = {'extra': 'allow'}

class GeminiAnalysisResult(BaseModel):
    """Modelo para el resultado del análisis de Gemini."""
    success: bool
    text: Optional[str] = None
    blocked: bool = False
    safety_ratings: list = []
    finish_reason: Optional[str] = None
    prompt_feedback: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Registro de ejecuciones en progreso
ejecuciones_activas: Dict[str, str] = {}

@app.get("/")
async def root():
    """Endpoint raíz para verificar que el servidor está activo."""
    return {"mensaje": "API del Bot de Arbitraje Triangular activa"}

@app.get("/api/health")
async def health_check():
    """Endpoint para verificar el estado del servidor."""
    return {
        "status": "OK",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.post("/api/opportunity")
async def receive_opportunity(opportunity_data: OpportunityData):
    """
    Endpoint para recibir datos de oportunidad de arbitraje.
    """
    api_logger.info(f"Received new opportunity data: {opportunity_data.model_dump_json()}")

    gemini_analysis_result: Optional[GeminiAnalysisResult] = None
    try:
        # Format prompt for Gemini
        prompt_formatter = PromptFormatter()
        gemini_prompt = prompt_formatter.format_opportunity_analysis_prompt(opportunity_data.model_dump())
        
        # Call Gemini API
        gemini_response = await gemini_client.generate_content(gemini_prompt)
        
        if gemini_response["success"]:
            gemini_analysis_result = GeminiAnalysisResult(
                success=True,
                text=gemini_response["text"],
                blocked=gemini_response["parsed_response"].get("blocked", False),
                safety_ratings=gemini_response["parsed_response"].get("safety_ratings", []),
                finish_reason=gemini_response["parsed_response"].get("finish_reason"),
                prompt_feedback=gemini_response["parsed_response"].get("prompt_feedback")
            )
            api_logger.info("Gemini analysis successful.")
        else:
            gemini_analysis_result = GeminiAnalysisResult(
                success=False,
                error=gemini_response.get("error", "Unknown error during Gemini analysis")
            )
            api_logger.error(f"Gemini analysis failed: {gemini_analysis_result.error}")
            # Depending on criticality, you might raise an HTTPException here
            # raise HTTPException(status_code=500, detail=f"Gemini analysis failed: {gemini_analysis_result.error}")

    except Exception as e:
        api_logger.error(f"Error during Gemini analysis integration: {str(e)}", exc_info=e)
        gemini_analysis_result = GeminiAnalysisResult(
            success=False,
            error=f"Exception during Gemini analysis: {str(e)}"
        )
        # raise HTTPException(status_code=500, detail=f"Exception during Gemini analysis: {str(e)}")

    # TODO: Integrate Telegram notification here
    # This might involve sending a message to a Telegram handler with opportunity_data and analysis results

    # TODO: Wait for user confirmation here
    # This might involve a mechanism to pause and resume the process based on user input,
    # potentially using a webhook from n8n or another service that handles user interaction.

    # También, el resultado de esta función podría necesitar ser enviado al WebSocket manager
    # para notificar al frontend sobre la nueva oportunidad y el análisis de IA.
    # Ejemplo: await manager.broadcast_json({"type": "new_opportunity_analyzed", "data": opportunity_data.model_dump(), "analysis": gemini_analysis_result.model_dump()})

    return {
        "status": "Opportunity received and Gemini analysis initiated",
        "data": opportunity_data.model_dump(),
        "gemini_analysis": gemini_analysis_result.model_dump() if gemini_analysis_result else None
    }


async def execute_arbitrage_task(solicitud: SolicitudEjecucion):
    """
    Tarea en segundo plano para ejecutar el arbitraje.
    
    Args:
        solicitud: Datos de la solicitud de ejecución.
    """
    operacion_id = solicitud.operacion_id
    resultado_final: Dict[str, Any] = {}
    
    try:
        # Actualizar estado en registro de ejecuciones activas
        ejecuciones_activas[operacion_id] = "EJECUTANDO"
        await manager.broadcast_json({"type": "operation_status_update", "operacion_id": operacion_id, "estado": "EJECUTANDO"})
        
        # Ejecutar el arbitraje (asumiendo que ejecutar_arbitraje es async)
        api_logger.info(f"Iniciando ejecución de arbitraje para operación: {operacion_id}")
        # Asumimos que ejecutar_arbitraje es una función async y devuelve un diccionario
        resultado_ejecucion_dict = await ejecutar_arbitraje(
            operacion_id=operacion_id,
            oportunidad=solicitud.oportunidad,
            analisis_ia=solicitud.analisis_ia
        )
        resultado_final = resultado_ejecucion_dict # Guardamos el resultado para el bloque finally
        
        # Actualizar estado en registro de ejecuciones activas
        ejecuciones_activas[operacion_id] = "COMPLETADO"
        await manager.broadcast_json({"type": "operation_status_update", "operacion_id": operacion_id, "estado": "COMPLETADO", "resultado": resultado_final})
        
        # Enviar resultado a n8n vía webhook
        enviar_resultado_n8n(resultado_final) # Usar el resultado guardado
        
    except Exception as e:
        api_logger.error(f"Error al ejecutar arbitraje para operación {operacion_id}: {str(e)}", exc_info=e)
        
        # Actualizar estado en registro de ejecuciones activas
        ejecuciones_activas[operacion_id] = "ERROR"
        resultado_final = { # Actualizar resultado_final también en caso de error
            "operacion_id": operacion_id,
            "estado": "ERROR",
            "resultado": f"Error: {str(e)}",
            "pares_ejecutados": [],
            "comisiones": 0.0,
            "slippage": 0.0,
            "ganancia_neta": 0.0,
            "rentabilidad_real": 0.0,
            "tiempo_ejecucion": 0.0
        }
        await manager.broadcast_json({"type": "operation_status_update", "operacion_id": operacion_id, "estado": "ERROR", "error_message": str(e)})
        
        # Enviar resultado de error a n8n
        enviar_resultado_n8n(resultado_final)
    
    finally:
        # Limpiar registro después de un tiempo
        # Considerar hacer esto asíncrono si time.sleep bloquea el event loop de la tarea de fondo
        await asyncio.sleep(300)  # 5 minutos
        if operacion_id in ejecuciones_activas:
            del ejecuciones_activas[operacion_id]
        # Notificar al frontend que la operación ya no está "activa" en memoria del servidor API
        await manager.broadcast_json({"type": "operation_removed_from_active", "operacion_id": operacion_id})


def enviar_resultado_n8n(resultado: Dict[str, Any]): # Esta función es síncrona, lo cual está bien si es llamada desde una tarea de fondo que puede bloquearse.
    """
    Envía el resultado de la ejecución a n8n vía webhook.
    
    Args:
        resultado: Resultado de la ejecución.
    """
    try:
        # URL del webhook en n8n
        webhook_url = settings.n8n_webhook_resultado
        
        # Formatear datos para el formato esperado por n8n
        datos = {
            "body": resultado
        }
        
        # Enviar POST request
        response = requests.post(
            webhook_url,
            json=datos,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            api_logger.info(f"Resultado enviado correctamente a n8n para operación: {resultado.get('operacion_id')}")
        else:
            api_logger.error(f"Error al enviar resultado a n8n. Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        api_logger.error(f"Error al enviar resultado a n8n: {str(e)}", exc_info=e)

@app.post("/api/ejecutar-arbitraje")
async def ejecutar_solicitud(solicitud: SolicitudEjecucion, background_tasks: BackgroundTasks):
    """
    Endpoint para recibir solicitudes de ejecución de arbitraje.
    
    Args:
        solicitud: Datos para la ejecución del arbitraje.
        background_tasks: Tareas en segundo plano de FastAPI.
        
    Returns:
        Confirmación de recepción de la solicitud.
    """
    operacion_id = solicitud.operacion_id
    
    # Validar que la operación no esté ya en ejecución
    if operacion_id in ejecuciones_activas:
        # Notificar al frontend que la operación ya está activa
        await manager.broadcast_json({
            "type": "error", 
            "operacion_id": operacion_id,
            "message": f"La operación {operacion_id} ya está en ejecución con estado: {ejecuciones_activas[operacion_id]}"
        })
        raise HTTPException(
            status_code=409,
            detail=f"La operación {operacion_id} ya está en ejecución con estado: {ejecuciones_activas[operacion_id]}"
        )
    
    # Registrar la solicitud en Supabase
    try:
        operacion_data = {
            "operacion_id": operacion_id,
            "ruta_arbitraje": solicitud.oportunidad.get("ruta", ""),
            "capital_inicial": solicitud.oportunidad.get("capital", 0),
            "analisis_ia": solicitud.analisis_ia,
            "decision_usuario": solicitud.confirmacion_usuario.decision,
            "fecha_decision": solicitud.confirmacion_usuario.timestamp,
            "estado": "PENDIENTE" # Estado inicial antes de la tarea en segundo plano
        }
        
        if "oportunidad_id" in solicitud.oportunidad:
            operacion_data["oportunidad_detectada_id"] = solicitud.oportunidad["oportunidad_id"]
        
        supabase_client.insertar_operacion(operacion_data) # Esto es síncrono, podría bloquear si es lento
        api_logger.info(f"Registrada solicitud de ejecución para operación: {operacion_id}")
        await manager.broadcast_json({"type": "operation_status_update", "operacion_id": operacion_id, "estado": "PENDIENTE"})
        
    except Exception as e:
        api_logger.error(f"Error al registrar solicitud en Supabase: {str(e)}", exc_info=e)
        await manager.broadcast_json({
            "type": "error", 
            "operacion_id": operacion_id,
            "message": f"Error al registrar la solicitud en Supabase: {str(e)}"
        })
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar la solicitud: {str(e)}"
        )
    
    # Ejecutar arbitraje en background
    background_tasks.add_task(execute_arbitrage_task, solicitud)
    
    return {
        "operacion_id": operacion_id,
        "estado": "RECIBIDO", # El endpoint HTTP responde inmediatamente
        "mensaje": "Solicitud recibida y en procesamiento en segundo plano"
    }

@app.get("/api/estado/{operacion_id}")
async def obtener_estado(operacion_id: str):
    """
    Endpoint para consultar el estado de una operación.
    El frontend también recibirá actualizaciones vía WebSocket.
    """
    # Verificar en ejecuciones activas
    estado_actual = "DESCONOCIDO"
    if operacion_id in ejecuciones_activas:
        estado_actual = ejecuciones_activas[operacion_id]
        return {
            "operacion_id": operacion_id,
            "estado": estado_actual,
            "source": "active_memory"
        }
    
    # Si no está activa, consultar en Supabase
    try:
        operacion = supabase_client.obtener_operacion(operacion_id) # Síncrono
        if operacion:
            estado_actual = operacion.get("estado", "DESCONOCIDO_EN_DB")
            return {
                "operacion_id": operacion_id,
                "estado": estado_actual,
                "source": "database"
            }
        else:
            # Notificar al frontend si se consulta un ID no encontrado
            # await manager.broadcast_json({"type": "error", "operacion_id": operacion_id, "message": f"No se encontró la operación con ID: {operacion_id}"})
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró la operación con ID: {operacion_id}"
            )
    except Exception as e:
        api_logger.error(f"Error al consultar estado de operación {operacion_id}: {str(e)}", exc_info=e)
        # await manager.broadcast_json({"type": "error", "operacion_id": operacion_id, "message": f"Error al consultar estado de operación: {str(e)}"})
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar estado de operación: {str(e)}"
        )

def start_server():
    """Inicia el servidor API."""
    host = settings.api_host
    port = settings.api_port
    
    api_logger.info(f"Iniciando servidor API en {host}:{port}...")
    uvicorn.run(app, host=host, port=port)

# WebSocket Management
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        api_logger.info(f"WebSocket connection established: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        api_logger.info(f"WebSocket connection closed: {websocket.client}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_json(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_ip = websocket.client.host if websocket.client else "unknown_client"
    api_logger.info(f"WebSocket client connected: {client_ip}")
    try:
        while True:
            data = await websocket.receive_text()
            api_logger.info(f"WebSocket received: {data} from {client_ip}")
            
            try:
                message_data = json.loads(data)
                msg_type = message_data.get("type")

                if msg_type == "subscribe":
                    channels = message_data.get("channels", [])
                    api_logger.info(f"Client {client_ip} subscribed to channels: {channels}")
                    await manager.send_personal_message(json.dumps({"type": "subscription_ack", "status": "Subscribed", "channels": channels, "client_ip": client_ip}), websocket)
                    # Ejemplo de envío de datos de prueba al subscribirse
                    await manager.send_personal_message(json.dumps({"type": "market_data", "data": {"symbol": "BTC/USDT", "price": 60000.0, "timestamp": time.time()}}), websocket)
                    await manager.send_personal_message(json.dumps({"type": "trading_signal", "data": {"id": "signal1", "symbol": "ETH/USDT", "action": "BUY", "price": 3000.0, "strategy": "ScalpingTest", "timestamp": time.time()}}), websocket)

                elif msg_type == "execute_order":
                    # Aquí se manejaría la lógica para procesar una orden desde el frontend
                    # Esto podría implicar llamar a una función en AdvancedTradingEngine
                    # o interactuar directamente con el exchange_client.
                    # Por ahora, solo acusamos recibo.
                    api_logger.info(f"Received execute_order from {client_ip}: {message_data}")
                    await manager.send_personal_message(json.dumps({"type": "order_ack", "order_details": message_data, "status": "OrderReceived"}), websocket)
                    # Simular una actualización de posición después de una orden
                    await asyncio.sleep(1) # Simular procesamiento
                    await manager.broadcast_json({
                        "type": "position_update",
                        "data": {
                            "id": f"pos_{time.time()}",
                            "symbol": message_data.get("symbol", "UNKNOWN"),
                            "side": message_data.get("side", "BUY"),
                            "quantity": message_data.get("quantity", 0),
                            "entry_price": message_data.get("price", 0) or (60050.0 if message_data.get("symbol") == "BTC/USDT" else 3005.0), # Simular precio de entrada
                            "pnl": 0.0,
                            "status": "OPEN",
                            "timestamp": time.time()
                        }
                    })


                elif msg_type == "update_config":
                    api_logger.info(f"Received update_config from {client_ip}: {message_data.get('config')}")
                    # Lógica para actualizar configuración en el backend
                    await manager.send_personal_message(json.dumps({"type": "config_ack", "status": "ConfigUpdateReceived"}), websocket)

                else:
                    api_logger.warning(f"Unknown WebSocket message type: {msg_type} from {client_ip}")
                    await manager.send_personal_message(json.dumps({"type": "error", "message": f"Unknown message type: {msg_type}"}), websocket)

            except json.JSONDecodeError:
                api_logger.error(f"WebSocket received invalid JSON: {data} from {client_ip}")
                await manager.send_personal_message(json.dumps({"type": "error", "message": "Invalid JSON format"}), websocket)
            except Exception as e:
                api_logger.error(f"Error processing WebSocket message from {client_ip}: {str(e)}", exc_info=e)
                await manager.send_personal_message(json.dumps({"type": "error", "message": f"Error processing your message: {str(e)}"}), websocket)

    except WebSocketDisconnect:
        api_logger.info(f"WebSocket client disconnected: {client_ip}")
    except Exception as e:
        api_logger.error(f"WebSocket error for client {client_ip}: {str(e)}", exc_info=e)
    finally:
        if websocket in manager.active_connections:
            manager.disconnect(websocket)
        api_logger.info(f"WebSocket connection cleanup for {client_ip}")


if __name__ == "__main__":
    # Permitir ejecución directa para pruebas
    # Necesitarás importar asyncio si no está ya importado globalmente para el time.sleep asíncrono
    import asyncio # Asegurar que asyncio esté disponible en este scope si es necesario
    start_server()
