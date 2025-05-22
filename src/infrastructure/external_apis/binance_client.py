"""
Cliente para la API de Binance.
Proporciona funciones para interactuar con Binance para datos y operaciones.
"""

import time
import hmac
import hashlib
import requests
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode
from ..utils.config import get_config_value, settings 
from ..utils.logger import get_logger

# Obtener logger específico
logger = get_logger("binance_client")

class BinanceClient:
    """
    Cliente para interactuar con la API de Binance.
    Proporciona métodos para obtener datos y ejecutar operaciones en Binance.
    """
    
    def __init__(self, trading: bool = False):
        """
        Inicializa el cliente con la configuración global.
        
        Args:
            trading: Si es True, inicializa con configuración para trading.
                    Si es False, inicializa solo para datos.
        """
        if trading:
            self.api_key = settings.binance_api_key
            self.api_secret = settings.binance_api_secret
            self.testnet = settings.binance_testnet
            self.base_url = "https://testnet.binance.vision/api/v3/" if self.testnet else "https://api.binance.com/api/v3/"
        else:
            self.api_key = None
            self.api_secret = None
            self.testnet = False # Data client doesn't need testnet config usually
            self.base_url = "https://api.binance.com/api/v3/" # Use production URL for data by default
            
        self.timeout = 10
        self.trading_enabled = trading
        
        if trading:
            logger.info(f"Cliente Binance inicializado para trading (testnet: {self.testnet})")
        else:
            logger.info("Cliente Binance inicializado para datos")
    
    def ping(self) -> bool:
        """
        Verifica que la API de Binance esté respondiendo.
        
        Returns:
            True si la API responde, False en caso contrario.
        """
        endpoint = "ping"
        result = self._make_api_request(endpoint)
        return result is not None
    
    def check_connection(self) -> bool:
        """
        Verifica la conexión con Binance.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario.
        """
        return self.ping()
    
    def get_markets(self) -> List[str]:
        """
        Obtiene la lista de todos los símbolos de trading disponibles.
        Alias para obtener_simbolos_trading.
        
        Returns:
            Lista de símbolos de trading.
        """
        return self.obtener_simbolos_trading()
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de la cuenta.
        
        Returns:
            Información de la cuenta o None si hay error.
        """
        if not self.trading_enabled:
            logger.error("Cliente no inicializado para trading")
            return None
            
        endpoint = "account"
        result = self._make_api_request(endpoint, signed=True)
        return result
    
    def get_balances(self) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene los saldos de todos los activos.
        
        Returns:
            Lista de saldos o None si hay error.
        """
        account_info = self.get_account_info()
        if account_info and "balances" in account_info:
            return account_info["balances"]
        return None
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del ticker para un símbolo.
        
        Args:
            symbol: Símbolo de trading (ej: BTCUSDT)
            
        Returns:
            Información del ticker o None si hay error.
        """
        endpoint = "ticker/24hr"
        params = {"symbol": symbol}
        return self._make_api_request(endpoint, params=params)
    
    def get_tickers(self) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene información del ticker para todos los símbolos.
        
        Returns:
            Lista con información de tickers o None si hay error.
        """
        endpoint = "ticker/24hr"
        return self._make_api_request(endpoint)
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Obtiene los headers para las solicitudes a Binance.
        
        Returns:
            Diccionario con los headers.
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
            
        return headers
    
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """
        Genera una firma HMAC SHA256 para la solicitud.
        
        Args:
            params: Parámetros de la solicitud.
            
        Returns:
            Firma codificada en hexadecimal.
        """
        if not self.api_secret:
            return ""
            
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_api_request(self, endpoint: str, method: str = "GET", 
                          params: Optional[Dict[str, Any]] = None, 
                          signed: bool = False) -> Any:
        """
        Realiza una solicitud a la API de Binance.
        
        Args:
            endpoint: Endpoint de la API.
            method: Método HTTP (GET, POST, DELETE).
            params: Parámetros para la solicitud.
            signed: Si la solicitud requiere firma.
            
        Returns:
            Respuesta de la API o None si hay error.
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        if params is None:
            params = {}
            
        if signed:
            if not self.api_key or not self.api_secret:
                logger.error("Se requiere API key y secret para una solicitud firmada")
                return None
                
            # Añadir timestamp
            params["timestamp"] = int(time.time() * 1000)
            
            # Generar firma
            signature = self._get_signature(params)
            params["signature"] = signature
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, timeout=self.timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=self.timeout)
            else:
                logger.error(f"Método HTTP no soportado: {method}")
                return None
                
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error en solicitud a Binance {endpoint}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error en solicitud a Binance {endpoint}: {str(e)}", exc_info=e)
            return None
    
    # Métodos para datos públicos
    
    def obtener_info_exchange(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del exchange.
        
        Returns:
            Información del exchange o None si hay error.
        """
        endpoint = "exchangeInfo"
        return self._make_api_request(endpoint)
    
    def obtener_simbolos_trading(self) -> List[str]:
        """
        Obtiene la lista de todos los símbolos de trading disponibles.
        
        Returns:
            Lista de símbolos de trading.
        """
        try:
            info = self.obtener_info_exchange()
            if not info:
                return []
                
            simbolos = [symbol["symbol"] for symbol in info.get("symbols", []) 
                      if symbol.get("status") == "TRADING"]
            
            logger.info(f"Obtenidos {len(simbolos)} símbolos de trading en Binance")
            return simbolos
        except Exception as e:
            logger.error(f"Error al obtener símbolos de trading: {str(e)}", exc_info=e)
            return []
    
    def obtener_precio_ticker(self, simbolo: str) -> Optional[float]:
        """
        Obtiene el precio actual de un símbolo.
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            
        Returns:
            Precio actual o None si hay error.
        """
        endpoint = "ticker/price"
        params = {"symbol": simbolo}
        
        result = self._make_api_request(endpoint, params=params)
        if result and "price" in result:
            return float(result["price"])
            
        return None
    
    def obtener_precios_todos(self) -> Dict[str, float]:
        """
        Obtiene los precios de todos los símbolos.
        
        Returns:
            Diccionario con símbolos y precios.
        """
        endpoint = "ticker/price"
        
        result = self._make_api_request(endpoint)
        if not result:
            return {}
            
        return {item["symbol"]: float(item["price"]) for item in result}
    
    def obtener_profundidad_mercado(self, simbolo: str, limit: int = 5) -> Optional[Dict[str, Any]]:
        """
        Obtiene la profundidad del mercado (order book).
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            limit: Número de niveles a obtener (default: 5).
            
        Returns:
            Order book o None si hay error.
        """
        endpoint = "depth"
        params = {
            "symbol": simbolo,
            "limit": limit
        }
        
        return self._make_api_request(endpoint, params=params)
    
    def obtener_klines(self, simbolo: str, intervalo: str = "1h", 
                       limit: int = 100) -> List[List[Any]]:
        """
        Obtiene datos históricos de velas (klines).
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            intervalo: Intervalo de tiempo (ej: 1m, 5m, 1h, 1d).
            limit: Número de velas a obtener (default: 100).
            
        Returns:
            Lista de velas.
        """
        endpoint = "klines"
        params = {
            "symbol": simbolo,
            "interval": intervalo,
            "limit": limit
        }
        
        result = self._make_api_request(endpoint, params=params)
        return result if result else []
    
    def obtener_volumen_24h(self, simbolo: str) -> Optional[float]:
        """
        Obtiene el volumen de 24h para un símbolo.
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            
        Returns:
            Volumen de 24h o None si hay error.
        """
        endpoint = "ticker/24hr"
        params = {"symbol": simbolo}
        
        result = self._make_api_request(endpoint, params=params)
        if result and "volume" in result:
            return float(result["volume"])
            
        return None
    
    # Métodos para trading (requieren API key y secret)
    
    def verificar_credenciales(self) -> bool:
        """
        Verifica que las credenciales de API sean válidas.
        
        Returns:
            True si las credenciales son válidas, False en caso contrario.
        """
        if not self.trading_enabled:
            logger.error("Cliente no inicializado para trading")
            return False
            
        endpoint = "account"
        result = self._make_api_request(endpoint, signed=True)
        
        if result and "balances" in result:
            logger.info("Credenciales de API verificadas correctamente")
            return True
        else:
            logger.error("Credenciales de API inválidas o acceso denegado")
            return False
    
    def obtener_saldo(self, asset: str) -> float:
        """
        Obtiene el saldo disponible de un activo.
        
        Args:
            asset: Símbolo del activo (ej: BTC, USDT).
            
        Returns:
            Saldo disponible del activo o 0 si hay error.
        """
        if not self.trading_enabled:
            logger.error("Cliente no inicializado para trading")
            return 0.0
            
        endpoint = "account"
        result = self._make_api_request(endpoint, signed=True)
        
        if result and "balances" in result:
            for balance in result["balances"]:
                if balance["asset"] == asset:
                    return float(balance["free"])
        
        return 0.0
    
    def crear_orden_mercado(self, simbolo: str, lado: str, cantidad: float) -> Optional[Dict[str, Any]]:
        """
        Crea una orden de mercado.
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            lado: Lado de la orden (BUY o SELL).
            cantidad: Cantidad a comprar/vender.
            
        Returns:
            Datos de la orden o None si hay error.
        """
        if not self.trading_enabled:
            logger.error("Cliente no inicializado para trading")
            return None
            
        endpoint = "order"
        params = {
            "symbol": simbolo,
            "side": lado,
            "type": "MARKET",
            "quantity": cantidad
        }
        
        result = self._make_api_request(endpoint, method="POST", params=params, signed=True)
        
        if result:
            logger.info(f"Orden de mercado creada: {simbolo} {lado} {cantidad}")
        else:
            logger.error(f"Error al crear orden de mercado: {simbolo} {lado} {cantidad}")
            
        return result
    
    def obtener_estado_orden(self, simbolo: str, orden_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de una orden.
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            orden_id: ID de la orden.
            
        Returns:
            Estado de la orden o None si hay error.
        """
        if not self.trading_enabled:
            logger.error("Cliente no inicializado para trading")
            return None
            
        endpoint = "order"
        params = {
            "symbol": simbolo,
            "orderId": orden_id
        }
        
        return self._make_api_request(endpoint, params=params, signed=True)
    
    def cancelar_orden(self, simbolo: str, orden_id: int) -> Optional[Dict[str, Any]]:
        """
        Cancela una orden abierta.
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            orden_id: ID de la orden.
            
        Returns:
            Confirmación de cancelación o None si hay error.
        """
        if not self.trading_enabled:
            logger.error("Cliente no inicializado para trading")
            return None
            
        endpoint = "order"
        params = {
            "symbol": simbolo,
            "orderId": orden_id
        }
        
        result = self._make_api_request(endpoint, method="DELETE", params=params, signed=True)
        
        if result:
            logger.info(f"Orden cancelada: {simbolo} {orden_id}")
        else:
            logger.error(f"Error al cancelar orden: {simbolo} {orden_id}")
            
        return result
    
    def obtener_reglas_simbolo(self, simbolo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene las reglas de trading para un símbolo.
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            
        Returns:
            Reglas de trading o None si hay error.
        """
        try:
            info = self.obtener_info_exchange()
            if not info:
                return None
                
            for symbol_info in info.get("symbols", []):
                if symbol_info["symbol"] == simbolo:
                    return symbol_info
                    
            return None
        except Exception as e:
            logger.error(f"Error al obtener reglas del símbolo {simbolo}: {str(e)}", exc_info=e)
            return None
    
    def redondear_cantidad(self, simbolo: str, cantidad: float) -> float:
        """
        Redondea la cantidad según las reglas del símbolo.
        
        Args:
            simbolo: Símbolo de trading (ej: BTCUSDT).
            cantidad: Cantidad a redondear.
            
        Returns:
            Cantidad redondeada.
        """
        try:
            rules = self.obtener_reglas_simbolo(simbolo)
            if not rules:
                return cantidad
                
            for filter in rules.get("filters", []):
                if filter["filterType"] == "LOT_SIZE":
                    step_size = float(filter["stepSize"])
                    min_qty = float(filter["minQty"])
                    
                    if cantidad < min_qty:
                        return 0.0
                        
                    precision = len(filter["stepSize"].rstrip("0").split(".")[1]) if "." in filter["stepSize"] else 0
                    rounded = round(cantidad - (cantidad % step_size), precision)
                    
                    return rounded
                    
            return cantidad
        except Exception as e:
            logger.error(f"Error al redondear cantidad para {simbolo}: {str(e)}", exc_info=e)
            return cantidad

# Instancias globales
binance_data_client = BinanceClient(trading=False)
binance_trade_client = BinanceClient(trading=True)
