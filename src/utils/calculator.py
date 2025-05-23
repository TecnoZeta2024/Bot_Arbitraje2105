"""
Módulo de cálculos para el Bot de Arbitraje Triangular.
Proporciona funciones para calcular rentabilidad, comisiones, y otras métricas.
"""

from decimal import Decimal, getcontext
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Configurar precisión para cálculos decimales
getcontext().prec = 18

def calcular_rentabilidad_triangular(precios: List[float], volumes: List[float], comisiones: List[float]) -> Dict[str, float]:
    """
    Calcula la rentabilidad de un arbitraje triangular.
    
    Args:
        precios: Lista de precios [p1, p2, p3] para cada paso del arbitraje.
        volumes: Lista de volúmenes disponibles para cada par.
        comisiones: Lista de comisiones para cada paso (porcentajes).
    
    Returns:
        Un diccionario con métricas calculadas:
        - rentabilidad_bruta: Porcentaje antes de comisiones
        - rentabilidad_neta: Porcentaje después de comisiones
        - monto_comisiones: Monto total de comisiones
        - capital_final: Capital después del ciclo completo
    """
    # Convertir a Decimal para cálculos precisos
    p1, p2, p3 = map(Decimal, precios)
    c1, c2, c3 = map(lambda x: Decimal(x) / Decimal('100'), comisiones)
    
    # Capital inicial 1.0 (normalizado)
    capital_inicial = Decimal('1.0')
    
    # Calcular multiplicadores después de comisiones
    m1 = (Decimal('1.0') - c1) / p1
    m2 = (Decimal('1.0') - c2) * p2
    m3 = (Decimal('1.0') - c3) * p3
    
    # Capital final después del ciclo completo
    capital_final = capital_inicial * m1 * m2 * m3
    
    # Cálculo de rentabilidad
    rentabilidad_bruta = (float(p1 * p2 * p3) - 1.0) * 100
    rentabilidad_neta = (float(capital_final) - 1.0) * 100
    
    # Monto total en comisiones
    monto_comisiones = float(capital_inicial - capital_final + (p1 * p2 * p3 - Decimal('1.0')))
    
    return {
        "rentabilidad_bruta": round(rentabilidad_bruta, 6),
        "rentabilidad_neta": round(rentabilidad_neta, 6),
        "monto_comisiones": round(monto_comisiones, 6),
        "capital_final": float(capital_final)
    }

def estimar_slippage(volume_orden: float, profundidad_mercado: Dict[str, Any]) -> float:
    """
    Estima el slippage potencial basado en la profundidad del mercado.
    
    Args:
        volume_orden: Volumen de la orden a ejecutar.
        profundidad_mercado: Diccionario con datos del order book.
    
    Returns:
        Porcentaje estimado de slippage.
    """
    if volume_orden <= 0:
        return 0.0
    
    # Extraer datos del order book
    bids = profundidad_mercado.get('bids', [])
    asks = profundidad_mercado.get('asks', [])
    
    if not bids or not asks:
        return 0.0
    
    # Para un mercado comprador (bid)
    def calcular_slippage_bid(vol: float) -> float:
        precio_mejor = float(bids[0][0])
        volumen_acumulado = 0.0
        precio_promedio = 0.0
        
        for precio, volumen in bids:
            precio = float(precio)
            volumen = float(volumen)
            if volumen_acumulado + volumen >= vol:
                # Volumen restante necesario
                vol_restante = vol - volumen_acumulado
                precio_promedio = (precio_promedio * volumen_acumulado + precio * vol_restante) / vol
                break
            volumen_acumulado += volumen
            precio_promedio = (precio_promedio * volumen_acumulado + precio * volumen) / (volumen_acumulado + volumen)
            
        # Si no hay suficiente liquidez
        if volumen_acumulado < vol:
            return 5.0  # Valor alto indicando poca liquidez
        
        # Calcular slippage
        return ((precio_mejor - precio_promedio) / precio_mejor) * 100
    
    # Para un mercado vendedor (ask)
    def calcular_slippage_ask(vol: float) -> float:
        precio_mejor = float(asks[0][0])
        volumen_acumulado = 0.0
        precio_promedio = 0.0
        
        for precio, volumen in asks:
            precio = float(precio)
            volumen = float(volumen)
            if volumen_acumulado + volumen >= vol:
                # Volumen restante necesario
                vol_restante = vol - volumen_acumulado
                precio_promedio = (precio_promedio * volumen_acumulado + precio * vol_restante) / vol
                break
            volumen_acumulado += volumen
            precio_promedio = (precio_promedio * volumen_acumulado + precio * volumen) / (volumen_acumulado + volumen)
            
        # Si no hay suficiente liquidez
        if volumen_acumulado < vol:
            return 5.0  # Valor alto indicando poca liquidez
        
        # Calcular slippage
        return ((precio_promedio - precio_mejor) / precio_mejor) * 100
    
    # Asumiendo que necesitamos el promedio de ambos lados
    slippage_bid = calcular_slippage_bid(volume_orden)
    slippage_ask = calcular_slippage_ask(volume_orden)
    
    return (slippage_bid + slippage_ask) / 2

def calcular_comision_binance(monto: float, tipo_orden: str = "market") -> float:
    """
    Calcula la comisión de Binance según el tipo de orden.
    
    Args:
        monto: Monto de la operación.
        tipo_orden: Tipo de orden ("market", "limit").
    
    Returns:
        Monto de la comisión.
    """
    # Tasas actuales de Binance (pueden cambiar)
    tasas = {
        "market": 0.1,  # 0.1%
        "limit": 0.1    # 0.1%
    }
    
    tasa = tasas.get(tipo_orden.lower(), 0.1)
    return monto * (tasa / 100)

def calcular_spread(mejor_bid: float, mejor_ask: float) -> float:
    """
    Calcula el spread porcentual entre el mejor bid y ask.
    
    Args:
        mejor_bid: Mejor precio de compra.
        mejor_ask: Mejor precio de venta.
    
    Returns:
        Spread en porcentaje.
    """
    if mejor_bid <= 0 or mejor_ask <= 0:
        return 0.0
    
    return ((mejor_ask - mejor_bid) / mejor_bid) * 100

def normalizar_precios(precios: List[float]) -> List[float]:
    """
    Normaliza una lista de precios para evitar problemas numéricos.
    
    Args:
        precios: Lista de precios.
    
    Returns:
        Lista de precios normalizados.
    """
    return [float(p) for p in precios]
