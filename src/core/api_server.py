"""
Servidor API para el Bot de Arbitraje Triangular.
Proporciona endpoints para recibir solicitudes de ejecución de arbitraje.
"""

import os
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import time
import uvicorn
from src.utils.logger import get_logger, api_logger
from src.utils.config import settings
from src.apis.supabase_client import supabase_client
from src.core.ejecutar_ciclo import ejecutar_arbitraje
from src.apis.gemini_client import gemini_client # Import Gemini client
from src.utils.prompt_formatter import PromptFormatter # Import PromptFormatter
import requests

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

    return {
        "status": "Opportunity received and Gemini analysis initiated",
        "data": opportunity_data.model_dump(),
        "gemini_analysis": gemini_analysis_result.model_dump() if gemini_analysis_result else None
    }


def execute_arbitrage_task(solicitud: SolicitudEjecucion):
    """
    Tarea en segundo plano para ejecutar el arbitraje.
    
    Args:
        solicitud: Datos de la solicitud de ejecución.
    """
    operacion_id = solicitud.operacion_id
    
    try:
        # Actualizar estado en registro de ejecuciones activas
        ejecuciones_activas[operacion_id] = "EJECUTANDO"
        
        # Ejecutar el arbitraje
        api_logger.info(f"Iniciando ejecución de arbitraje para operación: {operacion_id}")
        resultado = ejecutar_arbitraje(
            operacion_id=operacion_id,
            oportunidad=solicitud.oportunidad,
            analisis=solicitud.analisis_ia
        )
        
        # Actualizar estado en registro de ejecuciones activas
        ejecuciones_activas[operacion_id] = "COMPLETADO"
        
        # Enviar resultado a n8n vía webhook
        enviar_resultado_n8n(resultado)
        
    except Exception as e:
        api_logger.error(f"Error al ejecutar arbitraje para operación {operacion_id}: {str(e)}", exc_info=e)
        
        # Actualizar estado en registro de ejecuciones activas
        ejecuciones_activas[operacion_id] = "ERROR"
        
        # Enviar resultado de error a n8n
        resultado_error = {
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
        enviar_resultado_n8n(resultado_error)
    
    finally:
        # Limpiar registro después de un tiempo
        time.sleep(300)  # 5 minutos
        if operacion_id in ejecuciones_activas:
            del ejecuciones_activas[operacion_id]

def enviar_resultado_n8n(resultado: Dict[str, Any]):
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
            "estado": "PENDIENTE"
        }
        
        # Si hay un ID de oportunidad detectada, incluirlo
        if "oportunidad_id" in solicitud.oportunidad:
            operacion_data["oportunidad_detectada_id"] = solicitud.oportunidad["oportunidad_id"]
        
        # Insertar en Supabase
        supabase_client.insertar_operacion(operacion_data)
        api_logger.info(f"Registrada solicitud de ejecución para operación: {operacion_id}")
        
    except Exception as e:
        api_logger.error(f"Error al registrar solicitud en Supabase: {str(e)}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar la solicitud: {str(e)}"
        )
    
    # Ejecutar arbitraje en background
    background_tasks.add_task(execute_arbitrage_task, solicitud)
    
    return {
        "operacion_id": operacion_id,
        "estado": "RECIBIDO",
        "mensaje": "Solicitud recibida y en procesamiento"
    }

@app.get("/api/estado/{operacion_id}")
async def obtener_estado(operacion_id: str):
    """
    Endpoint para consultar el estado de una operación.
    
    Args:
        operacion_id: ID único de la operación.
        
    Returns:
        Estado actual de la operación.
    """
    # Verificar en ejecuciones activas
    if operacion_id in ejecuciones_activas:
        return {
            "operacion_id": operacion_id,
            "estado": ejecuciones_activas[operacion_id]
        }
    
    # Si no está activa, consultar en Supabase
    try:
        operacion = supabase_client.obtener_operacion(operacion_id)
        if operacion:
            return {
                "operacion_id": operacion_id,
                "estado": operacion.get("estado", "DESCONOCIDO")
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró la operación con ID: {operacion_id}"
            )
    except Exception as e:
        api_logger.error(f"Error al consultar estado de operación {operacion_id}: {str(e)}", exc_info=e)
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

if __name__ == "__main__":
    # Permitir ejecución directa para pruebas
    start_server()
