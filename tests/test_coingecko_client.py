import unittest
from unittest.mock import patch, MagicMock
import requests # Import requests to mock exceptions

from src.apis.coingecko_client import CoinGeckoClient

# Mock de las dependencias externas
@patch('src.apis.coingecko_client.get_coingecko_config')
@patch('src.apis.coingecko_client.requests')
class TestCoinGeckoClient(unittest.TestCase):

    def setUp(self):
        """Configuración común para los tests."""
        # Reset mocks before each test
        self.mock_get_coingecko_config.reset_mock()
        self.mock_requests.reset_mock()

        # Configure default mock settings
        self.mock_get_coingecko_config.return_value = {
            "base_url": "https://api.coingecko.com/api/v3/",
            "timeout": 15
        }

    @patch('src.apis.coingecko_client.get_logger') # Mock logger to prevent output during tests
    def test_init_without_api_key(self, mock_get_logger, mock_requests, mock_get_coingecko_config):
        """
        Test para la inicialización del cliente sin API key.
        """
        # Ensure config does not return an API key
        mock_get_coingecko_config.return_value = {
            "base_url": "https://api.coingecko.com/api/v3/",
            "timeout": 15
        }

        client = CoinGeckoClient()

        # Verify config was used
        mock_get_coingecko_config.assert_called_once()

        # Verify attributes
        self.assertEqual(client.base_url, "https://api.coingecko.com/api/v3/")
        self.assertEqual(client.api_key, "")
        self.assertEqual(client.timeout, 15)
        self.assertIn("Content-Type", client.headers)
        self.assertEqual(client.headers["Content-Type"], "application/json")
        self.assertNotIn("x-cg-pro-api-key", client.headers)

    @patch('src.apis.coingecko_client.get_logger') # Mock logger to prevent output during tests
    def test_init_with_api_key(self, mock_get_logger, mock_requests, mock_get_coingecko_config):
        """
        Test para la inicialización del cliente con API key.
        """
        # Configure config to return an API key
        mock_get_coingecko_config.return_value = {
            "base_url": "https://api.coingecko.com/api/v3/",
            "api_key": "test_coingecko_key",
            "timeout": 15
        }

        client = CoinGeckoClient()

        # Verify config was used
        mock_get_coingecko_config.assert_called_once()

        # Verify attributes
        self.assertEqual(client.base_url, "https://api.coingecko.com/api/v3/")
        self.assertEqual(client.api_key, "test_coingecko_key")
        self.assertEqual(client.timeout, 15)
        self.assertIn("Content-Type", client.headers)
        self.assertEqual(client.headers["Content-Type"], "application/json")
        self.assertIn("x-cg-pro-api-key", client.headers)
        self.assertEqual(client.headers["x-cg-pro-api-key"], "test_coingecko_key")

    def test_obtener_tokens_top_success(self, mock_requests, mock_get_coingecko_config):
        """
        Test para obtener_tokens_top (exitoso).
        Verifica que obtiene los tokens principales por capitalización.
        """
        client = CoinGeckoClient()
        limit = 50
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "bitcoin", "symbol": "btc"}, {"id": "ethereum", "symbol": "eth"}]
        mock_requests.get.return_value = mock_response

        tokens = client.obtener_tokens_top(limit)

        # Verify requests.get was called with correct parameters
        expected_params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "1h,24h,7d"
        }
        mock_requests.get.assert_called_once_with(
            "https://api.coingecko.com/api/v3/coins/markets",
            headers=client.headers,
            params=expected_params,
            timeout=15
        )
        self.assertEqual(tokens, [{"id": "bitcoin", "symbol": "btc"}, {"id": "ethereum", "symbol": "eth"}])

    def test_obtener_tokens_top_failure(self, mock_requests, mock_get_coingecko_config):
        """
        Test para obtener_tokens_top (fallo).
        Verifica que retorna una lista vacía si la solicitud falla.
        """
        client = CoinGeckoClient()
        limit = 50
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.get.return_value = mock_response

        tokens = client.obtener_tokens_top(limit)

        # Verify requests.get was called
        mock_requests.get.assert_called_once()
        self.assertEqual(tokens, [])

    def test_obtener_tokens_top_exception(self, mock_requests, mock_get_coingecko_config):
        """
        Test para obtener_tokens_top (excepción).
        Verifica que retorna una lista vacía si ocurre una excepción.
        """
        client = CoinGeckoClient()
        limit = 50
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection Error")

        tokens = client.obtener_tokens_top(limit)

        # Verify requests.get was called
        mock_requests.get.assert_called_once()
        self.assertEqual(tokens, [])

    # Aquí se añadirán más tests para las otras funciones

    def test_obtener_datos_token_success(self, mock_requests, mock_get_coingecko_config):
        """
        Test para obtener_datos_token (exitoso).
        Verifica que obtiene datos detallados de un token.
        """
        client = CoinGeckoClient()
        token_id = "bitcoin"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "bitcoin", "symbol": "btc", "market_data": {}}
        mock_requests.get.return_value = mock_response

        token_data = client.obtener_datos_token(token_id)

        # Verify requests.get was called with correct parameters
        expected_params = {
            "localization": "false",
            "tickers": "true",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        mock_requests.get.assert_called_once_with(
            f"https://api.coingecko.com/api/v3/coins/{token_id}",
            headers=client.headers,
            params=expected_params,
            timeout=15
        )
        self.assertEqual(token_data, {"id": "bitcoin", "symbol": "btc", "market_data": {}})

    def test_obtener_datos_token_failure(self, mock_requests, mock_get_coingecko_config):
        """
        Test para obtener_datos_token (fallo).
        Verifica que retorna None si la solicitud falla.
        """
        client = CoinGeckoClient()
        token_id = "nonexistent"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_requests.get.return_value = mock_response

        token_data = client.obtener_datos_token(token_id)

        # Verify requests.get was called
        mock_requests.get.assert_called_once_with(
            f"https://api.coingecko.com/api/v3/coins/{token_id}",
            headers=client.headers,
            params={
                "localization": "false",
                "tickers": "true",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            },
            timeout=15
        )
        self.assertIsNone(token_data)

    def test_obtener_datos_token_exception(self, mock_requests, mock_get_coingecko_config):
        """
        Test para obtener_datos_token (excepción).
        Verifica que retorna None si ocurre una excepción.
        """
        client = CoinGeckoClient()
        token_id = "bitcoin"
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection Error")

        token_data = client.obtener_datos_token(token_id)

        # Verify requests.get was called
        mock_requests.get.assert_called_once()
        self.assertIsNone(token_data)

    def test_buscar_token_success(self, mock_requests, mock_get_coingecko_config):
        """
        Test para buscar_token (exitoso).
        Verifica que busca tokens por nombre o símbolo.
        """
        client = CoinGeckoClient()
        query = "bitcoin"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"coins": [{"id": "bitcoin", "symbol": "btc"}, {"id": "wrapped-bitcoin", "symbol": "wbtc"}]}
        mock_requests.get.return_value = mock_response

        search_results = client.buscar_token(query)

        # Verify requests.get was called with correct parameters
        expected_params = {"query": query}
        mock_requests.get.assert_called_once_with(
            "https://api.coingecko.com/api/v3/search",
            headers=client.headers,
            params=expected_params,
            timeout=15
        )
        self.assertEqual(search_results, [{"id": "bitcoin", "symbol": "btc"}, {"id": "wrapped-bitcoin", "symbol": "wbtc"}])

    def test_buscar_token_failure(self, mock_requests, mock_get_coingecko_config):
        """
        Test para buscar_token (fallo).
        Verifica que retorna una lista vacía si la solicitud falla.
        """
        client = CoinGeckoClient()
        query = "nonexistent"
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.get.return_value = mock_response

        search_results = client.buscar_token(query)

        # Verify requests.get was called
        mock_requests.get.assert_called_once_with(
            "https://api.coingecko.com/api/v3/search",
            headers=client.headers,
            params={"query": query},
            timeout=15
        )
        self.assertEqual(search_results, [])

    def test_buscar_token_missing_coins(self, mock_requests, mock_get_coingecko_config):
        """
        Test para buscar_token (coins faltantes).
        Verifica que retorna una lista vacía si la respuesta no contiene 'coins'.
        """
        client = CoinGeckoClient()
        query = "bitcoin"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"exchanges": []} # Simulate missing 'coins' key
        mock_requests.get.return_value = mock_response

        search_results = client.buscar_token(query)

        # Verify requests.get was called
        mock_requests.get.assert_called_once_with(
            "https://api.coingecko.com/api/v3/search",
            headers=client.headers,
            params={"query": query},
            timeout=15
        )
        self.assertEqual(search_results, [])

    def test_buscar_token_exception(self, mock_requests, mock_get_coingecko_config):
        """
        Test para buscar_token (excepción).
        Verifica que retorna una lista vacía si ocurre una excepción.
        """
        client = CoinGeckoClient()
        query = "bitcoin"
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection Error")

        search_results = client.buscar_token(query)

        # Verify requests.get was called
        mock_requests.get.assert_called_once()
        self.assertEqual(search_results, [])

if __name__ == '__main__':
    unittest.main()
