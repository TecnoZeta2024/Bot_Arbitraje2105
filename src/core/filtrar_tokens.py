"""
Módulo para filtrado de tokens candidatos para arbitraje.
Obtiene datos de APIs externas y aplica filtros para seleccionar tokens adecuados.
"""

import time
from typing import Any, Dict, List, Optional

from ..apis.binance_client import binance_data_client
from ..apis.coingecko_client import coingecko_client
from ..apis.mobula_client import mobula_client
from ..apis.supabase_client import supabase_client
from ..utils.config import settings
from ..utils.logger import filtrado_logger, get_logger


def obtener_tokens_candidatos() -> List[Dict[str, Any]]:
    """
    Obtiene una lista combinada de tokens candidatos desde Mobula y CoinGecko.
    
    Returns:
        Lista de tokens con sus datos básicos.
    """
    tokens = []
    
    # Obtener tokens desde Mobula
    filtrado_logger.info("Obteniendo tokens desde Mobula...")
    mobula_tokens = mobula_client.obtener_tokens_top(limit=settings.max_tokens_considerados)
    
    for token in mobula_tokens:
        if "symbol" in token and "name" in token:
            tokens.append({
                "simbolo": token["symbol"],
                "nombre": token["name"],
                "market_cap": token.get("market_cap", 0),
                "source": "mobula"
            })
    
    # Obtener tokens desde CoinGecko para complementar
    filtrado_logger.info("Obteniendo tokens desde CoinGecko...")
    coingecko_tokens = coingecko_client.obtener_tokens_top(limit=settings.max_tokens_considerados)
    
    for token in coingecko_tokens:
        # Verificar si el token ya está en la lista
        exists = any(t["simbolo"] == token["symbol"].upper() for t in tokens)
        
        if not exists and "symbol" in token and "name" in token:
            tokens.append({
                "simbolo": token["symbol"].upper(),
                "nombre": token["name"],
                "market_cap": token.get("market_cap", 0),
                "source": "coingecko"
            })
    
    filtrado_logger.info(f"Total de tokens obtenidos: {len(tokens)}")
    return tokens

def filtrar_por_market_cap(tokens: List[Dict[str, Any]], min_market_cap: float = 500000000) -> List[Dict[str, Any]]:
    """
    Filtra tokens por capitalización de mercado mínima.
    
    Args:
        tokens: Lista de tokens a filtrar.
        min_market_cap: Capitalización de mercado mínima en USD.
        
    Returns:
        Lista de tokens filtrados.
    """
    filtrado_logger.info(f"Filtrando tokens con market cap >= ${min_market_cap/1000000}M...")
    filtered = [token for token in tokens if token.get("market_cap", 0) >= min_market_cap]
    filtrado_logger.info(f"Tokens después del filtro de market cap: {len(filtered)}")
    return filtered

def filtrar_por_disponibilidad_binance(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtra tokens que estén disponibles en Binance.
    
    Args:
        tokens: Lista de tokens a filtrar.
        
    Returns:
        Lista de tokens filtrados.
    """
    filtrado_logger.info("Obteniendo símbolos disponibles en Binance...")
    binance_symbols = binance_data_client.obtener_simbolos_trading()
    
    # Crear conjuntos de símbolos de base y quote (USDT, BTC, ETH, etc.)
    bases = set()
    quotes = set()
    
    for symbol in binance_symbols:
        # Buscar pares comunes
        for quote in ["USDT", "BTC", "ETH", "BNB", "BUSD"]:
            if symbol.endswith(quote):
                bases.add(symbol[:-len(quote)])
                quotes.add(quote)
                break
    
    filtrado_logger.info(f"Tokens base disponibles en Binance: {len(bases)}")
    filtrado_logger.info(f"Tokens quote disponibles en Binance: {list(quotes)}")
    
    # Filtrar tokens que estén en la lista de bases
    filtered = [token for token in tokens if token["simbolo"] in bases]
    filtrado_logger.info(f"Tokens disponibles en Binance: {len(filtered)}")
    
    return filtered

def obtener_metricas_token(token: Dict[str, Any]) -> Dict[str, Any]:
    """
    Obtiene métricas adicionales para un token.
    
    Args:
        token: Datos básicos del token.
        
    Returns:
        Token con métricas adicionales.
    """
    simbolo = token["simbolo"]
    token_data = token.copy()
    
    # Obtener métricas de rendimiento desde Mobula
    filtrado_logger.info(f"Obteniendo métricas para {simbolo}...")
    metricas = mobula_client.calcular_metricas_rendimiento(simbolo)
    
    token_data.update({
        "rendimiento_1h": metricas.get("rendimiento_1h", 0),
        "rendimiento_24h": metricas.get("rendimiento_24h", 0),
        "rendimiento_7d": metricas.get("rendimiento_7d", 0),
        "volatilidad": metricas.get("volatilidad", 0)
    })
    
    # Obtener volumen en Binance
    volumen = None
    for quote in ["USDT", "BTC", "ETH", "BNB", "BUSD"]:
        par = f"{simbolo}{quote}"
        vol = binance_data_client.obtener_volumen_24h(par)
        if vol:
            volumen = vol
            break
    
    token_data["volumen_binance_24h"] = volumen or 0
    
    return token_data

def filtrar_por_rendimiento(tokens: List[Dict[str, Any]], 
                           min_rendimiento_1h: float = 0.5,
                           min_rendimiento_24h: float = 3.0,
                           min_rendimiento_7d: float = 10.0) -> List[Dict[str, Any]]:
    """
    Filtra tokens por rendimiento mínimo.
    
    Args:
        tokens: Lista de tokens a filtrar.
        min_rendimiento_1h: Rendimiento mínimo en 1h (%).
        min_rendimiento_24h: Rendimiento mínimo en 24h (%).
        min_rendimiento_7d: Rendimiento mínimo en 7d (%).
        
    Returns:
        Lista de tokens filtrados.
    """
    filtrado_logger.info(f"Filtrando tokens por rendimiento (1h >= {min_rendimiento_1h}%, 24h >= {min_rendimiento_24h}%, 7d >= {min_rendimiento_7d}%)...")
    
    # Aplicar filtros de rendimiento
    filtered = []
    for token in tokens:
        if (token.get("rendimiento_1h", 0) >= min_rendimiento_1h or
            token.get("rendimiento_24h", 0) >= min_rendimiento_24h or
            token.get("rendimiento_7d", 0) >= min_rendimiento_7d):
            filtered.append(token)
    
    filtrado_logger.info(f"Tokens después del filtro de rendimiento: {len(filtered)}")
    return filtered

def filtrar_por_volumen(tokens: List[Dict[str, Any]], min_volumen: float = 1000000) -> List[Dict[str, Any]]:
    """
    Filtra tokens por volumen mínimo en Binance.
    
    Args:
        tokens: Lista de tokens a filtrar.
        min_volumen: Volumen mínimo en USD.
        
    Returns:
        Lista de tokens filtrados.
    """
    filtrado_logger.info(f"Filtrando tokens con volumen en Binance >= ${min_volumen/1000000}M...")
    filtered = [token for token in tokens if token.get("volumen_binance_24h", 0) >= min_volumen]
    filtrado_logger.info(f"Tokens después del filtro de volumen: {len(filtered)}")
    return filtered

def guardar_tokens_en_supabase(tokens: List[Dict[str, Any]]) -> int:
    """
    Guarda los tokens filtrados en Supabase.
    
    Args:
        tokens: Lista de tokens a guardar.
        
    Returns:
        Número de tokens guardados.
    """
    filtrado_logger.info(f"Guardando {len(tokens)} tokens en Supabase...")
    
    # Convertir a formato para Supabase
    tokens_data = []
    for token in tokens:
        token_data = {
            "simbolo": token["simbolo"],
            "nombre": token["nombre"],
            "market_cap": token.get("market_cap", 0),
            "rendimiento_1h": token.get("rendimiento_1h", 0),
            "rendimiento_24h": token.get("rendimiento_24h", 0),
            "rendimiento_7d": token.get("rendimiento_7d", 0),
            "volumen_binance_24h": token.get("volumen_binance_24h", 0),
            "fecha_actualizacion": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        tokens_data.append(token_data)
    
    # Insertar tokens en lotes para evitar limitaciones de API
    batch_size = 50
    for i in range(0, len(tokens_data), batch_size):
        batch = tokens_data[i:i+batch_size]
        try:
            supabase_client.insertar_tokens(batch)
        except Exception as e:
            filtrado_logger.error(f"Error al insertar lote de tokens en Supabase: {str(e)}", exc_info=e)
    
    filtrado_logger.info(f"Tokens guardados en Supabase: {len(tokens_data)}")
    return len(tokens_data)

def ejecutar_filtrado() -> Dict[str, Any]:
    """
    Ejecuta el proceso completo de filtrado de tokens.
    
    Returns:
        Diccionario con resultados del proceso.
    """
    start_time = time.time()
    
    filtrado_logger.info("Iniciando proceso de filtrado de tokens...")
    
    try:
        # Paso 1: Obtener tokens candidatos
        tokens = obtener_tokens_candidatos()
        inicial_count = len(tokens)
        
        # Paso 2: Filtrar por market cap
        tokens = filtrar_por_market_cap(tokens)
        
        # Paso 3: Filtrar por disponibilidad en Binance
        tokens = filtrar_por_disponibilidad_binance(tokens)
        
        # Paso 4: Obtener métricas adicionales para cada token
        tokens_con_metricas = []
        for token in tokens:
            token_data = obtener_metricas_token(token)
            tokens_con_metricas.append(token_data)
            # Pequeña pausa para evitar throttling de APIs
            time.sleep(0.1)
        
        # Paso 5: Filtrar por rendimiento
        tokens = filtrar_por_rendimiento(tokens_con_metricas)
        
        # Paso 6: Filtrar por volumen
        tokens = filtrar_por_volumen(tokens)
        
        # Paso 7: Guardar en Supabase
        tokens_guardados = guardar_tokens_en_supabase(tokens)
        
        # Calcular tiempo de ejecución
        execution_time = time.time() - start_time
        
        # Resultados
        result = {
            "tokens_iniciales": inicial_count,
            "tokens_filtrados": len(tokens),
            "tokens_guardados": tokens_guardados,
            "tiempo_ejecucion": round(execution_time, 2)
        }
        
        filtrado_logger.info(f"Proceso de filtrado completado: {result}")
        return result
        
    except Exception as e:
        filtrado_logger.error(f"Error en proceso de filtrado: {str(e)}", exc_info=e)
        return {
            "error": str(e),
            "tokens_filtrados": 0,
            "tokens_guardados": 0,
            "tiempo_ejecucion": round(time.time() - start_time, 2)
        }

if __name__ == "__main__":
    # Para permitir la ejecución directa para pruebas
    resultado = ejecutar_filtrado()
    print(resultado)
