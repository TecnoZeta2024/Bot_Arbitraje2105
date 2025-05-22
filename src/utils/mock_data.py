import pandas as pd
import numpy as np
import datetime
import random
from typing import List, Dict, Any, Optional

def generate_mock_operations(count: int = 100) -> List[Dict[str, Any]]:
    """
    Genera operaciones simuladas para desarrollo y pruebas
    
    Args:
        count (int): Número de operaciones a generar
        
    Returns:
        List[Dict]: Lista de operaciones simuladas
    """
    operations = []
    
    # Posibles estados
    estados = ["COMPLETADO", "FALLIDO", "CANCELADO", "PENDIENTE"]
    
    # Posibles rutas de arbitraje
    rutas = [
        "USDT → BTC → ETH → USDT",
        "USDT → ETH → BNB → USDT",
        "USDT → SOL → BTC → USDT",
        "USDT → BNB → ADA → USDT",
        "USDT → DOT → BTC → USDT"
    ]
    
    # Generar datos aleatorios
    for i in range(count):
        # Fecha aleatoria en los últimos 30 días
        fecha = datetime.datetime.now() - datetime.timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Estado aleatorio con probabilidades realistas
        estado = random.choices(
            estados, 
            weights=[0.65, 0.15, 0.10, 0.10],
            k=1
        )[0]
        
        # Determinar valores basados en estado
        if estado == "COMPLETADO":
            ganancia_neta = random.uniform(-2, 5)
            rentabilidad_real = random.uniform(-0.5, 2)
        else:
            ganancia_neta = 0
            rentabilidad_real = 0
            
        # Crear operación
        operation = {
            "operacion_id": f"OP-{i+1000}",
            "estado": estado,
            "ruta_arbitraje": random.choice(rutas),
            "capital_inicial": random.uniform(50, 200),
            "ganancia_neta": ganancia_neta,
            "rentabilidad_real": rentabilidad_real,
            "comisiones_totales": random.uniform(0.05, 0.25),
            "slippage_real": random.uniform(0.05, 0.5),
            "fecha_inicio_ejecucion": fecha.isoformat(),
            "fecha_completado": (fecha + datetime.timedelta(seconds=random.uniform(5, 30))).isoformat() if estado != "PENDIENTE" else None,
            "pares_ejecutados": generate_mock_pairs(random.choice(rutas))
        }
        
        operations.append(operation)
    
    return operations

def generate_mock_pairs(ruta: str) -> List[Dict[str, Any]]:
    """
    Genera pares de trading simulados basados en una ruta
    """
    tokens = ruta.replace("→", "").replace(" ", "").split()
    pairs = []
    
    for i in range(len(tokens) - 1):
        pairs.append({
            "symbol": f"{tokens[i+1]}{tokens[i]}",
            "step": i + 1,
            "price": random.uniform(0.001, 50000.0),
            "quantity": random.uniform(0.001, 2.0)
        })
    
    return pairs

def generate_mock_performance_metrics() -> Dict[str, Any]:
    """
    Genera métricas de rendimiento simuladas
    """
    return {
        "operaciones_totales": random.randint(80, 250),
        "operaciones_exitosas": random.randint(50, 150),
        "tasa_exito": random.uniform(0.6, 0.85),
        "ganancia_total": random.uniform(100, 500),
        "rentabilidad_promedio": random.uniform(0.8, 2.5),
        "mejor_ruta": "USDT → BTC → ETH → USDT",
        "capital_promedio": random.uniform(100, 250),
        "tiempo_promedio": random.uniform(12, 25),
        "comisiones_totales": random.uniform(25, 100),
        "operaciones_por_dia": random.uniform(5, 15)
    }

def generate_mock_realtime_opportunities(count: int = 5) -> List[Dict[str, Any]]:
    """
    Genera oportunidades de arbitraje simuladas en tiempo real
    """
    rutas = [
        "USDT → BTC → ETH → USDT",
        "USDT → ETH → BNB → USDT",
        "USDT → SOL → BTC → USDT",
        "USDT → BNB → ADA → USDT",
        "USDT → DOT → BTC → USDT",
        "USDT → AVAX → SOL → USDT",
        "USDT → LINK → ETH → USDT"
    ]
    
    opportunities = []
    
    for i in range(count):
        ruta = random.choice(rutas)
        rentabilidad = random.uniform(0.2, 3.0)
        confianza_ia = random.randint(60, 95)
        
        # La IA es más positiva con rentabilidades altas
        recomendacion = "PROCEDER" if rentabilidad > 1.5 and confianza_ia > 80 else \
                        "PRECAUCION" if rentabilidad > 0.8 else \
                        "DESCARTAR"
        
        opportunity = {
            "id": f"OPP-{random.randint(100, 999)}",
            "ruta": ruta,
            "rentabilidad_teorica": rentabilidad,
            "capital_sugerido": random.uniform(50, 200),
            "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=random.randint(0, 30))).isoformat(),
            "analisis_ia": {
                "recomendacion": recomendacion,
                "confianza": confianza_ia,
                "rentabilidad_neta_estimada": rentabilidad - random.uniform(0.1, 0.3),
                "riesgos_identificados": [
                    "Volatilidad elevada en últimos 30 minutos",
                    "Spread superior al promedio",
                    "Volumen bajo en uno de los pares"
                ] if recomendacion == "PRECAUCION" else [
                    "Slippage potencial elevado"
                ] if recomendacion == "DESCARTAR" else [
                    "Condiciones favorables"
                ]
            }
        }
        
        opportunities.append(opportunity)
    
    return opportunities

def generate_mock_config() -> Dict[str, Any]:
    """
    Genera configuración de sistema simulada
    """
    return {
        "filtrado_tokens": {
            "min_market_cap": 50000000,
            "min_volumen_binance": 1000000,
            "max_tokens": 50
        },
        "deteccion_oportunidades": {
            "min_rentabilidad": 0.5,
            "capital_default": 100,
            "intervalo_deteccion": 5  # minutos
        },
        "ejecucion": {
            "modo_testnet": True,
            "tiempo_espera_max": 300,  # segundos
            "reintentos_max": 3
        },
        "notificaciones": {
            "activar_telegram": True,
            "informe_diario": True,
            "alerta_oportunidades": True
        },
        "seguridad": {
            "max_operaciones_dia": 20,
            "capital_max_operacion": 200,
            "limite_perdida_diaria": 50
        }
    }
