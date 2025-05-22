"""
Validador para el nodo "Evaluar Recomendación IA" de n8n.
Este script genera y envía datos de prueba para validar el correcto funcionamiento
del nodo "Evaluar Recomendación IA" en el flujo de n8n.
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
logger = get_logger("n8n_validador")

def generar_oportunidad_prueba(tipo_recomendacion: str) -> Dict[str, Any]:
    """
    Genera datos de prueba para una oportunidad de arbitraje con una recomendación específica.
    
    Args:
        tipo_recomendacion: El tipo de recomendación a incluir ('PROCEDER', 'PRECAUCION', 'DESCARTAR').
    
    Returns:
        Diccionario con datos de prueba.
    """
    # Datos base de la oportunidad
    oportunidad_base = {
        "ruta": "USDT -> BTC -> ETH -> USDT",
        "pares": ["BTCUSDT", "ETHBTC", "ETHUSDT"],
        "rentabilidad": 1.2,
        "capital": 100.0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Datos del análisis IA según el tipo de recomendación
    if tipo_recomendacion == "PROCEDER":
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
    elif tipo_recomendacion == "PRECAUCION":
        analisis_ia = {
            "recomendacion": "PRECAUCION",
            "confianza": 60,
            "rentabilidad_neta_estimada": 0.6,
            "riesgos_identificados": [
                "Slippage considerable en par ETHBTC",
                "Volatilidad alta en ETH",
                "Spread amplio en BTCUSDT"
            ],
            "explicacion": "Aunque la rentabilidad es positiva, hay factores de riesgo significativos que podrían reducir la ganancia efectiva."
        }
    else:  # DESCARTAR
        analisis_ia = {
            "recomendacion": "DESCARTAR",
            "confianza": 90,
            "rentabilidad_neta_estimada": 0.1,
            "riesgos_identificados": [
                "Liquidez insuficiente en ETHBTC",
                "Volatilidad extrema en ETH",
                "Spread excesivo en BTCUSDT",
                "Alta probabilidad de slippage > 1%"
            ],
            "explicacion": "Los riesgos y costos de ejecución superan la rentabilidad teórica, resultando en una operación potencialmente perdedora."
        }
    
    # Combinar en un solo objeto para enviar a webhook
    return {
        "body": {
            "oportunidad": oportunidad_base,
            "output": analisis_ia
        }
    }

def enviar_webhook(datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía datos de prueba al webhook de n8n.
    
    Args:
        datos: Datos de prueba a enviar.
    
    Returns:
        Respuesta del servidor.
    """
    try:
        webhook_url = settings.n8n_webhook_oportunidad
        logger.info(f"Enviando datos de prueba a: {webhook_url}")
        
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

def validar_recomendacion_ia():
    """
    Ejecuta la validación del nodo "Evaluar Recomendación IA".
    Envía datos para los 3 casos posibles y verifica la respuesta.
    """
    # Lista de tipos de recomendaciones a probar
    tipos_recomendacion = ["PROCEDER", "PRECAUCION", "DESCARTAR"]
    resultados = {}
    
    for tipo in tipos_recomendacion:
        logger.info(f"Probando recomendación: {tipo}")
        
        # Generar y enviar datos
        datos = generar_oportunidad_prueba(tipo)
        resultado = enviar_webhook(datos)
        
        resultados[tipo] = resultado
        
        logger.info(f"Resultado para {tipo}: {json.dumps(resultado, indent=2)}")
        print(f"\n{'='*50}")
        print(f"PRUEBA: {tipo}")
        print(f"{'='*50}")
        print(f"RESULTADO: {'ÉXITO' if resultado.get('status', 0) < 400 else 'ERROR'}")
        print(f"DETALLES: {json.dumps(resultado, indent=2)}")
        print(f"{'='*50}\n")
    
    return resultados

if __name__ == "__main__":
    # Configurar argumentos
    parser = argparse.ArgumentParser(description="Validador para nodos de n8n")
    parser.add_argument("--tipo", choices=["PROCEDER", "PRECAUCION", "DESCARTAR"], help="Tipo específico de recomendación a probar")
    
    args = parser.parse_args()
    
    if args.tipo:
        # Probar solo un tipo específico
        datos = generar_oportunidad_prueba(args.tipo)
        resultado = enviar_webhook(datos)
        print(f"\n{'='*50}")
        print(f"PRUEBA: {args.tipo}")
        print(f"{'='*50}")
        print(f"RESULTADO: {'ÉXITO' if resultado.get('status', 0) < 400 else 'ERROR'}")
        print(f"DETALLES: {json.dumps(resultado, indent=2)}")
        print(f"{'='*50}\n")
    else:
        # Probar todos los tipos
        validar_recomendacion_ia()
