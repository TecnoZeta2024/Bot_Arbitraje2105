"""
Módulo para calcular métricas de rendimiento de tokens.
"""

import math  # Import math for square root in volatility calculation
import time
from typing import Any, Dict, List

from ..utils.logger import get_logger

# Obtener logger específico
logger = get_logger("performance_calculator")

def calcular_metricas_rendimiento(datos_historicos: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calcula métricas de rendimiento a partir de datos históricos.

    Args:
        datos_historicos: Lista de datos históricos del token, cada elemento debe contener 'price' y 'timestamp'.

    Returns:
        Diccionario con métricas de rendimiento (rendimiento_1h, rendimiento_24h, rendimiento_7d, volatilidad).
    """
    try:
        if not datos_historicos:
            return {
                "rendimiento_1h": 0.0,
                "rendimiento_24h": 0.0,
                "rendimiento_7d": 0.0,
                "volatilidad": 0.0
            }

        # Ensure data is sorted by timestamp
        datos_historicos.sort(key=lambda x: x.get("timestamp", 0))

        precio_actual = datos_historicos[-1].get("price", 0)
        current_timestamp = datos_historicos[-1].get("timestamp", 0)

        # Calculate performance for 1 hour, 24 hours, and 7 days
        rendimiento_1h = 0.0
        rendimiento_24h = 0.0
        rendimiento_7d = 0.0

        for dato in datos_historicos:
            timestamp = dato.get("timestamp", 0)
            price = dato.get("price", 0)

            if current_timestamp - timestamp <= 3600 and precio_actual is not None and price is not None and price > 0:
                rendimiento_1h = ((precio_actual - price) / price) * 100

            if current_timestamp - timestamp <= 86400 and precio_actual is not None and price is not None and price > 0:
                 rendimiento_24h = ((precio_actual - price) / price) * 100

            if current_timestamp - timestamp <= 604800 and precio_actual is not None and price is not None and price > 0:
                 rendimiento_7d = ((precio_actual - price) / price) * 100


        # Calculate volatility (standard deviation of daily returns)
        precios_diarios = []
        last_day_timestamp = 0
        for dato in datos_historicos:
            timestamp = dato.get("timestamp", 0)
            # Assuming daily data points or taking the last price of each day
            if timestamp - last_day_timestamp >= 86400 or last_day_timestamp == 0:
                 precios_diarios.append(dato.get("price", 0))
                 last_day_timestamp = timestamp

        rendimientos_diarios = []
        for i in range(1, len(precios_diarios)):
            if precios_diarios[i-1] > 0:
                rendimientos_diarios.append((precios_diarios[i] - precios_diarios[i-1]) / precios_diarios[i-1] * 100)

        volatilidad = 0.0
        if len(rendimientos_diarios) > 1:
            avg_rendimiento = sum(rendimientos_diarios) / len(rendimientos_diarios)
            variance = sum([(r - avg_rendimiento) ** 2 for r in rendimientos_diarios]) / (len(rendimientos_diarios) - 1)
            volatilidad = math.sqrt(variance)


        return {
            "rendimiento_1h": round(rendimiento_1h, 2),
            "rendimiento_24h": round(rendimiento_24h, 2),
            "rendimiento_7d": round(rendimiento_7d, 2),
            "volatilidad": round(volatilidad, 2)
        }
    except Exception as e:
        logger.error(f"Error en calcular_metricas_rendimiento: {str(e)}", exc_info=e)
        return {
            "rendimiento_1h": 0.0,
            "rendimiento_24h": 0.0,
            "rendimiento_7d": 0.0,
            "volatilidad": 0.0
        }
