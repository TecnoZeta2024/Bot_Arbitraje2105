"""
Validador para el nodo "Procesar Decisión Usuario" de n8n.
Este script genera y envía datos de prueba para validar el correcto funcionamiento
del nodo "Procesar Decisión Usuario" en el flujo de n8n.
"""

import argparse
import json
import requests
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Agregar directorio raíz al path para importar modules del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.config import settings
from src.utils.logger import get_logger

# Configurar logger
logger = get_logger("n8n_validador_decision")

def generar_decision_prueba(decision: str) -> Dict[str, Any]:
    """
    Genera datos de prueba para una decisión de usuario.
    
    Args:
        decision: La decisión del usuario ('Si' o 'No').
    
    Returns:
        Diccionario con datos de prueba.
    """
    return {
        "body": {
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
            "chat_id": settings.telegram_chat_id,
            "mensaje_id": "12345"  # ID ficticio para pruebas
        }
    }

def enviar_webhook(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía datos de prueba al webhook de n8n para decisión de usuario.
    
    Args:
        datos: Datos de prueba a enviar.
    
    Returns:
        Respuesta del servidor.
    """
    try:
        # Aquí usamos el ID del nodo "Esperar Confirmación Usuario" ya que es el que recibe la decisión
        webhook_id = "9028c049-7a92-4a41-a0c8-c2b96b0b8872"  # ID del webhook según el flujo n8n
        webhook_url = f"http://localhost:5678/webhook/{webhook_id}"
        
        logger.info(f"Enviando datos de decisión de prueba a: {webhook_url}")
        
        # Hacer el request POST
        response = requests.post(
            webhook_url,
            json=datos,
            headers={"Content-Type": "application/json"}
        )
        
        # Comprobar respuesta
        response.raise_for_status()
        logger.info(f"Datos enviados correctamente. Status: {response.status_code}")
        
        # Intentar parsear respuesta
        try:
            return response.json()
        except:
            return {"status": response.status_code, "text": response.text}
        
    except requests.RequestException as e:
        logger.error(f"Error al enviar datos: {str(e)}", exc_info=e)
        return {"error": str(e)}

def validar_decision_usuario():
    """
    Ejecuta la validación del nodo "Procesar Decisión Usuario".
    Envía datos para ambos casos posibles y verifica la respuesta.
    """
    # Probar ambas decisiones
    decisiones = ["Si", "No"]
    resultados = {}
    
    for decision in decisiones:
        logger.info(f"Probando decisión: {decision}")
        
        # Generar y enviar datos
        datos = generar_decision_prueba(decision)
        resultado = enviar_webhook(datos)
        
        resultados[decision] = resultado
        
        logger.info(f"Resultado para {decision}: {json.dumps(resultado, indent=2)}")
        print(f"\n{'='*50}")
        print(f"PRUEBA DECISIÓN: {decision}")
        print(f"{'='*50}")
        print(f"RESULTADO: {'ÉXITO' if resultado.get('status', 0) < 400 else 'ERROR'}")
        print(f"DETALLES: {json.dumps(resultado, indent=2)}")
        print(f"{'='*50}\n")
    
    return resultados

if __name__ == "__main__":
    # Configurar argumentos
    parser = argparse.ArgumentParser(description="Validador para nodo de decisión de usuario")
    parser.add_argument("--decision", choices=["Si", "No"], help="Decisión específica a probar")
    
    args = parser.parse_args()
    
    if args.decision:
        # Probar solo una decisión específica
        datos = generar_decision_prueba(args.decision)
        resultado = enviar_webhook(datos)
        print(f"\n{'='*50}")
        print(f"PRUEBA DECISIÓN: {args.decision}")
        print(f"{'='*50}")
        print(f"RESULTADO: {'ÉXITO' if resultado.get('status', 0) < 400 else 'ERROR'}")
        print(f"DETALLES: {json.dumps(resultado, indent=2)}")
        print(f"{'='*50}\n")
    else:
        # Probar ambas decisiones
        validar_decision_usuario()
