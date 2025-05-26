import unittest
from unittest.mock import patch, MagicMock
import json
import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests # Import requests to mock exceptions

from src.infrastructure.external_apis.binance_client import BinanceClient
from src.utils.config import settings # Import settings directly for mocking

# Mock de las dependencias externas
# Los mocks se inyectan como argumentos a los métodos de prueba
@patch('src.infrastructure.external_apis.binance_client.requests')
@patch('src.infrastructure.external_apis.binance_client.time') # Mock time for timestamp in signed requests
@patch('src.infrastructure.external_apis.binance_client.get_logger') # Mock logger to prevent output during tests
@patch('src.utils.config.settings') # Mock settings directly for testing BinanceClient init logic
class TestBinanceClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls, mock_settings, mock_get_logger, mock_time, mock_requests):
        """Configuración que se ejecuta una vez para toda la clase de tests."""
        # Configurar los valores mockeados para settings
        mock_settings.binance_api_key = 'mock_api_key_from_settings'
        mock_settings.binance_api_secret = 'mock_api_secret_from_settings'
        mock_settings.binance_testnet = True # Asegurar que testnet sea True para la URL base del cliente de trading

    @classmethod
    def tearDownClass(cls):
        """Limpieza que se ejecuta una vez después de todos los tests de la clase."""
        pass

    def setUp(self):
        """Configuración común para cada test."""
        # Los mocks inyectados por los decoradores de clase se pasan como argumentos a los métodos de prueba.
        # No es necesario resetearlos aquí si se manejan a nivel de método o si su estado no interfiere.
        # Para este caso, los mocks de requests, time y logger se pasan directamente a los métodos.
        pass

    def test_init_data_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para la inicialización del cliente de datos.
        """
        client = BinanceClient(trading=False)

        # Verify attributes
        self.assertEqual(client.base_url, "https://api.binance.com/api/v3/")
        self.assertIsNone(client.api_key)
        self.assertIsNone(client.api_secret)
        self.assertFalse(client.testnet)
        self.assertEqual(client.timeout, 10)
        self.assertFalse(client.trading_enabled)

    def test_init_trade_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para la inicialización del cliente de trading.
        """
        # Pass mock API keys directly to the constructor
        client = BinanceClient(trading=True, api_key='test_api_key', api_secret='test_api_secret')

        # Verify attributes
        self.assertEqual(client.base_url, "https://testnet.binance.vision/api/v3/") # Should be testnet URL
        self.assertEqual(client.api_key, "test_api_key")
        self.assertEqual(client.api_secret, "test_api_secret")
        self.assertTrue(client.testnet)
        self.assertEqual(client.timeout, 10)
        self.assertTrue(client.trading_enabled)

    def test_get_headers_data_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _get_headers en cliente de datos.
        """
        client = BinanceClient(trading=False)
        headers = client._get_headers()

        # Verify headers do not contain API key
        self.assertIn("Content-Type", headers)
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertNotIn("X-MBX-APIKEY", headers)

    def test_get_headers_trade_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _get_headers en cliente de trading.
        """
        # Pass mock API keys directly to the constructor
        client = BinanceClient(trading=True, api_key='test_api_key', api_secret='test_api_secret')
        headers = client._get_headers()

        # Verify headers contain API key
        self.assertIn("Content-Type", headers)
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertIn("X-MBX-APIKEY", headers)
        self.assertEqual(headers["X-MBX-APIKEY"], "test_api_key")

    def test_get_signature(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _get_signature.
        Verifica que genera la firma HMAC SHA256 correcta.
        """
        # Pass mock API keys directly to the constructor
        client = BinanceClient(trading=True, api_key='test_api_key', api_secret='test_api_secret')
        # Explicitly set api_secret to ensure it's not None for the test calculation
        client.api_secret = 'test_api_secret'
        params = {"symbol": "BTCUSDT", "limit": 100}

        # Expected signature calculation
        query_string = urlencode(params)
        expected_signature = hmac.new(
            client.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        signature = client._get_signature(params)

        self.assertEqual(signature, expected_signature)

    def test_make_api_request_get_success(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _make_api_request (GET exitoso).
        """
        client = BinanceClient(trading=False)
        endpoint = "test_endpoint"
        params = {"param1": "value1"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_requests.get.return_value = mock_response

        result = client._make_api_request(endpoint, method="GET", params=params)

        # Verify requests.get was called with correct parameters
        mock_requests.get.assert_called_once_with(
            "https://api.binance.com/api/v3/test_endpoint",
            headers={"Content-Type": "application/json"},
            params={"param1": "value1"},
            timeout=10
        )
        self.assertEqual(result, {"status": "success"})

    def test_make_api_request_post_success(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _make_api_request (POST exitoso).
        """
        # Use trading client for signed request example, pass mock API keys
        client = BinanceClient(trading=True, api_key='test_api_key', api_secret='test_api_secret')
        endpoint = "test_endpoint"
        params = {"param1": "value1"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_requests.post.return_value = mock_response

        # Mock signature generation
        with patch.object(client, '_get_signature', return_value='mock_signature') as mock_get_signature:
             result = client._make_api_request(endpoint, method="POST", params=params, signed=True)

             # Verify requests.post was called with correct parameters
             expected_params = {"param1": "value1", "timestamp": int(mock_time.time.return_value * 1000), "signature": "mock_signature"}
             mock_requests.post.assert_called_once_with(
                 "https://testnet.binance.vision/api/v3/test_endpoint", # Should be testnet URL
                 headers={"Content-Type": "application/json", "X-MBX-APIKEY": "test_api_key"},
                 params=expected_params,
                 timeout=10
             )
             mock_get_signature.assert_called_once_with({"param1": "value1", "timestamp": int(mock_time.time.return_value * 1000)})
             self.assertEqual(result, {"status": "success"})

    def test_make_api_request_error_status(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _make_api_request (respuesta con error).
        """
        client = BinanceClient(trading=False)
        endpoint = "test_endpoint"
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.get.return_value = mock_response

        result = client._make_api_request(endpoint)

        # Verify requests.get was called
        mock_requests.get.assert_called_once()
        self.assertIsNone(result)

    def test_make_api_request_exception(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _make_api_request (excepción durante la solicitud).
        """
        client = BinanceClient(trading=False)
        endpoint = "test_endpoint"
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection Error")

        result = client._make_api_request(endpoint)

        # Verify requests.get was called
        mock_requests.get.assert_called_once()
        self.assertIsNone(result)

    def test_make_api_request_signed_without_keys(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para _make_api_request (solicitud firmada sin API keys).
        """
        # Ensure client is initialized without keys for this test
        client = BinanceClient(trading=True, api_key=None, api_secret=None)
        endpoint = "test_endpoint"

        result = client._make_api_request(endpoint, signed=True)

        # Verify requests.get was NOT called
        mock_requests.get.assert_not_called()
        self.assertIsNone(result)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_info_exchange(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_info_exchange.
        Verifica que llama a _make_api_request con el endpoint correcto.
        """
        client = BinanceClient(trading=False)
        mock_make_api_request.return_value = {"symbols": []}

        info = client.obtener_info_exchange()

        # Verify _make_api_request was called with the correct endpoint and params
        mock_make_api_request.assert_called_once_with("exchangeInfo", method="GET", params=None, signed=False)
        self.assertEqual(info, {"symbols": []})

    @patch.object(BinanceClient, 'obtener_info_exchange')
    def test_obtener_simbolos_trading(self, mock_obtener_info_exchange, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_simbolos_trading.
        Verifica que obtiene y filtra los símbolos de trading.
        """
        client = BinanceClient(trading=False)
        mock_exchange_info = {
            "symbols": [
                {"symbol": "BTCUSDT", "status": "TRADING"},
                {"symbol": "ETHBTC", "status": "TRADING"},
                {"symbol": "LTCUSDT", "status": "BREAK"}, # Should be ignored
                {"symbol": "XRPETH", "status": "TRADING"},
                {"symbol": "NONTRADING", "status": "SETTLING"} # Should be ignored
            ]
        }
        mock_obtener_info_exchange.return_value = mock_exchange_info

        simbolos = client.obtener_simbolos_trading()

        # Verify obtener_info_exchange was called
        mock_obtener_info_exchange.assert_called_once()

        # Verify that only TRADING symbols are returned
        self.assertEqual(len(simbolos), 3)
        self.assertIn("BTCUSDT", simbolos)
        self.assertIn("ETHBTC", simbolos)
        self.assertIn("XRPETH", simbolos)
        self.assertNotIn("LTCUSDT", simbolos)
        self.assertNotIn("NONTRADING", simbolos)

    @patch.object(BinanceClient, 'obtener_info_exchange')
    def test_obtener_simbolos_trading_no_info(self, mock_obtener_info_exchange, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_simbolos_trading cuando obtener_info_exchange retorna None.
        Verifica que retorna una lista vacía.
        """
        client = BinanceClient(trading=False)
        mock_obtener_info_exchange.return_value = None # Simulate failure

        simbolos = client.obtener_simbolos_trading()

        # Verify obtener_info_exchange was called
        mock_obtener_info_exchange.assert_called_once()

        # Verify that an empty list is returned
        self.assertEqual(simbolos, [])

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_precio_ticker_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_precio_ticker (exitoso).
        Verifica que obtiene el precio de un símbolo.
        """
        client = BinanceClient(trading=False)
        mock_make_api_request.return_value = {"symbol": "BTCUSDT", "price": "60000.5"}

        price = client.obtener_precio_ticker("BTCUSDT")

        # Verify _make_api_request was called with the correct endpoint and params
        mock_make_api_request.assert_called_once_with("ticker/price", method="GET", params={"symbol": "BTCUSDT"}, signed=False)
        self.assertEqual(price, 60000.5)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_precio_ticker_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_precio_ticker (fallo).
        Verifica que retorna None si la solicitud falla.
        """
        client = BinanceClient(trading=False)
        mock_make_api_request.return_value = None # Simulate API request failure

        price = client.obtener_precio_ticker("BTCUSDT")

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("ticker/price", method="GET", params={"symbol": "BTCUSDT"}, signed=False)
        self.assertIsNone(price)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_precio_ticker_missing_price(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_precio_ticker (precio faltante).
        Verifica que retorna None si la respuesta no contiene el precio.
        """
        client = BinanceClient(trading=False)
        mock_make_api_request.return_value = {"symbol": "BTCUSDT"} # Simulate missing price field

        price = client.obtener_precio_ticker("BTCUSDT")

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("ticker/price", method="GET", params={"symbol": "BTCUSDT"}, signed=False)
        self.assertIsNone(price)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_precios_todos_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_precios_todos (exitoso).
        Verifica que obtiene los precios de todos los símbolos.
        """
        client = BinanceClient(trading=False)
        mock_make_api_request.return_value = [
            {"symbol": "BTCUSDT", "price": "60000.5"},
            {"symbol": "ETHBTC", "price": "0.05"},
            {"symbol": "XRPETH", "price": "0.0001"}
        ]

        prices = client.obtener_precios_todos()

        # Verify _make_api_request was called with the correct endpoint
        mock_make_api_request.assert_called_once_with("ticker/price", method="GET", params=None, signed=False)

        # Verify the returned dictionary
        self.assertEqual(len(prices), 3)
        self.assertEqual(prices["BTCUSDT"], 60000.5)
        self.assertEqual(prices["ETHBTC"], 0.05)
        self.assertEqual(prices["XRPETH"], 0.0001)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_precios_todos_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_precios_todos (fallo).
        Verifica que retorna un diccionario vacío si la solicitud falla.
        """
        client = BinanceClient(trading=False)
        mock_make_api_request.return_value = None # Simulate API request failure

        prices = client.obtener_precios_todos()

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("ticker/price", method="GET", params=None, signed=False)
        self.assertEqual(prices, {})

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_precios_todos_invalid_response(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_precios_todos (respuesta inválida).
        Verifica que retorna un diccionario vacío si la respuesta no es una lista.
        """
        client = BinanceClient(trading=False)
        mock_make_api_request.return_value = {"status": "success"} # Simulate non-list response

        prices = client.obtener_precios_todos()

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("ticker/price", method="GET", params=None, signed=False)
        self.assertEqual(prices, {})

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_profundidad_mercado(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_profundidad_mercado.
        Verifica que llama a _make_api_request con los parámetros correctos.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        limit = 10
        mock_make_api_request.return_value = {"bids": [], "asks": []}

        depth = client.obtener_profundidad_mercado(simbolo, limit)

        # Verify _make_api_request was called with the correct endpoint and params
        mock_make_api_request.assert_called_once_with(
            "depth",
            method="GET",
            params={"symbol": simbolo, "limit": limit},
            signed=False
        )
        self.assertEqual(depth, {"bids": [], "asks": []})

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_klines_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_klines (exitoso).
        Verifica que obtiene datos históricos de velas.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        intervalo = "1h"
        limit = 50
        mock_make_api_request.return_value = [[1,2,3,4,5,6,7,8,9,10,11,12]] # Simulate klines data

        klines = client.obtener_klines(simbolo, intervalo, limit)

        # Verify _make_api_request was called with the correct endpoint and params
        mock_make_api_request.assert_called_once_with(
            "klines",
            method="GET",
            params={"symbol": simbolo, "interval": intervalo, "limit": limit},
            signed=False
        )
        self.assertEqual(klines, [[1,2,3,4,5,6,7,8,9,10,11,12]])

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_klines_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_klines (fallo).
        Verifica que retorna una lista vacía si la solicitud falla.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        intervalo = "1h"
        limit = 50
        mock_make_api_request.return_value = None # Simulate API request failure

        klines = client.obtener_klines(simbolo, intervalo, limit)

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with(
            "klines",
            method="GET",
            params={"symbol": simbolo, "interval": intervalo, "limit": limit},
            signed=False
        )
        self.assertEqual(klines, [])

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_volumen_24h_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_volumen_24h (exitoso).
        Verifica que obtiene el volumen de 24h de un símbolo.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        mock_make_api_request.return_value = {"symbol": "BTCUSDT", "volume": "123456.789"}

        volume = client.obtener_volumen_24h(simbolo)

        # Verify _make_api_request was called with the correct endpoint and params
        mock_make_api_request.assert_called_once_with("ticker/24hr", method="GET", params={"symbol": simbolo}, signed=False)
        self.assertEqual(volume, 123456.789)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_volumen_24h_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_volumen_24h (fallo).
        Verifica que retorna None si la solicitud falla.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        mock_make_api_request.return_value = None # Simulate API request failure

        volume = client.obtener_volumen_24h(simbolo)

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("ticker/24hr", method="GET", params={"symbol": simbolo}, signed=False)
        self.assertIsNone(volume)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_volumen_24h_missing_volume(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_volumen_24h (volumen faltante).
        Verifica que retorna None si la respuesta no contiene el volumen.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        mock_make_api_request.return_value = {"symbol": "BTCUSDT"} # Simulate missing volume field

        volume = client.obtener_volumen_24h(simbolo)

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("ticker/24hr", method="GET", params={"symbol": simbolo}, signed=False)
        self.assertIsNone(volume)

    @patch.object(BinanceClient, '_make_api_request')
    def test_verificar_credenciales_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para verificar_credenciales (exitoso).
        Verifica que las credenciales son válidas.
        """
        client = BinanceClient(trading=True) # Trading client
        mock_make_api_request.return_value = {"balances": []} # Simulate successful response with balances

        is_valid = client.verificar_credenciales()

        # Verify _make_api_request was called with the correct endpoint and signed=True
        mock_make_api_request.assert_called_once_with("account", method="GET", params=None, signed=True)
        self.assertTrue(is_valid)

    @patch.object(BinanceClient, '_make_api_request')
    def test_verificar_credenciales_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para verificar_credenciales (fallo).
        Verifica que retorna False si la solicitud falla.
        """
        client = BinanceClient(trading=True) # Trading client
        mock_make_api_request.return_value = None # Simulate API request failure

        is_valid = client.verificar_credenciales()

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("account", method="GET", params=None, signed=True)
        self.assertFalse(is_valid)

    @patch.object(BinanceClient, '_make_api_request')
    def test_verificar_credenciales_missing_balances(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para verificar_credenciales (balances faltantes).
        Verifica que retorna False si la respuesta no contiene 'balances'.
        """
        client = BinanceClient(trading=True) # Trading client
        mock_make_api_request.return_value = {"status": "success"} # Simulate response without balances

        is_valid = client.verificar_credenciales()

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("account", method="GET", params=None, signed=True)
        self.assertFalse(is_valid)

    def test_verificar_credenciales_data_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para verificar_credenciales en cliente de datos.
        Verifica que retorna False si no es un cliente de trading.
        """
        client = BinanceClient(trading=False) # Data client

        is_valid = client.verificar_credenciales()

        # Verify _make_api_request was NOT called
        mock_requests.get.assert_not_called()
        self.assertFalse(is_valid)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_saldo_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_saldo (exitoso).
        Verifica que obtiene el saldo disponible de un activo.
        """
        client = BinanceClient(trading=True) # Trading client
        mock_make_api_request.return_value = {
            "balances": [
                {"asset": "BTC", "free": "0.5", "locked": "0.1"},
                {"asset": "USDT", "free": "1000.0", "locked": "50.0"}
            ]
        } # Simulate successful response with balances

        balance = client.obtener_saldo("USDT")

        # Verify _make_api_request was called with the correct endpoint and signed=True
        mock_make_api_request.assert_called_once_with("account", method="GET", params=None, signed=True)
        self.assertEqual(balance, 1000.0)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_saldo_asset_not_found(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_saldo (activo no encontrado).
        Verifica que retorna 0.0 si el activo no está en la lista de balances.
        """
        client = BinanceClient(trading=True) # Trading client
        mock_make_api_request.return_value = {
            "balances": [
                {"asset": "BTC", "free": "0.5", "locked": "0.1"},
                {"asset": "USDT", "free": "1000.0", "locked": "50.0"}
            ]
        } # Simulate successful response with balances

        balance = client.obtener_saldo("ETH") # Asset not in balances

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("account", method="GET", params=None, signed=True)
        self.assertEqual(balance, 0.0)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_saldo_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_saldo (fallo).
        Verifica que retorna 0.0 si la solicitud falla.
        """
        client = BinanceClient(trading=True) # Trading client
        mock_make_api_request.return_value = None # Simulate API request failure

        balance = client.obtener_saldo("USDT")

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with("account", method="GET", params=None, signed=True)
        self.assertEqual(balance, 0.0)

    def test_obtener_saldo_data_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_saldo en cliente de datos.
        Verifica que retorna 0.0 si no es un cliente de trading.
        """
        client = BinanceClient(trading=False) # Data client

        balance = client.obtener_saldo("USDT")

        # Verify _make_api_request was NOT called
        mock_requests.get.assert_not_called()
        self.assertEqual(balance, 0.0)

    @patch.object(BinanceClient, '_make_api_request')
    def test_crear_orden_mercado_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para crear_orden_mercado (exitoso).
        Verifica que crea una orden de mercado correctamente.
        """
        client = BinanceClient(trading=True) # Trading client
        simbolo = "BTCUSDT"
        lado = "BUY"
        cantidad = 0.001
        mock_make_api_request.return_value = {"orderId": 12345} # Simulate successful order creation

        order = client.crear_orden_mercado(simbolo, lado, cantidad)

        # Verify _make_api_request was called with the correct parameters
        mock_make_api_request.assert_called_once_with(
            "order",
            method="POST",
            params={"symbol": simbolo, "side": lado, "type": "MARKET", "quantity": cantidad},
            signed=True
        )
        self.assertEqual(order, {"orderId": 12345})

    @patch.object(BinanceClient, '_make_api_request')
    def test_crear_orden_mercado_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para crear_orden_mercado (fallo).
        Verifica que retorna None si la solicitud falla.
        """
        client = BinanceClient(trading=True) # Trading client
        simbolo = "BTCUSDT"
        lado = "BUY"
        cantidad = 0.001
        mock_make_api_request.return_value = None # Simulate API request failure

        order = client.crear_orden_mercado(simbolo, lado, cantidad)

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with(
            "order",
            method="POST",
            params={"symbol": simbolo, "side": lado, "type": "MARKET", "quantity": cantidad},
            signed=True
        )
        self.assertIsNone(order)

    def test_crear_orden_mercado_data_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para crear_orden_mercado en cliente de datos.
        Verifica que retorna None si no es un cliente de trading.
        """
        client = BinanceClient(trading=False) # Data client
        simbolo = "BTCUSDT"
        lado = "BUY"
        cantidad = 0.001

        order = client.crear_orden_mercado(simbolo, lado, cantidad)

        # Verify _make_api_request was NOT called
        mock_requests.post.assert_not_called()
        self.assertIsNone(order)

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_estado_orden_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_estado_orden (exitoso).
        Verifica que obtiene el estado de una orden.
        """
        client = BinanceClient(trading=True) # Trading client
        simbolo = "BTCUSDT"
        orden_id = 12345
        mock_make_api_request.return_value = {"status": "FILLED"} # Simulate successful response

        status = client.obtener_estado_orden(simbolo, orden_id)

        # Verify _make_api_request was called with the correct parameters
        mock_make_api_request.assert_called_once_with(
            "order",
            method="GET",
            params={"symbol": simbolo, "orderId": orden_id},
            signed=True
        )
        self.assertEqual(status, {"status": "FILLED"})

    @patch.object(BinanceClient, '_make_api_request')
    def test_obtener_estado_orden_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_estado_orden (fallo).
        Verifica que retorna None si la solicitud falla.
        """
        client = BinanceClient(trading=True) # Trading client
        simbolo = "BTCUSDT"
        orden_id = 12345
        mock_make_api_request.return_value = None # Simulate API request failure

        status = client.obtener_estado_orden(simbolo, orden_id)

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with(
            "order",
            method="GET",
            params={"symbol": simbolo, "orderId": orden_id},
            signed=True
        )
        self.assertIsNone(status)

    def test_obtener_estado_orden_data_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_estado_orden en cliente de datos.
        Verifica que retorna None si no es un cliente de trading.
        """
        client = BinanceClient(trading=False) # Data client
        simbolo = "BTCUSDT"
        orden_id = 12345

        status = client.obtener_estado_orden(simbolo, orden_id)

        # Verify _make_api_request was NOT called
        mock_requests.get.assert_not_called()
        self.assertIsNone(status)

    @patch.object(BinanceClient, '_make_api_request')
    def test_cancelar_orden_success(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para cancelar_orden (exitoso).
        Verifica que cancela una orden abierta.
        """
        client = BinanceClient(trading=True) # Trading client
        simbolo = "BTCUSDT"
        orden_id = 12345
        mock_make_api_request.return_value = {"orderId": 12345, "status": "CANCELED"} # Simulate successful cancellation

        cancellation_result = client.cancelar_orden(simbolo, orden_id)

        # Verify _make_api_request was called with the correct parameters
        mock_make_api_request.assert_called_once_with(
            "order",
            method="DELETE",
            params={"symbol": simbolo, "orderId": orden_id},
            signed=True
        )
        self.assertEqual(cancellation_result, {"orderId": 12345, "status": "CANCELED"})

    @patch.object(BinanceClient, '_make_api_request')
    def test_cancelar_orden_failure(self, mock_make_api_request, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para cancelar_orden (fallo).
        Verifica que retorna None si la solicitud falla.
        """
        client = BinanceClient(trading=True) # Trading client
        simbolo = "BTCUSDT"
        orden_id = 12345
        mock_make_api_request.return_value = None # Simulate API request failure

        cancellation_result = client.cancelar_orden(simbolo, orden_id)

        # Verify _make_api_request was called
        mock_make_api_request.assert_called_once_with(
            "order",
            method="DELETE",
            params={"symbol": simbolo, "orderId": orden_id},
            signed=True
        )
        self.assertIsNone(cancellation_result)

    def test_cancelar_orden_data_client(self, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para cancelar_orden en cliente de datos.
        Verifica que retorna None si no es un cliente de trading.
        """
        client = BinanceClient(trading=False) # Data client
        simbolo = "BTCUSDT"
        orden_id = 12345

        cancellation_result = client.cancelar_orden(simbolo, orden_id)

        # Verify requests.delete was NOT called
        mock_requests.delete.assert_not_called()
        self.assertIsNone(cancellation_result)

    @patch.object(BinanceClient, 'obtener_info_exchange')
    def test_obtener_reglas_simbolo_success(self, mock_obtener_info_exchange, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_reglas_simbolo (exitoso).
        Verifica que obtiene las reglas de trading para un símbolo.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        mock_exchange_info = {
            "symbols": [
                {"symbol": "ETHBTC", "filters": []},
                {"symbol": "BTCUSDT", "filters": [{"filterType": "LOT_SIZE", "stepSize": "0.000001"}]},
                {"symbol": "XRPETH", "filters": []}
            ]
        }
        mock_obtener_info_exchange.return_value = mock_exchange_info

        rules = client.obtener_reglas_simbolo(simbolo)

        # Verify obtener_info_exchange was called
        mock_obtener_info_exchange.assert_called_once()
        self.assertEqual(rules, {"symbol": "BTCUSDT", "filters": [{"filterType": "LOT_SIZE", "stepSize": "0.000001"}]})

    @patch.object(BinanceClient, 'obtener_info_exchange')
    def test_obtener_reglas_simbolo_not_found(self, mock_obtener_info_exchange, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_reglas_simbolo (símbolo no encontrado).
        Verifica que retorna None si el símbolo no está en la información del exchange.
        """
        client = BinanceClient(trading=False)
        simbolo = "NONEXISTUSDT"
        mock_exchange_info = {
            "symbols": [
                {"symbol": "ETHBTC", "filters": []},
                {"symbol": "BTCUSDT", "filters": []}
            ]
        }
        mock_obtener_info_exchange.return_value = mock_exchange_info

        rules = client.obtener_reglas_simbolo(simbolo)

        # Verify obtener_info_exchange was called
        mock_obtener_info_exchange.assert_called_once()
        self.assertIsNone(rules)

    @patch.object(BinanceClient, 'obtener_info_exchange')
    def test_obtener_reglas_simbolo_failure(self, mock_obtener_info_exchange, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para obtener_reglas_simbolo (fallo).
        Verifica que retorna None si obtener_info_exchange falla.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        mock_obtener_info_exchange.return_value = None # Simulate failure

        rules = client.obtener_reglas_simbolo(simbolo)

        # Verify obtener_info_exchange was called
        mock_obtener_info_exchange.assert_called_once()
        self.assertIsNone(rules)

    @patch.object(BinanceClient, 'obtener_reglas_simbolo')
    def test_redondear_cantidad_success(self, mock_obtener_reglas_simbolo, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para redondear_cantidad (exitoso).
        Verifica que redondea la cantidad según las reglas del símbolo.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        cantidad = 0.001567

        # Mock rules with LOT_SIZE filter
        mock_rules = {
            "symbol": "BTCUSDT",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                {"filterType": "LOT_SIZE", "stepSize": "0.000001", "minQty": "0.000001"}
            ]
        }
        mock_obtener_reglas_simbolo.return_value = mock_rules

        rounded_quantity = client.redondear_cantidad(simbolo, cantidad)

        # Verify obtener_reglas_simbolo was called
        mock_obtener_reglas_simbolo.assert_called_once_with(simbolo)
        self.assertAlmostEqual(rounded_quantity, 0.001567 - (0.001567 % 0.000001)) # Should round down to nearest step size

    @patch.object(BinanceClient, 'obtener_reglas_simbolo')
    def test_redondear_cantidad_below_min_qty(self, mock_obtener_reglas_simbolo, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para redondear_cantidad cuando la cantidad es menor al minQty.
        Verifica que retorna 0.0.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        cantidad = 0.00000001 # Below minQty

        # Mock rules with LOT_SIZE filter
        mock_rules = {
            "symbol": "BTCUSDT",
            "filters": [
                {"filterType": "LOT_SIZE", "stepSize": "0.000001", "minQty": "0.000001"}
            ]
        }
        mock_obtener_reglas_simbolo.return_value = mock_rules

        rounded_quantity = client.redondear_cantidad(simbolo, cantidad)

        # Verify obtener_reglas_simbolo was called
        mock_obtener_reglas_simbolo.assert_called_once_with(simbolo)
        self.assertEqual(rounded_quantity, 0.0)

    @patch.object(BinanceClient, 'obtener_reglas_simbolo')
    def test_redondear_cantidad_no_rules(self, mock_obtener_reglas_simbolo, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para redondear_cantidad cuando no se obtienen reglas.
        Verifica que retorna la cantidad original.
        """
        client = BinanceClient(trading=False)
        simbolo = "NONEXISTUSDT"
        cantidad = 123.456

        mock_obtener_reglas_simbolo.return_value = None # Simulate no rules found

        rounded_quantity = client.redondear_cantidad(simbolo, cantidad)

        # Verify obtener_reglas_simbolo was called
        mock_obtener_reglas_simbolo.assert_called_once_with(simbolo)
        self.assertEqual(rounded_quantity, cantidad) # Should return original quantity

    @patch.object(BinanceClient, 'obtener_reglas_simbolo')
    def test_redondear_cantidad_no_lot_size_filter(self, mock_obtener_reglas_simbolo, mock_settings, mock_get_logger, mock_time, mock_requests):
        """
        Test para redondear_cantidad cuando no hay filtro LOT_SIZE.
        Verifica que retorna la cantidad original.
        """
        client = BinanceClient(trading=False)
        simbolo = "BTCUSDT"
        cantidad = 123.456

        # Mock rules without LOT_SIZE filter
        mock_rules = {
            "symbol": "BTCUSDT",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01"}
            ]
        }
        mock_obtener_reglas_simbolo.return_value = mock_rules

        rounded_quantity = client.redondear_cantidad(simbolo, cantidad)

        # Verify obtener_reglas_simbolo was called
        mock_obtener_reglas_simbolo.assert_called_once_with(simbolo)
        self.assertEqual(rounded_quantity, cantidad) # Should return original quantity

if __name__ == '__main__':
    unittest.main()
