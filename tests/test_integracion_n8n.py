"""
Script de prueba integrada para el flujo completo del Bot de Arbitraje Triangular.
Este script prueba la integración entre Python, n8n y Supabase.
"""

import sys
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

# Agregar directorio raíz al path para importar modules del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.logger import get_logger
from src.utils.config import settings
from src.apis.supabase_client import supabase_client

# Configurar logger
logger = get_logger("test_integracion")

def generar_operacion_prueba() -> Dict[str, Any]:
    """
    Genera una operación de prueba completa.
    
    Returns:
        Diccionario con datos de la operación.
    """
    operacion_id = f"test-{uuid.uuid4()}"
    
    # Datos de oportunidad
    oportunidad = {
        "ruta": "USDT -> BTC -> ETH -> USDT",
        "pares": ["BTCUSDT", "ETHBTC", "ETHUSDT"],
        "rentabilidad": 1.2,
        "capital": 100.0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Datos de análisis IA
    analisis_ia = {
        "recomendacion": "PROCEDER",
        "confianza": 85,
        "rentabilidad_neta_estimada": 0.9,
        "riesgos_identificados": [
            "Posible slippage en par ETHBTC",
            "Volatilidad moderada en ETH"
        ],
        "explicacion": "La oportunidad presenta buena rentabilidad ajustada por riesgo, con liquidez suficiente en todos los pares."
    }
    
    # Datos de confirmación de usuario
    confirmacion_usuario = {
        "timestamp": datetime.now().isoformat(),
        "decision": "Ejecutar"
    }
    
    # Combinar todo en el formato esperado por API
    return {
        "operacion_id": operacion_id,
        "oportunidad": oportunidad,
        "analisis_ia": analisis_ia,
        "confirmacion_usuario": confirmacion_usuario
    }

def enviar_oportunidad_webhook(datos_oportunidad: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía datos de oportunidad al webhook de n8n.
    
    Args:
        datos_oportunidad: Datos de la oportunidad a enviar.
    
    Returns:
        Respuesta del servidor.
    """
    try:
        webhook_url = settings.n8n_webhook_oportunidad
        logger.info(f"Enviando oportunidad a: {webhook_url}")
        
        # Formatear datos para webhook
        datos = {
            "body": {
                "oportunidad": datos_oportunidad["oportunidad"]
            }
        }
        
        # Hacer el request POST
        response = requests.post(
            webhook_url,
            json=datos,
            headers={"Content-Type": "application/json"}
        )
        
        # Comprobar respuesta
        response.raise_for_status()
        logger.info(f"Oportunidad enviada correctamente. Status: {response.status_code}")
        
        # Intentar parsear respuesta
        try:
            return response.json()
        except:
            return {"status": response.status_code, "text": response.text}
        
    except requests.RequestException as e:
        logger.error(f"Error al enviar oportunidad: {str(e)}", exc_info=e)
        return {"error": str(e)}

def enviar_analisis_webhook(operacion_id: str, datos_oportunidad: Dict[str, Any], analisis_ia: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía datos de análisis al webhook de n8n, simulando la respuesta del nodo IA.
    
    Args:
        operacion_id: ID de la operación.
        datos_oportunidad: Datos de la oportunidad.
        analisis_ia: Datos del análisis IA.
    
    Returns:
        Respuesta del servidor.
    """
    try:
        # Aquí usamos el ID del nodo después del análisis IA
        webhook_id = "68b2748f-3aa7-4d28-afc4-1465256970f9"  # ID del nodo "Evaluar Recomendación IA"
        webhook_url = f"http://localhost:5678/webhook/{webhook_id}"
        
        logger.info(f"Enviando análisis a: {webhook_url}")
        
        # Formatear datos para webhook
        datos = {
            "operacion_id": operacion_id,
            "oportunidad": datos_oportunidad["oportunidad"],
            "output": analisis_ia
        }
        
        # Hacer el request POST
        response = requests.post(
            webhook_url,
            json=datos,
            headers={"Content-Type": "application/json"}
        )
        
        # Comprobar respuesta
        response.raise_for_status()
        logger.info(f"Análisis enviado correctamente. Status: {response.status_code}")
        
        # Intentar parsear respuesta
        try:
            return response.json()
        except:
            return {"status": response.status_code, "text": response.text}
        
    except requests.RequestException as e:
        logger.error(f"Error al enviar análisis: {str(e)}", exc_info=e)
        return {"error": str(e)}

def enviar_decision_usuario(decision: str) -> Dict[str, Any]:
    """
    Envía decisión de usuario al webhook de n8n.
    
    Args:
        decision: Decisión del usuario ('Si' o 'No').
    
    Returns:
        Respuesta del servidor.
    """
    try:
        # Aquí usamos el ID del nodo "Esperar Confirmación Usuario"
        webhook_id = "9028c049-7a92-4a41-a0c8-c2b96b0b8872"
        webhook_url = f"http://localhost:5678/webhook/{webhook_id}"
        
        logger.info(f"Enviando decisión '{decision}' a: {webhook_url}")
        
        # Formatear datos para webhook
        datos = {
            "body": {
                "decision": decision,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Hacer el request POST
        response = requests.post(
            webhook_url,
            json=datos,
            headers={"Content-Type": "application/json"}
        )
        
        # Comprobar respuesta
        response.raise_for_status()
        logger.info(f"Decisión enviada correctamente. Status: {response.status_code}")
        
        # Intentar parsear respuesta
        try:
            return response.json()
        except:
            return {"status": response.status_code, "text": response.text}
        
    except requests.RequestException as e:
        logger.error(f"Error al enviar decisión: {str(e)}", exc_info=e)
        return {"error": str(e)}

def enviar_solicitud_api(datos_operacion: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía solicitud de ejecución a la API Python.
    
    Args:
        datos_operacion: Datos completos de la operación.
    
    Returns:
        Respuesta del servidor.
    """
    try:
        api_url = settings.api_url_ejecutar
        logger.info(f"Enviando solicitud a API: {api_url}")
        
        # Hacer el request POST
        response = requests.post(
            api_url,
            json=datos_operacion,
            headers={"Content-Type": "application/json"}
        )
        
        # Comprobar respuesta
        response.raise_for_status()
        logger.info(f"Solicitud enviada correctamente. Status: {response.status_code}")
        
        # Intentar parsear respuesta
        try:
            return response.json()
        except:
            return {"status": response.status_code, "text": response.text}
        
    except requests.RequestException as e:
        logger.error(f"Error al enviar solicitud a API: {str(e)}", exc_info=e)
        return {"error": str(e)}

def verificar_supabase(operacion_id: str) -> Dict[str, Any]:
    """
    Verifica si la operación se ha registrado correctamente en Supabase.
    
    Args:
        operacion_id: ID de la operación a verificar.
    
    Returns:
        Datos de la operación o diccionario vacío si no existe.
    """
    try:
        logger.info(f"Verificando operación {operacion_id} en Supabase...")
        
        # Intentar obtener la operación
        operacion = supabase_client.obtener_operacion(operacion_id)
        
        if operacion:
            logger.info(f"Operación encontrada en Supabase con estado: {operacion.get('estado')}")
            return operacion
        else:
            logger.warning(f"Operación {operacion_id} no encontrada en Supabase")
            return {}
        
    except Exception as e:
        logger.error(f"Error al verificar operación en Supabase: {str(e)}", exc_info=e)
        return {"error": str(e)}

def simular_resultado_ejecucion(operacion_id: str) -> Dict[str, Any]:
    """
    Simula el resultado de la ejecución de una operación.
    
    Args:
        operacion_id: ID de la operación.
    
    Returns:
        Datos del resultado simulado.
    """
    resultado = {
        "operacion_id": operacion_id,
        "estado": "COMPLETADO",
        "resultado": "EXITOSO",
        "pares_ejecutados": [
            "BTCUSDT (compra): 40000.0 USDT, 0.00250 BTC",
            "ETHBTC (compra): 0.0625 BTC, 0.04 ETH",
            "ETHUSDT (venta): 2600.0 USDT, 0.04 ETH"
        ],
        "comisiones": 0.25,
        "slippage": 0.08,
        "ganancia_neta": 1.15,
        "rentabilidad_real": 1.15,
        "tiempo_ejecucion": 3.2
    }
    
    return resultado

def enviar_resultado_webhook(resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía resultado de ejecución al webhook de n8n.
    
    Args:
        resultado: Datos del resultado de ejecución.
    
    Returns:
        Respuesta del servidor.
    """
    try:
        webhook_url = settings.n8n_webhook_resultado
        logger.info(f"Enviando resultado a: {webhook_url}")
        
        # Formatear datos para webhook
        datos = {
            "body": resultado
        }
        
        # Hacer el request POST
        response = requests.post(
            webhook_url,
            json=datos,
            headers={"Content-Type": "application/json"}
        )
        
        # Comprobar respuesta
        response.raise_for_status()
        logger.info(f"Resultado enviado correctamente. Status: {response.status_code}")
        
        # Intentar parsear respuesta
        try:
            return response.json()
        except:
            return {"status": response.status_code, "text": response.text}
        
    except requests.RequestException as e:
        logger.error(f"Error al enviar resultado: {str(e)}", exc_info=e)
        return {"error": str(e)}

def test_integracion_completa():
    """
    Ejecuta una prueba de integración completa del flujo de trabajo.
    
    Pasos:
    1. Generar operación de prueba
    2. Enviar oportunidad a n8n
    3. Enviar análisis IA a n8n
    4. Enviar decisión de usuario a n8n
    5. Verificar registro en Supabase
    6. Simular resultado de ejecución
    7. Enviar resultado a n8n
    8. Verificar actualización en Supabase
    """
    print(f"\n{'='*50}")
    print("PRUEBA DE INTEGRACIÓN COMPLETA")
    print(f"{'='*50}")
    
    # Paso 1: Generar operación de prueba
    datos_operacion = generar_operacion_prueba()
    operacion_id = datos_operacion["operacion_id"]
    
    print(f"Operación generada: {operacion_id}")
    
    # Paso 2: Enviar oportunidad a n8n
    print("\nPaso 1/7: Enviando oportunidad a n8n...")
    respuesta_oportunidad = enviar_oportunidad_webhook(datos_operacion)
    print(f"Respuesta: {json.dumps(respuesta_oportunidad, indent=2)}")
    
    # Esperar un poco para que n8n procese
    time.sleep(2)
    
    # Paso 3: Enviar análisis IA a n8n
    print("\nPaso 2/7: Enviando análisis IA a n8n...")
    respuesta_analisis = enviar_analisis_webhook(operacion_id, datos_operacion["oportunidad"], datos_operacion["analisis_ia"])
    print(f"Respuesta: {json.dumps(respuesta_analisis, indent=2)}")
    
    # Esperar un poco para que n8n procese
    time.sleep(2)
    
    # Paso 4: Enviar decisión de usuario a n8n
    print("\nPaso 3/7: Enviando decisión de usuario a n8n...")
    respuesta_decision = enviar_decision_usuario("Si")
    print(f"Respuesta: {json.dumps(respuesta_decision, indent=2)}")
    
    # Esperar un poco para que n8n procese
    time.sleep(2)
    
    # Paso 5: Enviar solicitud a API Python
    print("\nPaso 4/7: Enviando solicitud a API Python...")
    respuesta_api = enviar_solicitud_api(datos_operacion)
    print(f"Respuesta: {json.dumps(respuesta_api, indent=2)}")
    
    # Esperar un poco para que la API procese
    time.sleep(2)
    
    # Paso 6: Verificar registro en Supabase
    print("\nPaso 5/7: Verificando registro en Supabase...")
    operacion_supabase = verificar_supabase(operacion_id)
    if operacion_supabase:
        print(f"Operación encontrada con estado: {operacion_supabase.get('estado')}")
    else:
        print(f"⚠️ Operación no encontrada en Supabase")
    
    # Paso 7: Simular resultado de ejecución
    print("\nPaso 6/7: Simulando resultado de ejecución...")
    resultado = simular_resultado_ejecucion(operacion_id)
    print(f"Resultado generado: {json.dumps(resultado, indent=2)}")
    
    # Paso 8: Enviar resultado a n8n
    print("\nPaso 7/7: Enviando resultado a n8n...")
    respuesta_resultado = enviar_resultado_webhook(resultado)
    print(f"Respuesta: {json.dumps(respuesta_resultado, indent=2)}")
    
    # Esperar un poco para que n8n procese
    time.sleep(3)
    
    # Paso 9: Verificar actualización en Supabase
    print("\nVerificando actualización en Supabase...")
    operacion_actualizada = verificar_supabase(operacion_id)
    if operacion_actualizada:
        print(f"Operación actualizada con estado: {operacion_actualizada.get('estado')}")
    else:
        print(f"⚠️ Operación no encontrada en Supabase después de enviar resultado")
    
    print(f"\n{'='*50}")
    print(f"PRUEBA DE INTEGRACIÓN {'COMPLETADA' if operacion_actualizada and operacion_actualizada.get('estado') == 'COMPLETADO' else 'INCOMPLETA'}")
    print(f"{'='*50}\n")
    
    return {
        "operacion_id": operacion_id,
        "resultado_final": operacion_actualizada
    }

if __name__ == "__main__":
    # Verificar si la API Python está activa
    try:
        r = requests.get(f"http://{settings.api_host}:{settings.api_port}/api/health")
        if r.status_code == 200:
            print("✅ API Python activa y funcionando")
        else:
            print("⚠️ API Python responde, pero con estado incorrecto:", r.status_code)
    except:
        print("❌ Error: La API Python no está accesible. Asegúrese de iniciarla con:")
        print(f"   python main.py --mode api")
        print("   Abortando prueba de integración.")
        sys.exit(1)
    
    # Verificar si n8n está activo
    try:
        r = requests.get("http://localhost:5678/")
        if r.status_code == 200:
            print("✅ n8n activo y funcionando")
        else:
            print("⚠️ n8n responde, pero con estado incorrecto:", r.status_code)
    except:
        print("❌ Error: n8n no está accesible. Asegúrese de iniciarlo con:")
        print("   npx n8n start")
        print("   Abortando prueba de integración.")
        sys.exit(1)
    
    # Verificar conexión con Supabase
    try:
        r = supabase_client.obtener_tokens(limit=1)
        print("✅ Conexión con Supabase establecida")
    except:
        print("❌ Error: No se puede conectar con Supabase. Verifique las credenciales.")
        print("   Abortando prueba de integración.")
        sys.exit(1)
    
    # Ejecutar prueba de integración
    test_integracion_completa()
