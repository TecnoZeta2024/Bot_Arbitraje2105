import itertools
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

import pandas as pd # Importar pandas
from src.data.exchange_adapters import BinanceAdapter, MobulaAdapter, IExchangeAdapter
from src.data.data_normalizer import DataNormalizer # Importar DataNormalizer
from src.domain.data_models import MarketDataUnified # Importar el esquema unificado
from src.dashboard.supabase_client import get_supabase_client, insertar_oportunidad  # Importar funciones
from src.core.telegram.telegram_handler import (
    telegram_handler,  # Import the TelegramHandler instance
)
from src.core.anomaly_detector import AnomalyDetector # Importar AnomalyDetector
from src.utils.calculator import calcular_rentabilidad_triangular
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger("deteccion")

"""
Módulo para detectar oportunidades de arbitraje triangular.
"""

def save_market_data_to_cache(symbols: List[str], tickers: Dict[str, float], cache_dir: str = "./cache") -> str:
    """
    Guarda los datos de mercado en caché, manteniendo solo los 5 archivos más recientes.
    
    Args:
        symbols: Lista de símbolos
        tickers: Diccionario de tickers
        cache_dir: Directorio para los archivos de caché
        
    Returns:
        str: Ruta del archivo de caché creado
    """
    os.makedirs(cache_dir, exist_ok=True)
    
    # Crear nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_data_{timestamp}.json"
    filepath = os.path.join(cache_dir, filename)
    
    # Guardar datos en formato JSON
    data = {
        "symbols": symbols,
        "tickers": tickers,
        "timestamp": timestamp
    }
    
    with open(filepath, "w") as f:
        json.dump(data, f)
    
    # Mantener solo los 5 archivos más recientes
    files = sorted([os.path.join(cache_dir, f) for f in os.listdir(cache_dir) 
                   if f.startswith("market_data_") and f.endswith(".json")])
    
    while len(files) > 5:
        os.remove(files[0])  # Eliminar el archivo más antiguo
        files = files[1:]  # Actualizar la lista
    
    logger.info(f"Datos de mercado guardados en caché: {filepath}")
    return filepath

def load_market_data_from_cache(cache_dir: str = "./cache") -> Tuple[Optional[List[str]], Optional[Dict[str, float]]]:
    """
    Carga los datos de mercado más recientes del caché.
    
    Args:
        cache_dir: Directorio de los archivos de caché
        
    Returns:
        tuple: (symbols, tickers) o (None, None) si no hay caché disponible
    """
    if not os.path.exists(cache_dir):
        logger.warning(f"Directorio de caché no encontrado: {cache_dir}")
        return None, None
    
    # Obtener el archivo de caché más reciente
    files = sorted([os.path.join(cache_dir, f) for f in os.listdir(cache_dir) 
                   if f.startswith("market_data_") and f.endswith(".json")])
    
    if not files:
        logger.warning("No hay archivos de caché disponibles")
        return None, None
    
    latest_file = files[-1]
    
    try:
        with open(latest_file, "r") as f:
            data = json.load(f)
        
        symbols = data.get("symbols", [])
        tickers = data.get("tickers", {})
        
        if not symbols or not tickers:
            logger.warning(f"Datos incompletos en el caché: {latest_file}")
            return None, None
        
        logger.info(f"Datos de mercado cargados desde caché: {latest_file}")
        return symbols, tickers
    
    except Exception as e:
        logger.error(f"Error al cargar datos de caché: {str(e)}")
        return None, None

def list_available_cache_files(cache_dir: str = "./cache") -> List[Dict[str, Any]]:
    """
    Lista los archivos de caché disponibles con su información.
    
    Args:
        cache_dir: Directorio de los archivos de caché
        
    Returns:
        List[Dict]: Lista de información de archivos de caché
    """
    if not os.path.exists(cache_dir):
        return []
    
    cache_files = []
    
    for filename in os.listdir(cache_dir):
        if filename.startswith("market_data_") and filename.endswith(".json"):
            filepath = os.path.join(cache_dir, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                
                # Extraer timestamp del nombre de archivo
                timestamp = data.get("timestamp", filename.split("_")[2].split(".")[0])
                
                # Formatear el timestamp para mostrar
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = timestamp
                
                cache_info = {
                    "filepath": filepath,
                    "timestamp": timestamp,
                    "formatted_time": formatted_time,
                    "symbols_count": len(data.get("symbols", [])),
                    "tickers_count": len(data.get("tickers", {}))
                }
                
                cache_files.append(cache_info)
            
            except Exception as e:
                logger.warning(f"Error al procesar archivo de caché {filename}: {str(e)}")
    
    # Ordenar por timestamp (más reciente primero)
    cache_files.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return cache_files

def load_specific_cache_file(filepath: str) -> Tuple[Optional[List[str]], Optional[Dict[str, float]]]:
    """
    Carga los datos de mercado desde un archivo de caché específico.
    
    Args:
        filepath: Ruta del archivo de caché a cargar
        
    Returns:
        tuple: (symbols, tickers) o (None, None) si hay error
    """
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        
        symbols = data.get("symbols", [])
        tickers = data.get("tickers", {})
        
        if not symbols or not tickers:
            logger.warning(f"Datos incompletos en el caché: {filepath}")
            return None, None
        
        logger.info(f"Datos de mercado cargados desde caché específico: {filepath}")
        return symbols, tickers
    
    except Exception as e:
        logger.error(f"Error al cargar datos de caché específico: {str(e)}")
        return None, None

def verificar_modulo_deteccion(binance_adapter: BinanceAdapter) -> Dict[str, Any]:
    """
    Verifica que el módulo de detección de oportunidades esté correctamente configurado.

    Args:
        binance_adapter (BinanceAdapter): Instancia del adaptador de Binance.
    
    Returns:
        dict: Resultado de la verificación
            {
                "success": bool,
                "message": str,
                "details": dict
            }
    """
    try:
        # Verificar la conexión con Binance
        # Usar el cliente interno del adaptador para obtener los mercados
        binance_markets = binance_adapter.binance_client.get_markets()
        
        if not binance_markets or len(binance_markets) == 0:
            return {
                "success": False,
                "message": "No se pudieron obtener los mercados de Binance",
                "details": {
                    "markets_count": 0
                }
            }
        
        # Verificar la conexión con Supabase (Optional, depending on dashboard needs)
        # from src.apis.supabase_client import SupabaseClient # Import locally to avoid circular dependency if not needed elsewhere
        # supabase_client = SupabaseClient()
        # connection_result = supabase_client.check_connection()
        
        # if not connection_result:
        #     return {
        #         "success": False,
        #         "message": "No se pudo conectar con Supabase",
        #         "details": {
        #             "binance_markets_count": len(binance_markets)
        #         }
        #     }
        
        # Verificar que hay al menos un número mínimo de mercados (e.g., 100)
        if len(binance_markets) < 100:
             return {
                 "success": False,
                 "message": f"No hay suficientes mercados en Binance ({len(binance_markets)}). Se requieren al menos 100 para una detección efectiva.",
                 "details": {
                     "markets_count": len(binance_markets)
                 }
             }

        # Verificar que se pueden obtener tickers
        # El adaptador no tiene un método get_tickers() que devuelva todos.
        # Usaremos el cliente interno para esta verificación.
        tickers = binance_adapter.binance_client.get_tickers()
        
        if not tickers or len(tickers) == 0:
            return {
                "success": False,
                "message": "No se pudieron obtener los tickers de Binance",
                "details": {
                    "tickers_count": 0
                }
            }
        
        # Comprobar que los componentes para el cálculo de triangulación funcionan
        # Only check imports, not full calculation execution
        from src.utils.calculator import calcular_rentabilidad_triangular

        # All checks passed
        return {
            "success": True,
            "message": "Módulo de detección correctamente configurado",
            "details": {
                "markets_count": len(binance_markets),
                "tickers_count": len(tickers)
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al verificar el módulo de detección: {str(e)}",
            "details": {
                "error": str(e)
            }
        }

async def fetch_market_data(
    binance_adapter: BinanceAdapter, 
    mobula_adapter: MobulaAdapter, 
    token_search_limit: int = 400,
    use_cache: bool = False,
    cache_dir: str = "./cache"
) -> tuple[List[str], Dict[str, float]] | tuple[None, None]:
    """
    Obtiene los símbolos y tickers, priorizando Mobula y usando Binance como fallback.
    Implementa limitación de symbols/tickers/parámetros por llamada API y soporte de caché.

    Args:
        binance_adapter (BinanceAdapter): Instancia del adaptador de Binance.
        mobula_adapter (MobulaAdapter): Instancia del adaptador de Mobula.
        token_search_limit (int): Límite de tokens a buscar en Mobula.
        use_cache (bool): Si True, intenta cargar datos desde caché primero.
        cache_dir (str): Directorio para los archivos de caché.

    Returns:
        tuple: (list of symbols, dict of tickers) o (None, None) si la obtención falla.
    """
    # Si se solicita usar caché, intentar cargar desde ahí primero
    if use_cache:
        logger.info("Intentando cargar datos de mercado desde caché...")
        symbols, tickers = load_market_data_from_cache(cache_dir)
        if symbols and tickers:
            logger.info(f"Usando datos de caché: {len(symbols)} símbolos, {len(tickers)} tickers")
            return symbols, tickers
        logger.info("No se encontraron datos en caché o son inválidos. Obteniendo datos nuevos.")
    logger.info("=== INICIANDO FETCH DE DATOS DE MERCADO ===")
    logger.info("Fetching market data (symbols and tickers), prioritizing Mobula...")
    data_normalizer = DataNormalizer() # Instanciar el normalizador/validador

    logger.info("=== INICIANDO FETCH DE DATOS DE MERCADO ===")
    logger.info("Fetching market data (symbols and tickers), prioritizing Mobula...")
    
    symbols = []
    tickers = {}
    
    # 1. Attempt to get data from Mobula and normalize/validate it
    try:
        binance_symbols_raw = binance_adapter.binance_client.obtener_simbolos_trading()
        if not binance_symbols_raw:
            logger.error("No se pudieron obtener símbolos de Binance. No se puede proceder.")
            return None, None
        
        symbols_to_fetch_mobula = binance_symbols_raw[:min(token_search_limit, len(binance_symbols_raw))]
        
        mobula_unified_data: List[MarketDataUnified] = []
        for symbol in symbols_to_fetch_mobula:
            try:
                raw_mobula_ticker = await mobula_adapter.get_raw_ticker(symbol)
                if raw_mobula_ticker:
                    market_data_unified = data_normalizer.normalize_ticker(raw_mobula_ticker, 'mobula')
                    if market_data_unified:
                        mobula_unified_data.append(market_data_unified)
            except Exception as e:
                logger.debug(f"No se pudo obtener o normalizar/validar ticker de Mobula para {symbol}: {e}")
        
        if mobula_unified_data:
            for data in mobula_unified_data:
                symbols.append(data.symbol)
                tickers[data.symbol] = float(data.price)
            logger.info(f"Obtenidos {len(symbols)} símbolos y {len(tickers)} tickers desde Mobula (normalizados y validados).")
        else:
            logger.warning("No se pudieron obtener datos de mercado válidos desde Mobula. Fallback a Binance.")
            
    except Exception as e:
        logger.error(f"Error fetching or normalizing/validating data from Mobula: {str(e)}. Fallback a Binance.", exc_info=e)

    # 2. Get tickers from Binance and normalize/validate them (if Mobula failed or as primary source)
    if not symbols or not tickers:
        try:
            binance_raw_tickers = binance_adapter.binance_client.obtener_precios_todos()
            if binance_raw_tickers:
                binance_unified_data: List[MarketDataUnified] = []
                for symbol, price in binance_raw_tickers.items():
                    # Crear un diccionario de datos brutos simulado para Binance para pasar al normalizador
                    # Asegurar que todos los campos obligatorios y opcionales estén presentes, incluso con valores por defecto
                    raw_binance_data = {
                        's': symbol,
                        'c': price, # Precio de cierre
                        'v': '0', # Volumen (no disponible en obtener_precios_todos, usar '0' como string para Decimal)
                        'q': '0', # Quote Volume
                        'h': '0', 'l': '0', 'o': '0', # High, Low, Open
                        'b': price, 'a': price, # Bid, Ask (usar precio como proxy)
                        'B': '0', 'A': '0', # Bid/Ask Qty
                        'E': int(datetime.now().timestamp() * 1000), # Timestamp en ms
                        'p': '0', 'P': '0', 'n': 0 # Price change, percentage, number of trades
                    }
                    # Normalizar y validar usando DataNormalizer
                    market_data_unified = data_normalizer.normalize_ticker(raw_binance_data, 'binance')
                    if market_data_unified:
                        binance_unified_data.append(market_data_unified)
                
                if binance_unified_data:
                    symbols = [data.symbol for data in binance_unified_data]
                    tickers = {data.symbol: float(data.price) for data in binance_unified_data}
                    logger.info(f"Obtenidos {len(symbols)} símbolos y {len(tickers)} tickers desde Binance (normalizados y validados).")
                else:
                    logger.error("No se pudieron normalizar/validar datos válidos desde Binance.")
                    return None, None
            else:
                logger.error("No se pudieron obtener los tickers desde Binance.")
                return None, None

        except Exception as e:
            logger.error(f"Error fetching or normalizing/validating tickers from Binance: {str(e)}", exc_info=e)
            return None, None

    if not symbols or not tickers:
        logger.error("Failed to fetch, normalize, and validate both symbols and tickers from any source.")
        return None, None

    logger.info(f"Market data fetch and transformation complete. Symbols: {len(symbols)}, Tickers: {len(tickers)}.")
    # Añadir logging para debug: mostrar algunos ejemplos de símbolos y tickers
    if symbols and len(symbols) > 0:
        logger.info(f"Sample symbols: {symbols[:5]}")
    if tickers and len(tickers) > 0:
        sample_tickers = dict(list(tickers.items())[:5])
        logger.info(f"Sample tickers: {sample_tickers}")
        
    # Guardar datos en caché si son válidos
    if symbols and tickers:
        try:
            cache_filepath = save_market_data_to_cache(symbols, tickers, cache_dir)
            logger.info(f"Datos de mercado guardados en caché: {cache_filepath}")
        except Exception as e:
            logger.warning(f"No se pudieron guardar los datos en caché: {str(e)}")
        
    logger.info(f"=== FETCH DE DATOS DE MERCADO FINALIZADO. Símbolos: {len(symbols) if symbols else 0}, Tickers: {len(tickers) if tickers else 0} ===")
    return symbols, tickers

def find_opportunities(symbols: List[str], tickers: Dict[str, float], umbral_rentabilidad: float, capital_inicial: float, fees_percentage: List[float] = [0.1, 0.1, 0.1]) -> List[Dict[str, Any]]:
    """
    Encuentra oportunidades de arbitraje triangular dadas los símbolos, tickers y parámetros. (Lógica para Encontrar Oportunidad)

    Args:
        symbols (List[str]): Lista de símbolos de trading disponibles.
        tickers (Dict[str, float]): Diccionario de tickers (símbolo: precio).
        umbral_rentabilidad (float): Umbral de rentabilidad mínima (en porcentaje).
        capital_inicial (float): Capital inicial sugerido para la operación.
        fees_percentage (List[float], optional): Lista de porcentajes de comisión por trade. Defaults to [0.1, 0.1, 0.1].

    Returns:
        List[Dict[str, Any]]: Lista de oportunidades encontradas.
    """
    logger.info("=== INICIANDO BÚSQUEDA DE OPORTUNIDADES TRIANGULARES ===")
    logger.info(f"Parámetros de búsqueda: Umbral={umbral_rentabilidad}%, Capital={capital_inicial}")
    logger.info("Finding triangular opportunities...")

    # fees_percentage ya tiene un valor por defecto en la firma de la función.
    # if fees_percentage is None:
    #     fees_percentage = [0.1, 0.1, 0.1] # Default fee: 0.1% per trade

    oportunidades_encontradas_list = []
    umbral_rentabilidad_decimal = umbral_rentabilidad / 100.0 # Convert to decimal

    # Lista ampliada de cotizaciones comunes para mejor parsing
    COMMON_QUOTES = [
        "USDT", "BUSD", "USDC", "DAI", "TUSD", "FDUSD", "BTC", "ETH", "BNB", "XRP", 
        "SOL", "DOGE", "TRX", "DOT", "MATIC", "AVAX", "SHIB", "LINK", "UNI", "ADA",
        "WETH", "WBTC", "EUR", "USD", "RUB", "GBP", "JPY", "AUD", "CAD", "CHF"
    ]
    
    # Lista de bases comunes
    COMMON_BASES = [
        "BTC", "ETH", "BNB", "XRP", "SOL", "DOGE", "TRX", "DOT", "MATIC", "AVAX", 
        "SHIB", "LINK", "UNI", "ADA", "LTC", "ETC", "ATOM", "ALGO", "VET", "NEAR"
    ]
    
    # Obtener todas las monedas únicas de los símbolos
    all_coins = set()
    parsed_symbols_count = 0
    failed_parsing_count = 0
    
    # Diagnóstico profundo: inspeccionar la coincidencia entre símbolos y tickers
    symbols_in_tickers = 0
    symbols_with_valid_price = 0
    
    # Lista para almacenar diagnósticos de algunos símbolos (para debugging)
    symbol_diagnostics = []
    
    # Recorrer algunos símbolos para diagnóstico detallado (limitando a los primeros 20 para evitar logs excesivos)
    for i, symbol in enumerate(symbols[:min(20, len(symbols))]):
        price = tickers.get(symbol)
        in_tickers = symbol in tickers
        valid_price = price is not None and price > 0
        
        # Almacenar diagnóstico
        symbol_diagnostics.append({
            "symbol": symbol,
            "in_tickers": in_tickers,
            "price": price,
            "valid_price": valid_price
        })
        
        if in_tickers:
            symbols_in_tickers += 1
        if valid_price:
            symbols_with_valid_price += 1
    
    # Registrar diagnóstico
    logger.info(f"Análisis de coincidencia de símbolos (muestra de {min(20, len(symbols))} símbolos):")
    for diag in symbol_diagnostics:
        logger.info(f"- Símbolo: {diag['symbol']}, Existe en tickers: {diag['in_tickers']}, Precio: {diag['price']}, Precio válido: {diag['valid_price']}")
    
    logger.info(f"De la muestra analizada: {symbols_in_tickers} existen en tickers, {symbols_with_valid_price} tienen precio válido")
    
    # PROBLEMA: Posible formato incorrecto entre símbolos de Mobula y tickers de Binance
    # SOLUCIÓN: Probar con coincidencia parcial de nombre si la coincidencia exacta falla
    active_symbols = {}
    symbols_matched = 0
    
    # Primero probar con coincidencia exacta
    for symbol in symbols:
        if symbol in tickers and tickers.get(symbol, 0) > 0:
            active_symbols[symbol] = tickers[symbol]
            symbols_matched += 1
    
    # Si no tenemos suficientes coincidencias, probar con un enfoque más flexible
    if symbols_matched < 10:  # Umbral arbitrario para activar la estrategia alternativa
        logger.info("Pocas coincidencias exactas, probando con coincidencia flexible de símbolos")
        
        # Crear mapas para búsqueda eficiente
        symbol_map = {s.upper(): s for s in symbols}
        ticker_map = {t.upper(): t for t in tickers.keys()}
        
        # Encontrar coincidencias aproximadas (por ejemplo, BTC vs BTCUSDT)
        for ticker_key in ticker_map:
            for symbol_key in symbol_map:
                # Si el símbolo es parte del ticker o viceversa
                if (symbol_key in ticker_key or ticker_key in symbol_key) and len(symbol_key) > 2:  # Evitar coincidencias con símbolos muy cortos
                    original_ticker = ticker_map[ticker_key]
                    price = tickers.get(original_ticker, 0)
                    if price > 0:
                        # Añadir a active_symbols usando el ticker original de Binance
                        if original_ticker not in active_symbols:
                            active_symbols[original_ticker] = price
                            symbols_matched += 1
                            
                            # Limitar el logging para no saturar
                            if symbols_matched <= 20:
                                logger.info(f"Coincidencia flexible: '{symbol_map[symbol_key]}' → '{original_ticker}' (precio: {price})")
    
    # Mostrar cuántos símbolos están activos (tienen ticker válido)
    logger.info(f"Símbolos activos con ticker válido: {len(active_symbols)} de {len(symbols)}")
    
    # PROBLEMA: Con muy pocos símbolos activos puede que no encontremos monedas
    # SOLUCIÓN: 1) Trabajar directamente con los tickers y extraer monedas de ellos
    
    # Si tenemos muy pocos símbolos activos (<10), usar los tickers directamente
    if len(active_symbols) < 10:
        logger.info(f"Muy pocos símbolos activos ({len(active_symbols)}). Extrayendo monedas directamente de tickers")
        
        # Usar una muestra de tickers si hay demasiados (para eficiencia)
        sample_size = min(500, len(tickers))
        sample_tickers = dict(list(tickers.items())[:sample_size])
        
        logger.info(f"Analizando {len(sample_tickers)} tickers para extraer monedas")
        
        # Procesar los tickers para extraer monedas
        coin_extractors = [
            # Patrón 1: Moneda contra USDT (ej: BTCUSDT -> BTC)
            lambda t: (t[:-4], "USDT") if t.endswith("USDT") and len(t) > 4 else None,
            # Patrón 2: Moneda contra BTC (ej: ETHBTC -> ETH)
            lambda t: (t[:-3], "BTC") if t.endswith("BTC") and len(t) > 3 else None,
            # Patrón 3: Moneda contra ETH (ej: LINKETH -> LINK)
            lambda t: (t[:-3], "ETH") if t.endswith("ETH") and len(t) > 3 else None,
            # Patrón 4: Moneda contra BNB (ej: ADABNB -> ADA)
            lambda t: (t[:-3], "BNB") if t.endswith("BNB") and len(t) > 3 else None,
        ]
        
        coins_extracted = set()
        
        for ticker in sample_tickers:
            for extractor in coin_extractors:
                result = extractor(ticker)
                if result:
                    coin, quote = result
                    coins_extracted.add(coin)
                    coins_extracted.add(quote)
        
        # Añadir monedas extraídas al conjunto all_coins
        all_coins.update(coins_extracted)
        logger.info(f"Extraídas {len(coins_extracted)} monedas directamente de tickers")
    
    # Usar active_symbols para símbolos válidos SÓLO si tenemos suficientes
    if len(active_symbols) >= 10:
        # Procesar símbolos activos para extraer monedas
        for symbol in active_symbols:
            try:
                base = None
                quote = None
                
                # 1. Buscar por cotizaciones comunes (más efectivo)
                for common_quote in COMMON_QUOTES:
                    if symbol.endswith(common_quote):
                        potential_base = symbol[:-len(common_quote)]
                        # Validar que la base no esté vacía
                        if potential_base:
                            base = potential_base
                            quote = common_quote
                            break
                
                # 2. Si no se encuentra por cotización, intentar por base común
                if not base or not quote:
                    for common_base in COMMON_BASES:
                        if symbol.startswith(common_base) and len(symbol) > len(common_base):
                            base = common_base
                            quote = symbol[len(common_base):]
                            break
                
                # 3. Si aún no se encuentra, intentar dividir el símbolo por la mitad (útil en algunos casos)
                if not base or not quote:
                    # Solo para símbolos de longitud razonable (entre 5 y 12 caracteres)
                    if 5 <= len(symbol) <= 12:
                        # Intentar dividir en diferentes puntos
                        for split_point in range(3, len(symbol)-2):
                            potential_base = symbol[:split_point]
                            potential_quote = symbol[split_point:]
                            # Verificar si alguno de los componentes es reconocible
                            if potential_base in COMMON_BASES or potential_quote in COMMON_QUOTES:
                                base = potential_base
                                quote = potential_quote
                                break
                
                # Si se ha identificado base y quote, añadirlos al conjunto
                if base and quote:
                    all_coins.add(base)
                    all_coins.add(quote)
                    parsed_symbols_count += 1
                else:
                    failed_parsing_count += 1
                    # Solo registrar algunos fallos para no llenar los logs
                    if failed_parsing_count <= 10:
                        logger.debug(f"No se pudo parsear el símbolo en base/quote: {symbol}")
                    elif failed_parsing_count == 11:
                        logger.debug("Omitiendo más mensajes de fallos de parseo...")
                        
            except Exception as e:
                failed_parsing_count += 1
                if failed_parsing_count <= 5:
                    logger.warning(f"Error al parsear símbolo: {symbol} - {e}")
                continue

    all_coins = list(all_coins)
    logger.info(f"Identificadas {len(all_coins)} monedas únicas. Símbolos parseados: {parsed_symbols_count}, Fallos: {failed_parsing_count}")
    
    # Si no hay monedas identificadas, usar algunas monedas comunes para pruebas
    if len(all_coins) == 0:
        logger.warning("No se pudieron identificar monedas. Usando monedas comunes para pruebas")
        all_coins = ["BTC", "ETH", "USDT", "BNB", "XRP", "ADA", "DOT", "DOGE", "LINK", "SOL"]
        logger.info(f"Usando {len(all_coins)} monedas predefinidas para pruebas")
    
    # Mejoras de rendimiento: reducir el número de combinaciones potenciales
    # Si hay demasiadas monedas, limitar a las más comunes
    MAX_COINS_FOR_COMBINATIONS = 100  # Límite razonable para controlar el tiempo de procesamiento
    
    if len(all_coins) > MAX_COINS_FOR_COMBINATIONS:
        # Priorizar monedas conocidas
        priority_coins = [coin for coin in all_coins if coin in COMMON_BASES + COMMON_QUOTES]
        # Completar con otras monedas hasta el límite si es necesario
        remaining_coins = [coin for coin in all_coins if coin not in priority_coins]
        remaining_slots = MAX_COINS_FOR_COMBINATIONS - len(priority_coins)
        
        if remaining_slots > 0:
            all_coins = priority_coins + remaining_coins[:remaining_slots]
        else:
            all_coins = priority_coins[:MAX_COINS_FOR_COMBINATIONS]
            
        logger.info(f"Limitando a {len(all_coins)} monedas para combinaciones de arbitraje")
    
    # PROBLEMA: No estamos usando correctamente los tickers cuando no hay símbolos activos
    # SOLUCIÓN: Usar directamente el diccionario de tickers completo
    
    # Crear un mapa de pares disponibles para búsqueda rápida (usando todos los tickers válidos)
    available_pairs = {}
    
    # Si tenemos suficientes símbolos activos, usarlos
    if len(active_symbols) >= 10:
        logger.info(f"Usando {len(active_symbols)} símbolos activos para available_pairs")
        available_pairs = active_symbols
    else:
        # Si no, usar todos los tickers disponibles 
        for symbol, price in tickers.items():
            if price is not None and price > 0:
                available_pairs[symbol] = price
        logger.info(f"Usando todos los {len(available_pairs)} tickers válidos para available_pairs")
    
    logger.info(f"Pares disponibles para arbitraje: {len(available_pairs)} (con precios válidos)")
    
    # Variables para estadísticas y debug
    total_combinations = 0
    valid_triangles = 0
    opportunities_above_threshold = 0
    
    # Definir un límite de combinaciones para log de progreso
    PROGRESS_LOG_INTERVAL = 1000000  # Loguear cada millón de combinaciones
    
    # Realizar algunas verificaciones para debugging
    if total_combinations == 0 and len(all_coins) >= 3:
        sample_coins = all_coins[:min(5, len(all_coins))]
        logger.info(f"Ejemplos de monedas: {sample_coins}")
        
        # Verificar si hay al menos algunos pares formados por estas monedas
        sample_pairs_found = 0
        for i, coin1 in enumerate(sample_coins):
            for j, coin2 in enumerate(sample_coins):
                if i != j:
                    # Verificar si existe el par en ambas direcciones
                    pair1 = f"{coin1}{coin2}"
                    pair2 = f"{coin2}{coin1}"
                    if pair1 in available_pairs:
                        logger.info(f"Par encontrado: {pair1} (precio: {available_pairs[pair1]})")
                        sample_pairs_found += 1
                    if pair2 in available_pairs:
                        logger.info(f"Par encontrado: {pair2} (precio: {available_pairs[pair2]})")
                        sample_pairs_found += 1
        
        logger.info(f"De la muestra de monedas, se encontraron {sample_pairs_found} pares en available_pairs")
    
    # Procesar todas las combinaciones de 3 monedas
    # PROBLEMA: Con pocas monedas identificadas, podemos no tener suficientes combinaciones
    # SOLUCIÓN: Verificar que tenemos suficientes monedas antes de intentar
    
    if len(all_coins) >= 3:
        for coin_a, coin_b, coin_c in itertools.combinations(all_coins, 3):
            total_combinations += 1
            
            # Log de progreso para combinaciones grandes
            if total_combinations % PROGRESS_LOG_INTERVAL == 0:
                logger.info(f"Progreso: {total_combinations} combinaciones procesadas, {valid_triangles} triángulos válidos, {opportunities_above_threshold} oportunidades encontradas")
            
            # Encontrar los pares que conectan A, B, y C en cualquier dirección
            pair_ab_symbol = None
            if f"{coin_a}{coin_b}" in available_pairs: 
                pair_ab_symbol = f"{coin_a}{coin_b}"
            elif f"{coin_b}{coin_a}" in available_pairs: 
                pair_ab_symbol = f"{coin_b}{coin_a}"
    
            # Si no se encuentra el primer par, saltar temprano
            if not pair_ab_symbol:
                continue
                
            pair_bc_symbol = None
            if f"{coin_b}{coin_c}" in available_pairs: 
                pair_bc_symbol = f"{coin_b}{coin_c}"
            elif f"{coin_c}{coin_b}" in available_pairs: 
                pair_bc_symbol = f"{coin_c}{coin_b}"
                
            # Si no se encuentra el segundo par, saltar temprano
            if not pair_bc_symbol:
                continue
    
            pair_ca_symbol = None
            if f"{coin_c}{coin_a}" in available_pairs: 
                pair_ca_symbol = f"{coin_c}{coin_a}"
            elif f"{coin_a}{coin_c}" in available_pairs: 
                pair_ca_symbol = f"{coin_a}{coin_c}"
                
            # Verificar si tenemos los tres pares necesarios para formar un triángulo
            if pair_ab_symbol and pair_bc_symbol and pair_ca_symbol:
                valid_triangles += 1
                
                # Para el primer triángulo válido, mostrar detalle para debugging
                if valid_triangles == 1:
                    logger.info(f"Primer triángulo encontrado: {coin_a}-{coin_b}-{coin_c}")
                    logger.info(f"Pares: {pair_ab_symbol}, {pair_bc_symbol}, {pair_ca_symbol}")
                    logger.info(f"Precios: {available_pairs[pair_ab_symbol]}, {available_pairs[pair_bc_symbol]}, {available_pairs[pair_ca_symbol]}")
                
                # Obtener precios directamente de available_pairs para mayor eficiencia
                price_ab = available_pairs[pair_ab_symbol]
                price_bc = available_pairs[pair_bc_symbol]
                price_ca = available_pairs[pair_ca_symbol]

                # Verificación adicional (debería ser redundante dado el filtrado previo)
                if price_ab > 0 and price_bc > 0 and price_ca > 0:

                    # Ciclo 1: A -> B -> C -> A
                    try:
                        # Calcular factor para A -> B con protección contra división por cero
                        if pair_ab_symbol == f"{coin_a}{coin_b}": # A/B
                            factor_ab = price_ab
                        else: # B/A
                            # Protección contra división por cero o números muy pequeños
                            if price_ab < 1e-10:
                                continue
                            factor_ab = 1 / price_ab

                        # Calcular factor para B -> C
                        if pair_bc_symbol == f"{coin_b}{coin_c}": # B/C
                            factor_bc = price_bc
                        else: # C/B
                            if price_bc < 1e-10:
                                continue
                            factor_bc = 1 / price_bc

                        # Calcular factor para C -> A
                        if pair_ca_symbol == f"{coin_c}{coin_a}": # C/A
                            factor_ca = price_ca
                        else: # A/C
                            if price_ca < 1e-10:
                                continue
                            factor_ca = 1 / price_ca

                        # Beneficio bruto para A -> B -> C -> A
                        gross_profit_factor_1 = factor_ab * factor_bc * factor_ca
                        rentabilidad_bruta_1 = (gross_profit_factor_1 - 1) * 100

                        # Filtrar resultados con rentabilidad negativa o sospechosamente alta
                        # (a veces pueden ser errores de cálculo o datos)
                        if rentabilidad_bruta_1 <= 0 or rentabilidad_bruta_1 > 1000:
                            continue
                            
                        if rentabilidad_bruta_1 > umbral_rentabilidad:
                            opportunities_above_threshold += 1
                        logger.info(f"Oportunidad encontrada (A->B->C->A): {coin_a} -> {coin_b} -> {coin_c} -> {coin_a}")
                        logger.info(f"Pares: {pair_ab_symbol}, {pair_bc_symbol}, {pair_ca_symbol}")
                        logger.info(f"Precios: {price_ab}, {price_bc}, {price_ca}")
                        logger.info(f"Factores: {factor_ab}, {factor_bc}, {factor_ca}")
                        logger.info(f"Rentabilidad Bruta: {rentabilidad_bruta_1:.6f}%")

                        # Calculate net profitability considering fees
                        net_profit_calc_result_1 = calcular_rentabilidad_triangular(
                            precios=[factor_ab, factor_bc, factor_ca], # Pass factors
                            volumes=[0, 0, 0], # Volumes not used in current calc_rentabilidad_triangular
                            comisiones=fees_percentage
                        )
                        rentabilidad_neta_1 = net_profit_calc_result_1["rentabilidad_neta"]

                        # Determine steps and estimated amounts based on initial capital
                        current_amount = capital_inicial
                        steps_1 = []

                        # Step 1: A -> B
                        steps_1.append({
                            "order": 1,
                            "from_coin": coin_a,
                            "to_coin": coin_b,
                            "pair": pair_ab_symbol,
                            "amount_in": round(current_amount, 8) # Round for precision
                        })
                        current_amount *= factor_ab * (1 - fees_percentage[0]/100) # Apply fee

                        # Step 2: B -> C
                        steps_1.append({
                            "order": 2,
                            "from_coin": coin_b,
                            "to_coin": coin_c,
                            "pair": pair_bc_symbol,
                            "amount_in": round(current_amount, 8)
                        })
                        current_amount *= factor_bc * (1 - fees_percentage[1]/100) # Apply fee

                        # Step 3: C -> A
                        steps_1.append({
                            "order": 3,
                            "from_coin": coin_c,
                            "to_coin": coin_a,
                            "pair": pair_ca_symbol,
                            "amount_in": round(current_amount, 8)
                        })
                        # Final amount after cycle is current_amount * factor_ca * (1 - fees_percentage[2]/100)


                        opportunity_data = {
                            "opportunity_id": f"{int(time.time())}-{len(oportunidades_encontradas_list) + 1}",
                            "cycle": f"{coin_a} -> {coin_b} -> {coin_c} -> {coin_a}",
                            "profit_percentage_gross": round(rentabilidad_bruta_1, 6),
                            "profit_percentage_net": round(rentabilidad_neta_1, 6),
                            "steps": steps_1,
                            "capital_inicial": capital_inicial,
                            "capital_sugerido": capital_inicial
                        }
                        oportunidades_encontradas_list.append(opportunity_data)


                    except Exception as e:
                        # Si hay un error en los cálculos del ciclo 1, registrarlo y continuar
                        logger.debug(f"Error en cálculos del ciclo 1 ({coin_a}-{coin_b}-{coin_c}): {str(e)}")
                        continue

                    # Ciclo 2: A -> C -> B -> A
                    try:
                        # Calcular factor para A -> C con protección
                        if pair_ca_symbol == f"{coin_a}{coin_c}": # A/C
                            factor_ac = price_ca
                        else: # C/A
                            if price_ca < 1e-10:
                                continue
                            factor_ac = 1 / price_ca

                        # Calcular factor para C -> B
                        if pair_bc_symbol == f"{coin_c}{coin_b}": # C/B
                            factor_cb = price_bc
                        else: # B/C
                            if price_bc < 1e-10:
                                continue
                            factor_cb = 1 / price_bc

                        # Calcular factor para B -> A
                        if pair_ab_symbol == f"{coin_b}{coin_a}": # B/A
                            factor_ba = price_ab
                        else: # A/B
                            if price_ab < 1e-10:
                                continue
                            factor_ba = 1 / price_ab

                        # Beneficio bruto para A -> C -> B -> A
                        gross_profit_factor_2 = factor_ac * factor_cb * factor_ba
                        rentabilidad_bruta_2 = (gross_profit_factor_2 - 1) * 100

                        # Filtrar resultados con rentabilidad negativa o sospechosamente alta
                        if rentabilidad_bruta_2 <= 0 or rentabilidad_bruta_2 > 1000:
                            continue
                            
                        if rentabilidad_bruta_2 > umbral_rentabilidad:
                            opportunities_above_threshold += 1
                        logger.info(f"Oportunidad encontrada (A->C->B->A): {coin_a} -> {coin_c} -> {coin_b} -> {coin_a}")
                        logger.info(f"Pares: {pair_ca_symbol}, {pair_bc_symbol}, {pair_ab_symbol}")
                        logger.info(f"Precios: {price_ca}, {price_bc}, {price_ab}")
                        logger.info(f"Factores: {factor_ac}, {factor_cb}, {factor_ba}")
                        logger.info(f"Rentabilidad Bruta: {rentabilidad_bruta_2:.6f}%")

                        # Calculate net profitability considering fees
                        net_profit_calc_result_2 = calcular_rentabilidad_triangular(
                            precios=[factor_ac, factor_cb, factor_ba], # Pass factors
                            volumes=[0, 0, 0], # Volumes not used in current calc_rentabilidad_triangular
                            comisiones=fees_percentage
                        )
                        rentabilidad_neta_2 = net_profit_calc_result_2["rentabilidad_neta"]

                        # Determine steps and estimated amounts based on initial capital
                        current_amount = capital_inicial
                        steps_2 = []

                        # Step 1: A -> C
                        steps_2.append({
                            "order": 1,
                            "from_coin": coin_a,
                            "to_coin": coin_c,
                            "pair": pair_ca_symbol,
                            "amount_in": round(current_amount, 8)
                        })
                        current_amount *= factor_ac * (1 - fees_percentage[0]/100) # Apply fee

                        # Step 2: C -> B
                        steps_2.append({
                            "order": 2,
                            "from_coin": coin_c,
                            "to_coin": coin_b,
                            "pair": pair_bc_symbol,
                            "amount_in": round(current_amount, 8)
                        })
                        current_amount *= factor_cb * (1 - fees_percentage[1]/100) # Apply fee

                        # Step 3: B -> A
                        steps_2.append({
                            "order": 3,
                            "from_coin": coin_b,
                            "to_coin": coin_a,
                            "pair": pair_ab_symbol,
                            "amount_in": round(current_amount, 8)
                        })
                        # Final amount after cycle is current_amount * factor_ba * (1 - fees_percentage[2]/100)


                        opportunity_data = {
                            "opportunity_id": f"{int(time.time())}-{len(oportunidades_encontradas_list) + 1}",
                            "cycle": f"{coin_a} -> {coin_c} -> {coin_b} -> {coin_a}",
                            "profit_percentage_gross": round(rentabilidad_bruta_2, 6),
                            "profit_percentage_net": round(rentabilidad_neta_2, 6),
                            "steps": steps_2,
                            "capital_inicial": capital_inicial,
                            "capital_sugerido": capital_inicial
                        }
                        oportunidades_encontradas_list.append(opportunity_data)

                    except Exception as e:
                        # Si hay un error en los cálculos del ciclo 2, registrarlo y continuar
                        logger.debug(f"Error en cálculos del ciclo 2 ({coin_a}-{coin_c}-{coin_b}): {str(e)}")
                        continue
    else:
            logger.warning(f"No se pudieron procesar combinaciones: se requieren al menos 3 monedas (identificadas: {len(all_coins)})")
            
    # Filtrar las oportunidades con rentabilidad negativa antes de devolverlas
    filtered_opportunities = [
        opp for opp in oportunidades_encontradas_list 
        if opp["profit_percentage_net"] > 0
    ]
    
    # Registrar la diferencia
    filtered_out = len(oportunidades_encontradas_list) - len(filtered_opportunities)
    if filtered_out > 0:
        logger.info(f"Se filtraron {filtered_out} oportunidades con rentabilidad negativa o cero.")
    
    # Ensure a list is always returned
    logger.info(f"=== BÚSQUEDA DE OPORTUNIDADES TRIANGULARES FINALIZADA. Oportunidades encontradas: {len(filtered_opportunities)} ===")
    return filtered_opportunities  # Devolver solo oportunidades positivas


async def ejecutar_deteccion(
    binance_adapter: BinanceAdapter, 
    mobula_adapter: MobulaAdapter, 
    webhook_url: Optional[str] = None,
    use_cache: bool = False,
    cache_filepath: Optional[str] = None,
    cache_dir: str = "./cache"
) -> List[Dict[str, Any]]:
    """
    Detecta oportunidades de arbitraje triangular en Binance y, opcionalmente, las envía a un webhook.
    Esta función orquesta el proceso completo de detección y envío.
    
    Args:
        binance_adapter: Adaptador de Binance
        mobula_adapter: Adaptador de Mobula
        webhook_url: URL del webhook para enviar oportunidades (opcional)
        use_cache: Si True, intenta usar datos del caché
        cache_filepath: Si se especifica, usa un archivo de caché específico
        cache_dir: Directorio para archivos de caché
        
    Returns:
        List[Dict[str, Any]]: Lista de oportunidades encontradas
    """
    start_time = time.time()
    logger.info("=== INICIANDO ORQUESTACIÓN DE DETECCIÓN DE OPORTUNIDADES TRIANGULARES ===")
    logger.info(f"Parámetros de ejecución: webhook_url={webhook_url}, use_cache={use_cache}, cache_filepath={cache_filepath}")
    logger.info(f"Parámetros de configuración:")
    
    try:
        # Verificar que los adaptadores son válidos
        if not binance_adapter:
            logger.error("Error: Adaptador Binance no proporcionado o inválido")
            return [] # Devolver lista vacía en caso de error
            
        if not mobula_adapter:
            logger.warning("Advertencia: Adaptador Mobula no proporcionado. Solo se usarán datos de Binance.")
            
        # Obtener y validar parámetros de configuración
        try:
            umbral_rentabilidad = settings.umbral_rentabilidad
            if not isinstance(umbral_rentabilidad, (int, float)) or umbral_rentabilidad <= 0:
                logger.warning(f"Umbral de rentabilidad inválido: {umbral_rentabilidad}. Usando valor predeterminado: 1.0%")
                umbral_rentabilidad = 1.0
                
            capital_inicial = settings.capital_inicial
            if not isinstance(capital_inicial, (int, float)) or capital_inicial <= 0:
                logger.warning(f"Capital inicial inválido: {capital_inicial}. Usando valor predeterminado: 100")
                capital_inicial = 100.0
                
            logger.info(f"- Umbral de rentabilidad: {umbral_rentabilidad}%")
            logger.info(f"- Capital inicial: {capital_inicial}")
            if webhook_url:
                logger.info(f"- Webhook URL configurado: {webhook_url[:30]}...")
            else:
                logger.info("- Webhook URL no configurado. No se enviarán oportunidades.")
                
        except AttributeError as e:
            logger.error(f"Error al acceder a configuración: {str(e)}. Usando valores predeterminados.")
            umbral_rentabilidad = 1.0
            capital_inicial = 100.0

        # Instanciar el detector de anomalías
        anomaly_detector = AnomalyDetector(
            z_score_threshold=settings.anomaly_z_score_threshold,
            contamination=settings.anomaly_isolation_forest_contamination
        )
        logger.info(f"Detector de anomalías inicializado con Z-score threshold: {settings.anomaly_z_score_threshold}, Isolation Forest contamination: {settings.anomaly_isolation_forest_contamination}")

        # Obtener datos de mercado
        logger.info("Obteniendo datos de mercado...")
        
        if cache_filepath:
            logger.info(f"Usando archivo de caché específico: {cache_filepath}")
            symbols, tickers = load_specific_cache_file(cache_filepath)
        else:
            symbols, tickers = await fetch_market_data(
                binance_adapter, 
                mobula_adapter,
                use_cache=use_cache,
                cache_dir=cache_dir
            )
        
        if not symbols or not tickers:
            logger.error("Error: No se pudieron obtener datos de mercado para la ejecución.")
            return []
            
        logger.info(f"Datos de mercado obtenidos exitosamente: {len(symbols)} símbolos, {len(tickers)} tickers")
        
        # Convertir tickers a DataFrame para detección de anomalías
        # Asegurarse de que el DataFrame tenga un índice y una columna numérica para el precio
        tickers_df = pd.DataFrame.from_dict(tickers, orient='index', columns=['price'])
        tickers_df.index.name = 'symbol'
        
        logger.info("Realizando detección de anomalías en los datos de mercado...")
        anomalies_results = await anomaly_detector.detect_anomalies(tickers_df, columns_for_z_score=['price'])
        
        # Unir los resultados de anomalías con los tickers originales para fácil acceso
        # Esto crea un DataFrame con 'price' y las columnas 'is_anomaly_z_score_price', 'is_anomaly_isolation_forest', 'is_overall_anomaly'
        market_data_with_anomalies = tickers_df.join(anomalies_results)
        
        # Opcional: Filtrar o registrar anomalías antes de buscar oportunidades
        anomalous_symbols = market_data_with_anomalies[market_data_with_anomalies['is_overall_anomaly']].index.tolist()
        if anomalous_symbols:
            logger.warning(f"Anomalías detectadas en los siguientes símbolos: {anomalous_symbols}")
            # Aquí se podría implementar una lógica para descartar símbolos anómalos
            # o para enviar una alerta específica sobre ellos.
            # Por ahora, solo se loguea.
        else:
            logger.info("No se detectaron anomalías en los datos de mercado.")

        logger.info("Buscando oportunidades de arbitraje triangular...")
        
        # Buscar oportunidades
        start_finding = time.time()
        opportunities = find_opportunities(symbols, tickers, umbral_rentabilidad, capital_inicial)
        finding_time = time.time() - start_finding
        
        # Procesar resultados
        if opportunities:
            logger.info(f"¡Éxito! Se encontraron {len(opportunities)} oportunidades en {finding_time:.2f} segundos.")
            
            # Mostrar detalles de las mejores oportunidades (limitado a 3 para no saturar logs)
            top_opportunities = sorted(opportunities, key=lambda x: x["profit_percentage_net"], reverse=True)[:3]
            logger.info("Mejores oportunidades encontradas:")
            
            for i, opp in enumerate(top_opportunities, 1):
                logger.info(f"{i}. {opp['cycle']} - Rentabilidad neta: {opp['profit_percentage_net']}%, Capital: {opp['capital_sugerido']}")
            
            # Integrate with TelegramHandler to send notification and request confirmation
            logger.info(f"Sending {len(opportunities)} opportunities for Telegram notification and confirmation and logging to Supabase...")
            
            # Obtener la instancia del cliente Supabase
            supabase_client_instance = get_supabase_client()

            for opportunity_data in opportunities:
                try:
                    # Adjuntar información de anomalías a la oportunidad si el símbolo es anómalo
                    # Extraer los símbolos involucrados en la oportunidad
                    involved_symbols = []
                    cycle_parts = opportunity_data['cycle'].split(' -> ')
                    if len(cycle_parts) >= 3: # Asegurarse de que hay al menos 3 partes para extraer símbolos
                        involved_symbols.append(cycle_parts[0]) # Coin A
                        involved_symbols.append(cycle_parts[1]) # Coin B
                        involved_symbols.append(cycle_parts[2]) # Coin C
                        
                    opportunity_anomalies = {}
                    for symbol in involved_symbols:
                        if symbol in market_data_with_anomalies.index:
                            symbol_anomalies = market_data_with_anomalies.loc[symbol]
                            if symbol_anomalies['is_overall_anomaly']:
                                opportunity_anomalies[symbol] = {
                                    'is_anomaly_z_score_price': bool(symbol_anomalies.get('is_anomaly_z_score_price', False)),
                                    'is_anomaly_isolation_forest': bool(symbol_anomalies.get('is_anomaly_isolation_forest', False)),
                                    'price_at_detection': float(symbol_anomalies['price']) # Convertir Decimal a float para JSON
                                }
                    
                    if opportunity_anomalies:
                        opportunity_data['anomalies_detected'] = opportunity_anomalies
                        logger.warning(f"Oportunidad {opportunity_data.get('opportunity_id', 'N/A')} involucra símbolos anómalos: {opportunity_anomalies}")
                    else:
                        opportunity_data['anomalies_detected'] = {} # Asegurar que el campo existe

                    # Log initial opportunity to Supabase
                    insertar_oportunidad(opportunity_data) # Usar la función directamente
                    logger.info(f"Logged initial opportunity {opportunity_data.get('opportunity_id', 'N/A')} to Supabase.")

                    # Call the new method in TelegramHandler
                    # This method will handle sending the message and registering the pending operation
                    await telegram_handler.notify_opportunity_for_confirmation(opportunity_data)
                    logger.info(f"Sent opportunity {opportunity_data.get('opportunity_id', 'N/A')} for Telegram processing.")
                except Exception as e:
                    logger.error(f"Error processing opportunity {opportunity_data.get('opportunity_id', 'N/A')} for logging or Telegram: {e}", exc_info=e)
                    
        else:
            logger.info(f"No se encontraron oportunidades que superen el umbral de {umbral_rentabilidad}% en {finding_time:.2f} segundos.")
            logger.info("Sugerencias: Considere reducir el umbral de rentabilidad o ampliar el rango de tokens analizados.")

    except Exception as e:
        logger.error(f"Error general durante la detección de oportunidades: {str(e)}", exc_info=e)
        return []
        
    finally:
        # Registrar tiempo total y mensaje de finalización
        total_time = time.time() - start_time
        logger.info(f"=== DETECCIÓN FINALIZADA EN {total_time:.2f} SEGUNDOS ===")
        
        # Devolver las opportunities encontradas (although they are now sent to TelegramHandler)
        return opportunities


async def run_detection_and_send_to_webhook(binance_adapter: BinanceAdapter, mobula_adapter: MobulaAdapter, umbral_rentabilidad: float, capital_inicial: float, webhook_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Ejecuta el proceso de detección con los parámetros especificados y envía los resultados a un webhook.

    Args:
        binance_adapter (BinanceAdapter): Instancia del adaptador de Binance.
        mobula_adapter (MobulaAdapter): Instancia del adaptador de Mobula.
        umbral_rentabilidad (float): Umbral mínimo de rentabilidad (en porcentaje).
        capital_inicial (float): Capital inicial sugerido para la operación.
        webhook_url (Optional[str]): URL del webhook al que enviar las oportunidades.

    Returns:
        List[Dict[str, Any]]: Lista de oportunidades encontradas.
    """
    start_time = time.time()
    logger.info("=== INICIANDO RUN_DETECTION_AND_SEND_TO_WEBHOOK ===")
    logger.info(f"Ejecutando detección con umbral de {umbral_rentabilidad}% y capital de {capital_inicial}")
    
    try:
        # Validar parámetros de entrada
        if umbral_rentabilidad < 0:
            logger.warning(f"Umbral de rentabilidad negativo: {umbral_rentabilidad}%. Usando valor absoluto.")
            umbral_rentabilidad = abs(umbral_rentabilidad)
            
        if capital_inicial <= 0:
            logger.warning(f"Capital inicial inválido: {capital_inicial}. Usando valor predeterminado: 100")
            capital_inicial = 100.0
            
        # Obtener datos de mercado
        logger.info("Obteniendo datos de mercado...")
        symbols, tickers = await fetch_market_data(binance_adapter, mobula_adapter)
        
        if not symbols or not tickers:
            logger.error("No se pudieron obtener datos de mercado para la detección y envío al webhook.")
            return []
            
        logger.info(f"Datos obtenidos exitosamente. Buscando oportunidades...")
        
        # Buscar oportunidades
        start_finding = time.time()
        opportunities = find_opportunities(symbols, tickers, umbral_rentabilidad, capital_inicial)
        finding_time = time.time() - start_finding
        
        # Procesar resultados
        if opportunities:
            logger.info(f"Se encontraron {len(opportunities)} oportunidades en {finding_time:.2f} segundos.")
            
            # Enviar al webhook si está configurado
            if webhook_url:
                logger.info(f"Enviando resultados al webhook: {webhook_url[:30]}...")
                sent_count = 0
                failed_count = 0
                
                for opportunity_data in opportunities:
                    try:
                        response = requests.post(webhook_url, json=opportunity_data, timeout=10)
                        response.raise_for_status()
                        sent_count += 1
                        
                        # Limitar logging detallado a las primeras 3 oportunidades
                        if sent_count <= 3:
                            logger.info(f"Enviada oportunidad {opportunity_data.get('cycle')} (ID: {opportunity_data.get('opportunity_id', 'N/A')})")
                    except requests.exceptions.RequestException as e:
                        failed_count += 1
                        logger.error(f"Error al enviar oportunidad: {str(e)}", exc_info=e)
                        
                logger.info(f"Envío completado: {sent_count} exitosos, {failed_count} fallidos")
            else:
                logger.info("No se envió a webhook porque no se proporcionó URL.")
        else:
            logger.info(f"No se encontraron oportunidades que superen el umbral de {umbral_rentabilidad}%.")
            
    except Exception as e:
        logger.error(f"Error durante el proceso de detección y envío: {str(e)}", exc_info=e)
        return []
        
    finally:
        # Registrar tiempo total
        total_time = time.time() - start_time
        logger.info(f"Proceso completado en {total_time:.2f} segundos")
        
    return opportunities


# Código para ejecutar la verificación o detección directamente
if __name__ == "__main__":
    import asyncio
    logger.info("Iniciando script de detección de oportunidades...")
    # Instantiate adapters here and pass them to the orchestrator function
    binance_adapter_instance = BinanceAdapter(trading=False) # For data fetching
    mobula_adapter_instance = MobulaAdapter()
    
    # Use the new function for command line execution if webhook is configured
    if settings.n8n_webhook_oportunidad:
        asyncio.run(run_detection_and_send_to_webhook(
            binance_adapter_instance,
            mobula_adapter_instance,
            settings.umbral_rentabilidad,
            settings.capital_inicial,
            settings.n8n_webhook_oportunidad
        ))
    else:
        # Or just run detection without sending if no webhook
        asyncio.run(ejecutar_deteccion(binance_adapter_instance, mobula_adapter_instance))
    logger.info("Script de detección de oportunidades finalizado.")

def send_opportunities_to_webhook(opportunities: List[Dict[str, Any]], webhook_url: str) -> bool:
    """
    Sends a list of opportunities to a specified webhook URL.

    Args:
        opportunities (List[Dict[str, Any]]): List of opportunities to send.
        webhook_url (str): The webhook URL.

    Returns:
        bool: True if sending was successful for all opportunities, False otherwise.
    """
    logger.info("=== INICIANDO SEND_OPPORTUNITIES_TO_WEBHOOK ===")
    logger.info(f"Attempting to send {len(opportunities)} opportunities to webhook: {webhook_url}")
    success = True
    if not webhook_url:
        logger.warning("Webhook URL is not provided. Cannot send opportunities.")
        return False

    for opportunity_data in opportunities:
        try:
            response = requests.post(webhook_url, json=opportunity_data)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            logger.info(f"Successfully sent opportunity {opportunity_data.get('opportunity_id', 'N/A')}. Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send opportunity {opportunity_data.get('opportunity_id', 'N/A')} to webhook: {e}")
            success = False # Mark as failed but continue trying to send others

    return success
